from os import urandom
from base64 import b64encode, b64decode

from lampost.util.pdkdf2 import pbkdf2_bin

SALT_LENGTH = 8
KEY_LENGTH = 20
COST_FACTOR = 800


def make_hash(password):
    salt = bytes(urandom(SALT_LENGTH))
    password_hash = pbkdf2_bin(bytes(password, 'utf-8'), salt, COST_FACTOR, KEY_LENGTH)
    return '{}${}'.format(
        b64encode(salt).decode(),
        b64encode(password_hash).decode())


def check_password(existing_hash, password, salt=None):
    if isinstance(existing_hash, str):
        salt, existing_hash = tuple(b64decode(bytes(element, 'utf-8')) for element in existing_hash.split('$'))
    entered_hash = pbkdf2_bin(bytes(password, 'utf-8'), salt, COST_FACTOR, KEY_LENGTH)
    diff = 0
    for byte_a, byte_b in zip(existing_hash, entered_hash):
        diff |= byte_a ^ byte_b
    return diff == 0