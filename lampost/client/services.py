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

    def _session_dispatch(self, event, source_session=None):
        for session in self.sessions:
            if session != source_session:
                session.append(event)


@provides('player_list_service')
class PlayerListService(ClientService):

    def _post_init(self):
        super(PlayerListService, self)._post_init()
        register('player_list', self._process_list)

    def register(self, session, data):
        super(PlayerListService, self).register(session, data)
        session.append({'player_list': session_manager.player_info_map})

    def _process_list(self, player_list):
        self._session_dispatch({'player_list': player_list})


@provides('any_login_service')
class AnyLoginService(ClientService):

    def _post_init(self):
        super(AnyLoginService, self)._post_init()
        register('player_login', self._process_login)

    def _process_login(self, player):
        self._session_dispatch({'any_login': {'name': player.name}})


@provides('edit_update_service')
class EditUpdateService(ClientService):

    def _post_init(self):
        super(EditUpdateService, self)._post_init()
        register('edit_update', self._edit_update)

    def _edit_update(self, edit_type, model, source_session=None):
        update = {'edit_type': edit_type, 'model': model, 'local': not source_session}
        self._session_dispatch({'edit_update': update}, source_session)


