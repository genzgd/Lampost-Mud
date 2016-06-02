from lampost.di.app import on_app_start

from lampmud.comm.broadcast import BroadcastMap
from lampost.di.resource import Injected, module_inject
from lampost.db.dbo import KeyDBO, OwnerDBO
from lampost.db.dbofield import DBOField
from lampost.gameops.action import make_action
from lampmud.mud.action import mud_action

log = Injected('log')
db = Injected('datastore')
mud_actions = Injected('mud_actions')
module_inject(__name__)

all_socials = {}


@on_app_start
def _start():
    # load all socials into memory so that the appropriate actions are available
    db.load_object_set('social')


class Social(KeyDBO, OwnerDBO):
    dbo_key_type = 'social'
    dbo_set_key = 'socials'

    b_map = DBOField({})

    msg_class = 'social'

    def on_loaded(self):
        try:
            if mud_actions[(self.dbo_id,)] != self:
                log.warn("Mud action already exists for social id {}", self.dbo_id)
        except KeyError:
            mud_actions[(self.dbo_id,)] = make_action(self, self.dbo_id)
            all_socials[self.dbo_id] = self
        self.broadcast_map = BroadcastMap(**self.b_map)

    def on_deleted(self):
        all_socials.pop(self.dbo_id)
        if mud_actions[(self.dbo_id,)] == self:
            del mud_actions[(self.dbo_id,)]

    def __call__(self, source, target, **_):
        source.broadcast(target=target, broadcast_map=self.broadcast_map)


@mud_action('socials')
def socials_action(**_):
    socials = sorted(all_socials.keys())
    if socials:
        return " ".join(socials)
    return "No socials created!"
