import time
from datetime import datetime, timedelta
from os import urandom
from base64 import b64encode

from lampost.context.resource import m_requires, requires
from lampost.context.config import m_configured
from lampost.util.lputil import ClientError

m_requires(__name__, 'log', 'dispatcher', 'user_manager')

m_configured(__name__, 'refresh_link_interval', 'broadcast_interval', 'link_dead_prune', 'link_dead_interval',
             'link_idle_refresh')


class SessionManager():
    def __init__(self):
        self.session_map = {}
        self.player_info_map = {}
        self.player_session_map = {}

    def _post_init(self):
        register_p(self._refresh_link_status, seconds=refresh_link_interval)
        register_p(self._broadcast_status, seconds=broadcast_interval)
        self.link_dead_prune = timedelta(seconds=link_dead_prune)
        self.link_dead_interval = timedelta(seconds=link_dead_interval)
        self.link_idle_refresh = timedelta(seconds=link_idle_refresh)
        register('player_logout', self._player_logout)

    def get_session(self, session_id):
        return self.session_map.get(session_id)

    def player_session(self, player_id):
        return self.player_session_map.get(player_id)

    def start_session(self):
        session_id = self._get_next_id()
        session = GameSession()
        self.session_map[session_id] = session
        session.append({'connect': session_id})
        dispatch('session_connect', session)
        return session

    def start_edit_session(self):
        session_id = self._get_next_id()
        session = ClientSession()
        self.session_map[session_id] = session
        return session_id, session

    def reconnect_session(self, session_id, player_id):
        session = self.get_session(session_id)
        if not session or not session.ld_time or not session.player or session.player.dbo_id != player_id:
            return self.start_session()
        stale_output = session.pull_output()
        client_data = {}
        session.append({'connect': session_id})
        dispatch('session_connect', session)
        session.append({'login': client_data})
        dispatch('user_connect', session.user, client_data)
        dispatch('player_connect', session.player, client_data)
        session.append_list(stale_output)
        session.player.display_line("-- Reconnecting Session --", 'system')
        session.player.parse("look")
        return session

    def login(self, session, user_name, password):
        user_name = user_name.lower()
        try:
            user = user_manager.validate_user(user_name, password)
        except ClientError as ce:
            HQCKSO({'login_failure': ce.client_message})
            return
        session.connect_user(user)
        if len(user.player_ids) == 1:
            self.start_player(session, user.player_ids[0])
        elif user_name != user.user_name:
            self.start_player(session, user_name)
        else:
            client_data = {}
            dispatch('user_connect', user, client_data)
            session.append({'user_login': client_data})

    def start_player(self, session, player_id):
        old_session = self.player_session(player_id)
        if old_session:
            player = old_session.player
            old_session.player = None
            old_session.user = None
            old_session.append({'logout': 'other_location'})
            self._connect_session(session, player, '-- Existing Session Logged Out --')
            player.parse('look')
        else:
            player = user_manager.find_player(player_id)
            if not player:
                session.append('logout')
                return
            self._connect_session(session, player, 'Welcome {}'.format(player.name))
            user_manager.login_player(player)
        client_data = {}
        dispatch('user_connect', session.user, client_data)
        dispatch('player_connect', player, client_data)
        session.append({'login': client_data})
        if not old_session:
            dispatch('player_login', player)
        self.player_info_map[player.dbo_id] = session.player_info(session.activity_time)
        self._broadcast_status()

    def _connect_session(self, session, player, text):
        if player.user_id != session.user.dbo_id:
            raise ClientError("Player user does not match session user")
        self.player_session_map[player.dbo_id] = session
        session.connect_player(player)
        session.display_line({'text': text, 'display': 'system'})

    def _player_logout(self, session):
        session.user = None
        player = session.player
        if not player:
            return
        player.last_logout = int(time.time())
        user_manager.logout_player(player)
        session.player = None
        del self.player_info_map[player.dbo_id]
        del self.player_session_map[player.dbo_id]
        session.append({'logout': 'logout'})
        self._broadcast_status()

    def _get_next_id(self):
        u_session_id = b64encode(bytes(urandom(16))).decode()
        while self.get_session(u_session_id):
            u_session_id = b64encode(bytes(urandom(16))).decode()
        return u_session_id

    def _refresh_link_status(self):
        now = datetime.now()
        for session_id, session in list(self.session_map.items()):
            if session.ld_time:
                if now - session.ld_time > self.link_dead_prune:
                    del self.session_map[session_id]
                    session.disconnect()
            elif session.request:
                if now - session.attach_time >= self.link_idle_refresh:
                    session.append({"keep_alive": True})
            elif now - session.attach_time > self.link_dead_interval:
                session.link_failed("Timeout")

    def _broadcast_status(self):
        now = datetime.now()
        for session in self.player_session_map.values():
            if session.player:
                self.player_info_map[session.player.dbo_id] = session.player_info(now)
        dispatch('player_list', self.player_info_map)


@requires('json_encode')
class ClientSession():
    def __init__(self):
        self._pulse_reg = None
        self.attach_time = datetime.now()
        self.request = None
        self.ld_time = None
        self._reset()

    def attach(self, request):
        if self.request:
            self.reattach(request)
        else:
            self.attach_time = datetime.now()
            self.ld_time = None
            self.request = request

    def reattach(self, request):
        self._push({'link_status': 'cancel'})
        self.request = request
        self._push({'link_status': 'good'})

    def append(self, data):
        if data:
            self._output.append(data)
        if not self._pulse_reg:
            self._pulse_reg = register("pulse", self._push_output)

    def append_list(self, data):
        self._output += data
        self.append(None)

    def pull_output(self):
        self.activity_time = datetime.now()
        output = self._output
        if self._pulse_reg:
            unregister(self._pulse_reg)
            self._pulse_reg = None
        self._reset()
        return output

    def link_failed(self, reason):
        debug("Link failed {}", reason)
        self.ld_time = datetime.now()
        self.request = None

    def disconnect(self):
        dispatch('session_disconnect', self)
        detach_events(self)

    def _push_output(self):
        if self.request:
            self._output.append({'link_status': "good"})
            self._push(self._output)
            unregister(self._pulse_reg)
            self._pulse_reg = None
            self._reset()

    def _reset(self):
        self._lines = []
        self._output = []
        self._status = None

    def _push(self, output):
        self.request.write(self.json_encode(output))
        self.request.finish()
        self.request = None


class GameSession(ClientSession):
    def __init__(self):
        super().__init__()
        self.user = None
        self.player = None

    def connect_user(self, user):
        self.user = user
        self.activity_time = datetime.now()

    def connect_player(self, player):
        self.player = player
        player.session = self
        self.activity_time = datetime.now()

    def player_info(self, now):
        if self.ld_time:
            status = "Link Dead"
        else:
            idle = (now - self.activity_time).seconds
            if idle < 60:
                status = "Active"
            else:
                status = "Idle: " + str(idle // 60) + "m"
        return {'status': status, 'name': self.player.name, 'loc': self.player.env.title}

    def display_line(self, display_line):
        if not self._lines:
            self.append({'display': {'lines': self._lines}})
        self._lines.append(display_line)

    def update_status(self, status):
        try:
            self._status.update(status)
        except AttributeError:
            self._status = status
            self.append({'status': status})

    def disconnect(self):
        dispatch('player_logout', self)
        super().disconnect()
