
from lampost.di.config import ConfigVal
from lampost.di.resource import Injected, module_inject

from lampmud.env.instance import AreaInstance

db = Injected('datastore')
ev = Injected('dispatcher')
module_inject(__name__)

preserve_hours = ConfigVal('instance_preserve_hours')

instance_map = {}


def _post_init():
    ev.register('maintenance', remove_old)


def next_instance():
    instance_id = db.db_counter('instance_id')
    area_instance = AreaInstance(instance_id)
    instance_map[instance_id] = area_instance
    return area_instance


def remove_old():
    stale_pulse = db.future_pulse(preserve_hours * 60 * 60)
    for instance_id, instance in instance_map.copy().items():
        if instance.pulse_stamp < stale_pulse and not [entity for entity in instance.entities
                                                       if hasattr(entity, 'is_player') and entity.session]:
            delete(instance_id)


def get(instance_id):
    return instance_map.get(instance_id)


def delete(instance_id):
    del instance_map[instance_id]
