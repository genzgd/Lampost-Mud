from tornado.web import RequestHandler

from lampost.server.handlers import SessionHandler
from lampost.context.resource import m_requires
from lampost.model.player import Player
from lampost.util.lputil import ClientError

m_requires(__name__, 'log', 'session_manager', 'user_manager', 'datastore',
           'json_decode', 'json_encode', 'perm', 'edit_notify_service')


def editor_login(session):
    edit_perms = []
    player = session.player
    if has_perm(player, 'builder'):
        edit_perms.extend(['build', 'mud'])
    if has_perm(player, 'admin'):
        edit_perms.extend(['player'])
    if has_perm(player, 'supreme'):
        edit_perms.extend(['admin', 'config'])
    session.append({'editor_login': {'edit_perms': edit_perms, 'playerId': player.dbo_id, 'imm_level': player.imm_level,
                                     'playerName': player.name}})
    edit_notify_service.register(session)


class EditConnect(RequestHandler):
    def post(self):
        session_id = self.request.headers.get('X-Lampost-Session')
        session = session_manager.get_session(session_id)
        if not session:
            session_id, session = session_manager.start_edit_session()
            session.player = None
        if not session.player:
            content = json_decode(self.request.body.decode())
            game_session = session_manager.get_session(content.get('gameSessionId'))
            if game_session:
                if getattr(game_session, 'user', None) and game_session.user.dbo_id == content.get('userId'):
                    session.player = game_session.player
                else:
                    log.warn("Edit session connected with non-match user id")
        session.append({'connect': session_id})
        if session.player:
            editor_login(session)
        else:
            session.append({'connect_only': True})
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(json_encode(session.pull_output()))


class EditLogin(SessionHandler):
    def main(self):
        content = self._content()
        user_name = content.userId.lower()
        try:
            user = user_manager.validate_user(user_name, content.password)
        except ClientError:
            self.session.append({'login_failure': "Invalid user name or password."})
            return
        imm = None
        for player in (load_object(player_id, Player) for player_id in user.player_ids):
            if player.dbo_id == user_name:
                if player.imm_level:
                    imm = player
                    break
                self.session.append({'login_failure': '{} is not immortal.'.format(player.name)})
                return
            if player.imm_level and (not imm or player.imm_level > imm.imm_level):
                imm = player
        if imm:
            self.session.player = imm
            editor_login(self.session)
        else:
            self.session.append({'login_failure': 'No immortals on this account.'})


class EditLogout(SessionHandler):
    def main(self):
        edit_notify_service.unregister(self.session)
        self.session.player = None
        self.session.append({'editor_logout': True})
