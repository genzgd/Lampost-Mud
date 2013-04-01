import hashlib

from os import urandom
from base64 import b64encode, b64decode
from itertools import izip
from lampost.util.pdkdf2 import pbkdf2_bin

SALT_LENGTH = 8
KEY_LENGTH = 20
COST_FACTOR = 800


def make_hash(password):
    if isinstance(password, unicode):
        password = password.encode('utf-8')
    salt = b64encode(urandom(SALT_LENGTH))
    return '{}${}'.format(
        salt,
        b64encode(pbkdf2_bin(password, salt, COST_FACTOR, KEY_LENGTH)))


def check_password(password, full_hash):
    if isinstance(password, unicode):
        password = password.encode('utf-8')
    salt, existing_hash = full_hash.split('$')
    existing_hash = b64decode(existing_hash)
    entered_hash = pbkdf2_bin(password, salt, COST_FACTOR, KEY_LENGTH)
    diff = 0
    for char_a, char_b in izip(existing_hash, entered_hash):
        diff |= ord(char_a) ^ ord(char_b)
    return diff == 0









