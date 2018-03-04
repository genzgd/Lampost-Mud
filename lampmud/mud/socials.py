from lampost.di.app import on_app_start

from lampmud.comm.broadcast import BroadcastMap
from lampost.di.resource import Injected, module_inject
from lampost.db.dbo import OwnerDBO
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
    for social in db.load_object_set('social'):
        add_social_action(social)


def add_social_action(social):
    if mud_actions.primary(social.dbo_id):
        log.warn("Mud action already exists for social id {}", social.dbo_id)
    else:
        mud_actions.add(make_action(social, social.dbo_id))
        all_socials[social.dbo_id] = social


def remove_social_action(social):
    all_socials.pop(social.dbo_id)
    mud_actions.remove(social)


class Social(OwnerDBO):
    dbo_key_type = 'social'
    dbo_set_key = 'socials'

    b_map = DBOField({})

    msg_class = 'social'

    def _on_loaded(self):
        self.broadcast_map = BroadcastMap(**self.b_map)

    def _on_db_created(self):
        add_social_action(self)

    def _on_db_deleted(self):
        remove_social_action(self)

    def __call__(self, source, target, **_):
        source.broadcast(target=target, broadcast_map=self.broadcast_map)


@mud_action('socials')
def socials_action(**_):
    socials = sorted(all_socials.keys())
    if socials:
        return " ".join(socials)
    return "No socials created!"
