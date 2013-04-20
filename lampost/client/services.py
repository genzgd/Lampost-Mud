from collections import defaultdict
from lampost.context.resource import m_requires, provides
from lampost.util.lmutil import StateError

m_requires('log', 'session_manager', 'dispatcher', __name__)


class ClientService(object):
    def __init__(self):
        self.sessions = set()

    def _post_init(self):
        register('session_disconnect', self.unregister)

    def register(self, session, data):
        self.sessions.add(session)

    def unregister(self, session):
        try:
            self.sessions.remove(session)
        except KeyError:
            pass

    def _session_dispatch(self, event):
        for session in self.sessions:
            session.append(event)


@provides('player_list_service')
class PlayerListService(ClientService):

    def _post_init(self):
        super(PlayerListService, self)._post_init()
        register('player_login', self._process_login)
        register('player_logout', self._process_logout)
        register('player_list', self._process_list)

    def register(self, session, data):
        super(PlayerListService, self).register(session, data)
        return {'player_list': session_manager.player_info_map}

    def _process_login(self, player):
        self._session_dispatch({'player_login': {'id': player.dbo_id, 'data': {'status': 'Logging In', 'name': player.name, 'loc': player.env.title}}})

    def _process_logout(self, player):
        self._session_dispatch({'player_logout': {'id': player.dbo_id}})

    def _process_list(self, player_list):
        self._session_dispatch({'player_list': player_list})


@provides('any_login_service')
class AnyLoginService(ClientService):

    def _post_init(self):
        super(AnyLoginService, self)._post_init()
        register('player_login', self._process_login)

    def _process_login(self, player):
        self._session_dispatch({'any_login': {'name': player.name}})


