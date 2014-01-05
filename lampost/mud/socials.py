from lampost.context.resource import m_requires
from lampost.datastore.dbo import RootDBO, DBOField
from lampost.mud.action import mud_action

m_requires('datastore',  __name__)


def _post_init():
    global socials
    socials = load_object_set(Social)


class Social(RootDBO):
    dbo_key_type = 'social'
    dbo_set_key = 'socials'

    b_map = DBOField({})

    msg_class = 'rec_social'

    def on_loaded(self):
        mud_action(self.dbo_id)(self)

    def __call__(self, source, target, **ignored):
        source.broadcast(target=target, **self.b_map)


@mud_action('socials')
def socials_action(**ignored):
    return " ".join(sorted([social.dbo_id for social in socials]))
