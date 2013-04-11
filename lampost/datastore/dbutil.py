from lampost.context.resource import m_requires

m_requires('log', 'datastore', 'json_decode', __name__)


def build_indexes(dbo_cls):
    for ix_name in dbo_cls.dbo_indexes:
        datastore.redis.delete('ix:{}:{}'.format(dbo_cls.dbo_key_type, ix_name))
    for dbo_id in fetch_set_keys(dbo_cls.dbo_set_key):
        try:
            dbo_key = '{}:{}'.format(dbo_cls.dbo_key_type, dbo_id)
            dbo_dict = json_decode(datastore.redis.get(dbo_key))
            for ix_name in dbo_cls.dbo_indexes:
                ix_value = dbo_dict.get(ix_name)
                if ix_value is not None and ix_value != '':
                    set_index('ix:{}:{}'.format(dbo_cls.dbo_key_type, ix_name), ix_value, dbo_id)
        except (ValueError, TypeError):
            warn("Missing dbo object {} from set key {}".format(dbo_id, dbo_cls.dbo_set_key, self))

