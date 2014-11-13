from lampost.comm.broadcast import BroadcastMap
from lampost.context.resource import m_requires
from lampost.datastore.dbo import RootDBO, DBOField
from lampost.mud.action import mud_action

m_requires(__name__, 'datastore')


def _post_init():
    global socials
    socials = load_object_set(Social)


class Social(RootDBO):
    dbo_key_type = 'social'
    dbo_set_key = 'socials'

    b_map = DBOField({})

    msg_class = 'social'

    def on_loaded(self):
        mud_action(self.dbo_id)(self)
        self.broadcast_map = BroadcastMap(**self.b_map)

    def __call__(self, source, target, **_):
        source.broadcast(target=target, broadcast_map=self.broadcast_map)


@mud_action('socials')
def socials_action(**_):
    return " ".join(sorted([social.dbo_id for social in socials]))
