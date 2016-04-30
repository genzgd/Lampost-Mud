from lampost.context import resource, scripts, config
from lampost.datastore.redisstore import RedisStore
from lampost.gameops import dbconfig
from lampost.util.logging import LogFactory

resource.m_requires(__name__, 'log')


def _prepare():
    resource.register('log', LogFactory())
    scripts.select_json()


def reset_config(args):
    _prepare()
    datastore = resource.register('datastore', RedisStore(args.db_host, args.db_port, args.db_num, args.db_pw), True)
    config_id = args.config_id
    existing = datastore.load_object(config_id, dbconfig.Config)
    if not existing:
        print("Existing configuration does not exist, try lampost_setup")
        return
    datastore.delete_object(existing)

    try:
        config_yaml = config.load_yaml(args.config_dir)
        if not config_yaml:
            print("No yaml found.  Confirm config/working directory?")
            return
        db_config = dbconfig.create(config_id, config_yaml, True)
    except Exception as exp:
        exception("Failed to create configuration from yaml")
        datastore.save_object(existing)
        print("Exception creating configuration from yaml.")
        return
    config.activate(db_config.section_values)
    print('Config {} successfully reloaded from yaml files'.format(config_id))
