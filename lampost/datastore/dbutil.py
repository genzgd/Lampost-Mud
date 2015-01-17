import time

from lampost.context.resource import m_requires
from lampost.datastore import classes
from lampost.datastore.classes import get_dbo_class
from lampost.editor.admin import admin_op
from lampost.model.player import Player
from lampost.setup.configinit import load_config


m_requires(__name__, 'log', 'datastore', 'perm')


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


@admin_op
def rebuild_all_fks():
    start_time = time.time()
    updated = 0

    def update(update_cls, set_key=None):
        nonlocal updated
        for dbo in load_object_set(update_cls, set_key):
            save_object(dbo)
            updated += 1
            for child_type in getattr(dbo_cls, 'dbo_children_types', ()):
                update(get_dbo_class(child_type), '{}_{}s:{}'.format(dbo_key_type, child_type, dbo.dbo_id))

    for holder_key in datastore.redis.keys('*:holders'):
        delete_key(holder_key)
    for ref_key in datastore.redis.keys('*:refs'):
        delete_key(ref_key)
    for dbo_cls in classes._dbo_registry.values():
        dbo_key_type = getattr(dbo_cls, 'dbo_key_type', None)
        if dbo_key_type and not hasattr(dbo_cls, 'dbo_parent_type'):
            update(dbo_cls)


    return "{} objects updated in {} seconds".format(updated, time.time() - start_time)


@admin_op
def restore_db_from_yaml(config_id='lampost', path='conf', force="no"):
    yaml_config = load_config(path)
    existing = load_object(config_id, 'config')
    if existing:
        if force != 'yes':
            return "Object exists and force is not 'yes'"
        delete_object(existing)
    config = create_from_dicts(config_id, yaml_config, True)
    config.activate()
    return 'Config {} successfully loaded from yaml files'.format(config_id)



