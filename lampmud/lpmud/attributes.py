from lampost.di.app import on_app_start
from lampost.di.config import config_value
from lampost.db.dbofield import DBOField
from lampost.db.registry import get_dbo_class

attributes = []
attr_list = []

pool_keys = []
resource_pools = []


@on_app_start(priority=200)
def _init():
    global attributes
    global resource_pools
    global pool_keys
    global attr_list

    attributes = config_value('attributes')
    attr_list = [attr['dbo_id'] for attr in attributes]

    resource_pools = config_value('resource_pools')
    pool_keys = [(pool['dbo_id'], "base_{}".format(pool['dbo_id'])) for pool in resource_pools]

    player_cls = get_dbo_class('player')
    player_cls.add_dbo_fields({attr['dbo_id']: DBOField(0) for attr in attributes})
    player_cls.add_dbo_fields({pool['dbo_id']: DBOField(0) for pool in resource_pools})


def base_pools(entity):
    for pool in resource_pools:
        total = sum(getattr(entity, key) * value for key, value in pool['calc'].items())
        setattr(entity, 'base_{}'.format(pool['dbo_id']), total)


def fill_pools(entity):
    base_pools(entity)
    for pool_id, base_pool_id in pool_keys:
        setattr(entity, pool_id, getattr(entity, base_pool_id))


def restore_attrs(entity):
    for attr in attr_list:
        setattr(entity, attr, getattr(entity, "perm_{}".format(attr)))


def need_refresh(entity):
    for pool_id, base_pool_id in pool_keys:
        if getattr(entity, pool_id) < getattr(entity, base_pool_id):
            return True
