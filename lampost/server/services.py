from lampost.context.resource import m_requires

m_requires(__name__, 'log', 'session_manager', 'dispatcher', 'perm')


class ClientService():
    def __init__(self):
        self.sessions = set()

    def _post_init(self):
        register('session_disconnect', self.unregister)

    def register(self, session, data=None):
        self.sessions.add(session)

    def unregister(self, session):
        try:
            self.sessions.remove(session)
        except KeyError:
            pass

    def _session_dispatch(self, event):
        for session in self.sessions:
            session.append(event)


class PlayerListService(ClientService):

    def _post_init(self):
        super()._post_init()
        register('player_list', self._process_list)

    def register(self, session, data):
        super().register(session, data)
        session.append({'player_list': session_manager.player_info_map})

    def _process_list(self, player_list):
        self._session_dispatch({'player_list': player_list})


class AnyLoginService(ClientService):

    def _post_init(self):
        super()._post_init()
        register('player_login', self._process_login)

    def _process_login(self, player):
        self._session_dispatch({'any_login': {'name': player.name}})


class EditUpdateService(ClientService):

    def _post_init(self):
        super()._post_init()
        register('publish_edit', self.publish_edit)

    def publish_edit(self, edit_type, edit_obj, source_session=None, local=False):
        edit_dto = edit_obj.edit_dto
        if source_session:
            local_dto = edit_dto.copy()
            local_dto['can_write'] = has_perm(source_session.player, edit_obj)
        else:
            local_dto = None
        edit_update  = {'edit_update': {'edit_type': edit_type}}

        for session in self.sessions:
            if session == source_session:
                if local:
                    event = edit_update.copy()
                    local_dto['local'] = True
                    event['edit_update']['model'] = local_dto
                    session.append(event)
            else:
                event = edit_update.copy()
                event_dto = edit_dto.copy()
                event_dto['can_write'] = has_perm(session.player, edit_obj)
                event['edit_update']['model'] = event_dto
                session.append(event)

        return local_dto
