from importlib import import_module

from lampost.context import resource, scripts, config
from lampost.datastore.redisstore import RedisStore
from lampost.gameops import dbconfig, event, permissions
from lampost.util.logging import LogFactory
from lampost.server.user import UserManager


resource.m_requires(__name__, 'log')


def new_setup(args):

    resource.register('log', LogFactory())
    scripts.select_json()

    # Initialize the database, flush if requested
    datastore = resource.register('datastore', RedisStore(args.db_host, args.db_port, args.db_num, args.db_pw), True)
    if args.flush:
        db_num = datastore.pool.connection_kwargs['db']
        if db_num == args.db_num:
            warn("Flushing database {}", db_num)
            datastore.redis.flushdb()
        else:
            print("Error:  DB Numbers do not match")
            return

    db_config = datastore.load_object(args.config_id, 'config')
    if db_config:
        print("Error:  This instance is already set up")
        return

    # Load config yaml files and create the database configuration
    config_yaml = config.load_yaml(args.config_dir)
    db_config = dbconfig.create(args.config_id, config_yaml, True)
    config_values = config.activate(db_config.section_values)

    # Initialize core services needed by the reset of the setup process
    resource.register('dispatcher', event, True)
    perm = resource.register('perm', permissions, True)
    perm._post_init()

    app_setup = import_module('{}.setup'.format(args.app_id))
    first_player = app_setup.first_time_setup(args, datastore, config_values)

    user_manager = UserManager()
    user = user_manager.create_user(args.imm_account, args.imm_password)
    player = user_manager.attach_player(user, first_player)
    perm.update_immortal_list(player)
