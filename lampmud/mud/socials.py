from lampmud.comm.broadcast import BroadcastMap
from lampost.di.resource import m_requires, Injected
from lampost.db.dbo import KeyDBO, OwnerDBO
from lampost.db.dbofield import DBOField
from lampost.gameops.action import make_action
from lampmud.mud.action import mud_action

m_requires(__name__, 'log',  'mud_actions')

db = Injected('datastore')


def _post_init():
    global socials
    socials = db.load_object_set(Social)


class Social(KeyDBO, OwnerDBO):
    dbo_key_type = 'social'
    dbo_set_key = 'socials'

    b_map = DBOField({})

    msg_class = 'social'

    def on_loaded(self):
        try:
            if mud_actions[self.dbo_id] != self:
                warn("Mud action already exists for social id {}", self.dbo_id)
        except KeyError:
            mud_actions[(self.dbo_id,)] = make_action(self, self.dbo_id)
        self.broadcast_map = BroadcastMap(**self.b_map)

    def __call__(self, source, target, **_):
        source.broadcast(target=target, broadcast_map=self.broadcast_map)


@mud_action('socials')
def socials_action(**_):
    return " ".join(sorted([social.dbo_id for social in socials]))
