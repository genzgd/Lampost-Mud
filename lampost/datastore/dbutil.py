from lampost.context.resource import m_requires
from lampost.datastore import classes
from lampost.editor.admin import admin_op

m_requires(__name__, 'log', 'datastore', 'json_decode', 'config_manager')


@admin_op
def rebuild_indexes(dbo_cls):
    for ix_name in dbo_cls.dbo_indexes:
        delete_key('ix:{}:{}'.format(dbo_cls.dbo_key_type, ix_name))
    for dbo_id in fetch_set_keys(dbo_cls.dbo_set_key):
        try:
            dbo_key = '{}:{}'.format(dbo_cls.dbo_key_type, dbo_id)
            dbo_dict = json_decode(datastore.redis.get(dbo_key))
            for ix_name in dbo_cls.dbo_indexes:
                ix_value = dbo_dict.get(ix_name)
                if ix_value is not None and ix_value != '':
                    set_index('ix:{}:{}'.format(dbo_cls.dbo_key_type, ix_name), ix_value, dbo_id)
        except (ValueError, TypeError):
            warn("Missing dbo object {} from set key {}", dbo_id, dbo_cls.dbo_set_key)

@admin_op
def rebuild_owner_refs():
    delete_key('owner_index')
    for dbo_cls in classes._dbo_registry.values():
        if not dbo_cls.dbo_key_type:
            continue
        owner_field = dbo_cls.dbo_fields.get('owner_id')
        if not owner_field:
            continue
        owner_default = owner_field.default
        for dbo_id in fetch_set_keys(dbo_cls.dbo_set_key):
            try:
                dbo_key = '{}:{}'.format(dbo_cls.dbo_key_type, dbo_id)
                dbo_dict = json_decode(datastore.redis.get(dbo_key))
                owner_id = dbo_dict.get('owner_id', owner_default)
                info("Setting owner {} for dbo {}", owner_id, dbo_key)
            except (ValueError, TypeError):
                warn("Missing dbo object {} from set key {}", dbo_id, dbo_cls.dbo_set_key)
