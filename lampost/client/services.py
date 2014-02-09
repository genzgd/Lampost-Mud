from lampost.context.resource import m_requires, provides

m_requires('log', 'session_manager', 'dispatcher', 'perm', __name__)


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


@provides('edit_update_service', True)
class EditUpdateService(ClientService):

    def edit_dto(self, player, dbo):
        dto = dbo.dto_value
        dto['can_write'] = has_perm(player, dbo)
        return dto

    def publish_edit(self, edit_type, model, source_session, local=False):
        event_dto = None
        for session in self.sessions:
            event = {'edit_update': {'edit_type': edit_type, 'model': self.edit_dto(session.player, model)}}
            if session == source_session:
                if local:
                    event['edit_update']['local'] = True
                    session.append(event)
                event_dto = event['edit_update']['model']
            else:
                session.append(event)
        return event_dto
