from twisted.web.resource import Resource
from lampost.client.resources import request
from lampost.context.resource import m_requires, requires
from lampost.dto.rootdto import RootDTO
from lampost.model.player import Player
from lampost.util.lmutil import DataError

m_requires('datastore', 'perm', 'user_manager',__name__)

class PlayerResource(Resource):
    def __init__(self):
        Resource.__init__(self)
        self.putChild('list', PlayerList())
        self.putChild('delete', PlayerDelete())

class PlayerList(Resource):
    @request
    def render_POST(self, content, session):
        return [PlayerDTO(key.split(':')[1]) for key in fetch_set_keys("players")]

@requires('user_manager')
class PlayerDelete(Resource):
    @request
    def render_POST(self, content, session):
        user, player = self.user_manager.find_user(content.player_id)
        if not user or not player:
            raise DataError("Player no longer exists.")
        if player.imm_level >= perm_level('supreme'):
            raise DataError("Cannot delete root user.")
        if hasattr(player, 'session'):
            raise DataError("Player is logged in.")
        user_level = self.user_manager.user_imm_level(user)
        if user_level > 0:
            check_perm(session, 'supreme')
        else:
            check_perm(session, 'admin')
        self.user_manager.delete_player(user, player)


class PlayerDTO(RootDTO):
    def __init__(self, id):
        player = load_object(Player, id)
        if not hasattr(player, 'session'):
            evict_object(player)
        self.id = id
        self.level = getattr(player, 'level', 0)
        self.logged_in = 'Yes' if hasattr(player, 'session') else 'No'
        self.user_id = player.user_id
        self.imm_level = perm_name(getattr(player, 'imm_level', 0))
        self.created = player.created
        self.last_login = player.last_login
        self.last_logout = player.last_logout


