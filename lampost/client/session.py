import time

from datetime import datetime, timedelta
from os import urandom
from base64 import b64encode

from lampost.context.resource import m_requires, requires, provides
from lampost.gameops.display import SYSTEM_DISPLAY


LINK_DEAD_INTERVAL = timedelta(seconds=15)
LINK_DEAD_PRUNE = timedelta(minutes=2)
LINK_IDLE_REFRESH = timedelta(seconds=45)

m_requires('log', 'dispatcher', __name__)


@provides('session_manager')
@requires('user_manager')
class SessionManager(object):
    def __init__(self):
        self.session_map = {}
        self.player_info_map = {}
        self.player_session_map = {}
        register_p(self._refresh_link_status, seconds=5)
        register_p(self._broadcast_player_list, seconds=30)

    def get_session(self, session_id):
        return self.session_map.get(session_id, None)

    def player_session(self, player_id):
        return self.player_session_map.get(player_id, None)

    def start_session(self):
        session_id = self._get_next_id()
        session = UserSession()
        self.session_map[session_id] = session
        connect = {'connect': session_id}
        dispatch('session_connect', session, connect)
        return connect

    def reconnect_session(self, session_id, player_id):
        session = self.get_session(session_id)
        if not session or not session.ld_time or not session.player or session.player.dbo_id != player_id:
            return self.start_session()
        session.player.display_line("-- Reconnecting Session --", SYSTEM_DISPLAY)
        session.player.parse("look")
        client_data = {}
        connect = {'connect': session_id, 'login': client_data}
        dispatch('session_connect', session, connect)
        dispatch('user_connect', session.user, client_data)
        dispatch('player_connect', session.player, client_data)
        return connect

    def login(self, session, user_name, password):
        user_name = unicode(user_name).lower()
        result, user = self.user_manager.validate_user(user_name, password)
        if result != "ok":
            return {"login_failure": result}
        session.connect_user(user)
        if len(user.player_ids) == 1:
            return self.start_player(session, user.player_ids[0])
        if user_name != user.user_name:
            return self.start_player(session, user_name)
        client_data = {}
        dispatch('user_connect', user, client_data)
        return {'user_login': client_data}

    def start_player(self, session, player_id):
        old_session = self.player_session(player_id)
        if old_session:
            player = old_session.player
            old_session.player = None
            old_session.user = None
            old_session.append({'logout': 'other_location'})
            intro_line = '-- Existing Session Logged Out --'
        else:
            player = self.user_manager.login_player(player_id)
            intro_line = "Welcome " + player.name
        if player.user_id != session.user.dbo_id:
            raise StateError("Player user does not match session user")
        self.player_info_map[player.dbo_id] = session.connect_player(player)
        self.player_session_map[player.dbo_id] = session
        if not old_session:
            dispatch('player_login', player)
        player.display_line(intro_line, SYSTEM_DISPLAY)
        player.parse("look")
        client_data = {}
        dispatch('user_connect', session.user, client_data)
        dispatch('player_connect', player, client_data)
        return {'login': client_data}

    def logout(self, session):
        player = session.player
        if player:
            player.last_logout = int(time.time())
            self.user_manager.logout_player(player)
            session.player = None
            del self.player_info_map[player.dbo_id]
            del self.player_session_map[player.dbo_id]
            dispatch('player_logout', player)
        session.user = None
        return {'logout': 'logout'}

    def _get_next_id(self):
        u_session_id = b64encode(str(urandom(16)))
        while self.get_session(u_session_id):
            u_session_id = b64encode(str(urandom(16)))
        return u_session_id

    def _refresh_link_status(self):
        now = datetime.now()
        for session_id, session in self.session_map.items():
            if session.ld_time:
                if now - session.ld_time > LINK_DEAD_PRUNE:
                    if session.player:
                        self.logout(session)
                    del self.session_map[session_id]
                    dispatch('session_disconnect', session)
                    session.disconnect()
            elif session.request:
                if now - session.attach_time >= LINK_IDLE_REFRESH:
                    session.append({"keep_alive": True})
            elif now - session.attach_time > LINK_DEAD_INTERVAL:
                session.link_failed("Timeout")

    def _broadcast_player_list(self):
        now = datetime.now()
        for session in self.player_session_map.itervalues():
            if session.player:
                self.player_info_map[session.player.dbo_id] = session.player_info(now)
        dispatch('player_list', self.player_info_map)


@requires('json_encode')
class UserSession(object):

    def __init__(self):
        self._lines = []
        self._output = []
        self._pulse_reg = None

        self.attach_time = datetime.now()
        self.request = None
        self.player = None
        self.ld_time = None
        self.user = None

    def attach(self, request):
        if self.request:
            self._push({'link_status': 'cancel'})
        self.attach_time = datetime.now()
        self.ld_time = None
        self.request = request
        self.request.notifyFinish().addErrback(self.link_failed)

    def append(self, data):
        if data not in self._output:
            self._output.append(data)
        if not self._pulse_reg:
            self._pulse_reg = register("pulse", self._push_output)

    def pull_output(self):
        self.activity_time = datetime.now()
        output = self._output
        if self._pulse_reg:
            unregister(self._pulse_reg)
            self._pulse_reg = None
        self._output = []
        self._lines = []
        return output

    def connect_user(self, user):
        self.user = user
        self._activity_time = datetime.now()

    def connect_player(self, player):
        self.player = player
        player.session = self
        self.activity_time = datetime.now()
        return self.player_info(self.activity_time)

    def player_info(self, now):
        if self.ld_time:
            status = "Link Dead"
        else:
            idle = (now - self.activity_time).seconds
            if idle < 60:
                status = "Active"
            else:
                status = "Idle: " + str(idle / 60) + "m"
        return {'status': status, 'name': self.player.name, 'loc': self.player.env.title}

    def display_line(self, display_line):
        if not self._lines:
            self.append({'display': {'lines': self._lines}})
        self._lines.append(display_line)

    def link_failed(self, error):
        if self.player:
            warn("Link failed for {} ".format(self.player.name, repr(error)), self)
        self.ld_time = datetime.now()
        self.request = None

    def disconnect(self):
        detach_events(self)

    def _push_output(self):
        if self.request:
            self._output.append({'link_status': "good"})
            self._push(self._output)
            self._output = []
            self._lines = []
            unregister(self._pulse_reg)
            self._pulse_reg = None

    def _push(self, output):
        self.request.write(self.json_encode(output))
        self.request.finish()
        self.request = None

    @property
    def privilege(self):
        return self.player.imm_level if self.player else 0

