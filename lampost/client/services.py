from collections import defaultdict
from lampost.context.resource import m_requires, provides
from lampost.util.lmutil import StateError

m_requires('session_manager', 'dispatcher', __name__)

client_services = {}


def client_service(service_id):
    def wrapper(cls):
        client_services[service_id] = cls()
        return cls
    return wrapper


class ClientService(object):
    def __init__(self):
        self.sessions = set()

    def register(self, session, data):
        self.sessions.add(session)

    def unregister(self, session):
        self.sessions.remove(session)

    def _session_dispatch(self, event):
        for session in self.sessions:
            session.append(event)


@client_service('player_list')
class PlayerListService(ClientService):

    def _post_init(self):
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


@provides('client_services')
class ClientServiceManager(object):

    def _post_init(self):
        register('session_disconnect', self.session_disconnect)
        for service in client_services.itervalues():
            try:
                service._post_init()
            except AttributeError:
                pass

    def register(self, service_id, session, data):
        try:
            return client_services[service_id].register(session, data)
        except KeyError:
            raise StateError("No such service.")

    def unregister(self, service_id, session):
        try:
            return client_services[service_id].unregister(session)
        except KeyError:
            raise StateError("No such service.")

    def session_disconnect(self, session):
        for service in client_services.itervalues():
            service.unregister(session)