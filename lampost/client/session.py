import time

from datetime import datetime, timedelta
from os import urandom
from base64 import b64encode

from lampost.context.resource import requires, provides
from lampost.model.player import Player
from lampost.client.user import User


LINK_DEAD_INTERVAL = timedelta(seconds=15)
LINK_DEAD_PRUNE = timedelta(minutes=2)
LINK_IDLE_REFRESH = timedelta(seconds=45)


@provides('sm')
@requires('dispatcher', 'datastore', 'nature', 'user_manager')
class SessionManager(object):
    def __init__(self):
        self.session_map = {}
        self.player_info_map = {}
        self.player_session_map = {}
        self.register_p(self._refresh_link_status, seconds=5)

    def _login_result(self, user, player):
        return {'name': player.name, 'privilege': player.imm_level, 'editors': self.nature.editors(player), 'user_id': user.dbo_id,
                'player_ids': user.player_ids}

    def get_session(self, session_id):
        return self.session_map.get(session_id)

    def player_session(self, player_id):
        return self.player_session_map.get(player_id, None)

    def start_session(self):
        session_id = self._get_next_id()
        session = UserSession()
        self.session_map[session_id] = session
        return self._respond(connect=session_id)

    def reconnect_session(self, session_id, player_id):
        session = self.get_session(session_id)
        if not session or not session.ld_time or not session.player or session.player.dbo_id != player_id:
            return self.start_session()
        session.player.display_line("-- Reconnecting Session --")
        session.player.parse("look")
        user = self.datastore.load_object(User, session.player.user_id)
        return self._respond(login=self._login_result(user, session.player), connect=session_id)

    def login(self, session, user_id, password):
        user_id = unicode(user_id).lower()
        result, user = self.user_manager.validate_user(user_id, password)
        if result != "ok":
            return {"login_failure": result}
        session.connect_user(user)
        if len(user.player_ids) == 1:
            return self._start_player(session, user, user.player_ids[0])
        if user_id != user.user_id:
            return self._start_player(session, user, user_id)

        user_login = {'user_id': user.user_id, 'player_ids': user.player_ids}
        return self._respond(user_login=user_login)

    def _start_player(self, session, user, player_id):
        old_session = self.player_session(player_id)
        if old_session:
            player = old_session.player
            old_session.player = None
            old_session.user_id = 0
            old_session.append({'logout': 'other_location'})
            intro_line = '-- Existing Session Logged Out --'
        else:
            player = self.datastore.load_object(Player, player_id)
            intro_line = "Welcome " + player.name
            self.nature.baptise(player)
            player.last_login = int(time.time())
            if not player.created:
                player.created = player.last_login
            player.start()
        self.player_info_map[player.dbo_id] = session.connect_player(player)
        self.player_session_map[player.dbo_id] = session
        player.display_line(intro_line,  0x002288)
        player.parse("look")
        return self._respond(login=self._login_result(user, player))

    def logout(self, session):
        player = session.player
        player.last_logout = int(time.time())
        player.age += player.last_logout - player.last_login
        player.leave_env()
        player.detach()
        session.player = None
        del self.player_info_map[player.dbo_id]
        self.save_object(player)
        self.evict_object(player)
        del self.player_session_map[player.dbo_id]
        return self._respond(logout="logout")

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
                    continue
            elif session.request:
                if now - session.attach_time > LINK_IDLE_REFRESH:
                    session.append({"keep_alive":True})
            elif now - session.attach_time > LINK_DEAD_INTERVAL:
                session.link_failed("Timeout")
            if session.player:
                self.player_info_map[session.player.dbo_id] = session.player_info(now)
        self._display_players()

    def _respond(self, **response):
        response['player_list'] = self.player_info_map
        return response

    def _display_players(self):
        for session in self.session_map.itervalues():
            session.append({"player_list":self.player_info_map})


@requires('dispatcher', 'encode')
class UserSession(object):
    def __init__(self):
        self.output = {}
        self.player = None
        self.attach_time = datetime.now()
        self.ld_time = None
        self.request = None
        self.pulse_reg = None
        self.user = None

    def attach(self, request):
        if self.request:
            self.push({'link_status':'cancel'})
        self.attach_time = datetime.now()
        self.ld_time = None
        self.request = request
        self.request.notifyFinish().addErrback(self.link_failed)

    def link_failed(self, error):
        self.ld_time = datetime.now()
        self.request = None

    def append(self, data):
        if not self.pulse_reg:
            self.pulse_reg = self.register("pulse", self.push_output)
        self.output.update(data)

    def pull_output(self):
        output = self.output
        if self.pulse_reg:
            self.unregister(self.pulse_reg)
            self.pulse_reg = None
        self.output = {}
        return output

    def push_output(self):
        if self.request:
            self.output['link_status'] = "good"
            self.push(self.output)
            self.output = {}
            self.unregister(self.pulse_reg)
            self.pulse_reg = None

    def push(self, output):
        self.request.write(self.encode(output))
        self.request.finish()
        self.request = None

    def connect_user(self, user):
        self.user = user
        self.activity_time = datetime.now()

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
                status =  "Idle: " + str(idle / 60) + "m"
        return {'status': status, 'name':self.player.name, 'loc':self.player.env.title}

    def display_line(self, display_line):
        display = self.output.get('display', {'lines':[]})
        display['lines'].append(display_line)
        self.append({'display':display})

    @property
    def privilege(self):
        return self.player.imm_level if self.player else 0







