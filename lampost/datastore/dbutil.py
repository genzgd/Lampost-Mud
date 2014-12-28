from lampost.context.resource import m_requires
from lampost.datastore import classes
from lampost.editor.admin import admin_op

m_requires(__name__, 'log', 'datastore', 'perm', 'config_manager')


@admin_op
def rebuild_indexes(dbo_cls):
    for ix_name in dbo_cls.dbo_indexes:
        delete_key('ix:{}:{}'.format(dbo_cls.dbo_key_type, ix_name))
    for dbo_id in fetch_set_keys(dbo_cls.dbo_set_key):
        try:
            dbo_key = '{}:{}'.format(dbo_cls.dbo_key_type, dbo_id)
            dbo_dict = load_raw(dbo_key)
            for ix_name in dbo_cls.dbo_indexes:
                ix_value = dbo_dict.get(ix_name)
                if ix_value is not None and ix_value != '':
                    set_index('ix:{}:{}'.format(dbo_cls.dbo_key_type, ix_name), ix_value, dbo_id)
        except (ValueError, TypeError):
            warn("Missing dbo object {} from set key {}", dbo_id, dbo_cls.dbo_set_key)

@admin_op
def rebuild_owner_refs():
    system_default = config_manager.system_accounts[0]
    for immortal_id in perm.immortals.keys():
        delete_key('owned:{}'.format(immortal_id))
    for dbo_cls in classes._dbo_registry.values():
        dbo_key_type = getattr(dbo_cls, 'dbo_key_type', None)
        if not dbo_key_type:
            continue
        owner_field = dbo_cls.dbo_fields.get('owner_id', None)
        if not owner_field:
            continue
        owner_default = owner_field.default
        for dbo_id in fetch_set_keys(dbo_cls.dbo_set_key):
            try:
                dbo_key = '{}:{}'.format(dbo_cls.dbo_key_type, dbo_id)
                dbo_dict = load_raw(dbo_key)
                owner_id = dbo_dict.get('owner_id', owner_default)
                if owner_id not in perm.immortals:
                    warn("owner id {} not found, setting owner of {} to system default {}", owner_id, dbo_key, system_default)
                    owner_id = system_default
                    if owner_id == owner_default:
                        del dbo_dict['owner_id']
                    else:
                        dbo_dict['owner_id'] = owner_id
                    save_raw(dbo_key, dbo_dict)
                add_set_key('owned:{}'.format(owner_id), dbo_key)
            except (ValueError, TypeError):
                warn("Missing dbo object {} from set key {}", dbo_id, dbo_cls.dbo_set_key)
