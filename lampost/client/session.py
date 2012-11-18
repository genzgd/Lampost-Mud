import time
from datetime import datetime, timedelta
from lampost.context.resource import requires, provides
from lampost.dto.display import Display, DisplayLine
from lampost.dto.link import LinkCancel, LinkGood
from lampost.dto.rootdto import RootDTO
from os import urandom
from base64 import b64encode

LINK_DEAD_INTERVAL = timedelta(seconds=15)
LINK_DEAD_PRUNE = timedelta(minutes=2)
LINK_IDLE_REFRESH = timedelta(seconds=45)

@requires('nature')
class LoginResult(RootDTO):
    def __init__(self, player):
        login = RootDTO()
        login.name = player.name
        login.privilege = player.imm_level
        login.editors = self.nature.editors(player)
        login.user_id = player.user_id
        self.login = login

@provides('sm')
@requires('dispatcher', 'datastore', 'nature', 'user_manager')
class SessionManager():
    def __init__(self):
        self.session_map = {}
        self.player_map = {}
        self.player_session_map = {}
        self.register_p(self._refresh_link_status, seconds=5)

    def get_session(self, session_id):
        return self.session_map.get(session_id)

    def user_session(self, user_id):
        return self.player_session_map.get(user_id, None)

    def start_session(self):
        session_id = self._get_next_id()
        session = UserSession()
        self.session_map[session_id] = session
        return self._respond(RootDTO(connect=session_id))

    def child_session(self, parent_id):
        parent_session = self.get_session(parent_id)

    def reconnect_session(self, session_id, player_id):
        session = self.get_session(session_id)
        if not session or not session.ld_time or not session.player or session.player.dbo_id != player_id:
            return self.start_session()
        session.display_line(DisplayLine("-- Reconnecting Session --"))
        return self._respond(LoginResult(session.player).merge(RootDTO(connect=session_id)))

    def login(self, session, user_id, password):
        result, user, player  = self.user_manager.validate_user(user_id, password)
        if result != "ok":
            return result

        old_session = self.user_session(player.dbo_id)
        if old_session:
            if old_session == session: #Could happen with some weird timing, apparently
                session.append(player.parse("look"))
                return self._respond(LoginResult(player))
            old_session.player = None
            old_session.user_id = 0
            del self.player_session_map[player.dbo_id]
            old_session.append(RootDTO(logout="other_location"))
        else:
            player.last_login = int(time.time())
            if not player.created:
                player.created = player.last_login
            player.session = session
            self.nature.baptise(player)
            player.start()
        if old_session:
            player.display_line("-- Existing Session Logged Out --", 0x002288)
        else:
            player.display_line("Welcome " + player.name,  0x002288)
        self.player_map[player.dbo_id] = session.login(player, user)
        self.player_session_map[player.dbo_id] = session
        player.parse("look")
        return self._respond(LoginResult(player))

    def logout(self, session):
        player = session.player
        player.last_logout = int(time.time())
        player.age += player.last_logout - player.last_login
        player.leave_env()
        player.detach()
        session.player = None
        del self.player_map[player.dbo_id]
        self.save_object(player)
        self.evict_object(player)
        del self.player_session_map[player.dbo_id]
        return self._respond(RootDTO(logout="logout"))

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
                    session.append(RootDTO(keepalive=True))
            elif now - session.attach_time > LINK_DEAD_INTERVAL:
                session.link_failed("Timeout")
            if session.player:
                self.player_map[session.player.dbo_id] = session.player_info(now)
        self._display_players()

    def _respond(self, rootDto):
        return rootDto.merge(RootDTO(player_list=self.player_map))

    def _display_players(self):
        player_list_dto = RootDTO(player_list=self.player_map)
        for session in self.session_map.itervalues():
            session.append(player_list_dto)

@requires('dispatcher')
class BaseSession(object):
    def __init__(self):
        self.output = RootDTO()
        self.player = None
        self.attach_time = datetime.now()
        self.ld_time = None
        self.request = None
        self.pulse_reg = None
        self.user = None

    def attach(self, request):
        if self.request:
            self.push(LinkCancel())
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
        self.output.merge(data)

    def pull_output(self):
        output = self.output
        if self.pulse_reg:
            self.unregister(self.pulse_reg)
            self.pulse_reg = None
        self.output = RootDTO()
        return output

    def push_output(self):
        if self.request:
            self.push(self.output.merge(LinkGood()))
            self.output = RootDTO()
            self.unregister(self.pulse_reg)
            self.pulse_reg = None

    def push(self, output):
        self.request.write(output.json)
        self.request.finish()
        self.request = None

    @property
    def privilege(self):
        return self.player.imm_level if self.player else 0


class UserSession(BaseSession):
    def __init__(self):
        super(UserSession, self).__init__()

    def login(self, player, user):
        self.player = player
        self.user = user
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
        info = RootDTO(status=status)
        info.name = self.player.name
        info.loc = self.player.env.title
        return info

    def display_line(self, display_line):
        display = Display()
        display.append(display_line)
        self.append(display)






