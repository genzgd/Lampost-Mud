from tornado.web import RequestHandler
from lampost.context.resource import m_requires

m_requires(__name__, 'log', 'session_manager', 'json_decode', 'json_encode', 'perm')


def editor_login(session):
    edit_perms = []
    player = session.player
    if has_perm(player, 'creator'):
        edit_perms.extend(['area', 'room', 'mobile', 'article', 'script'])
    if has_perm(player, 'admin'):
        edit_perms.extend(['players', 'social', 'display', 'race', 'attack', 'defense'])
    if has_perm(player, 'supreme'):
        edit_perms.extend(['config'])
    session.append({'editor_login': {'edit_perms': edit_perms, 'playerId:': player.dbo_id, 'playerName': player.name}})


class EditConnect(RequestHandler):
    def post(self):
        session_id = self.request.headers.get('X-Lampost-Session')
        session = session_manager.get_session(session_id)
        if not session:
            session_id, session = session_manager.start_edit_session()
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
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(json_encode(session.pull_output()))
