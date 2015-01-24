from lampost.context.config import m_configured

pool_keys = []
attr_list = []


def _on_configured():
    global attr_list, pool_keys
    pool_keys = [(pool['dbo_id'], "base_{}".format(pool['dbo_id'])) for pool in resource_pools]
    attr_list = [attr['dbo_id'] for attr in attributes]

m_configured(__name__, 'attributes', 'resource_pools')


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

