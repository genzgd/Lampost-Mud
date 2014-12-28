from lampost.context.resource import m_requires
from lampost.datastore import classes
from lampost.editor.admin import admin_op
from lampost.model.player import Player

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
    # Yes, we're abusing the keys command.  If we required a later version of Redis (2.8) we could use SCAN
    for owned_key in datastore.redis.keys('owned:*'):
        delete_key(owned_key)
    for dbo_cls in classes._dbo_registry.values():
        dbo_key_type = getattr(dbo_cls, 'dbo_key_type', None)
        if not dbo_key_type:
            continue
        owner_field = dbo_cls.dbo_fields.get('owner_id', None)
        if not owner_field:
            continue
        for dbo in load_object_set(dbo_cls):
            if dbo.owner_id in perm.immortals:
                dbo.db_created()
            else:
                warn("owner id {} not found, setting owner of {} to default {}", owner_id, dbo_key, owner_field.default)
                dbo.change_owner()

@admin_op
def rebuild_immortal_list():
    delete_key('immortals')
    for player in load_object_set(Player):
        if player.imm_level:
            set_db_hash('immortals', player.dbo_id, player.imm_level)

