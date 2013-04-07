from lampost.client.user import User
from lampost.context.resource import m_requires
from lampost.datastore.dbutil import build_indexes
from lampost.setup.scripts import build_default_displays
from base64 import b64decode
from lampost.util.encrypt import make_hash

m_requires('log', 'config_manager', 'datastore', __name__)


def displays():
    config_manager.config.default_displays = build_default_displays()
    config_manager.save_config()


def passwords():
    for user_id in fetch_set_keys('users'):
        user = load_object(User, user_id.split(':')[1])
        if not user:
            error('Missing user id {}'.format(user_id))
            continue
        if not user.password:
            user.password = make_hash('password')
            save_object(user)
            info('Created default password for {}'.format(user_id))
            continue
        try:
            salt, password_hash = user.password.split('$')
            b64decode(salt)
            b64decode(password_hash)
            info('Password for {} appears to be hashed'.format(user_id))
            continue
        except:
            info('Hashing password for {}'.format(user_id))
            user.password = make_hash(user.password)
            save_object(user)


def user_indexes():
    datastore.redis.delete("user_name_index")
    build_indexes(User)


def player_age():
    for player_id in fetch_set_keys('players'):
        player = load_object(Player, player_id)
        if not player:
            error('Missing player id {}'.format(player_id))






