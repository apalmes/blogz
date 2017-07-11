import hashlib
import random
import string


def make_salt():
    return ''.join([random.choice(string.ascii_letters) for x in range(5)])


def make_pw_hash(password, salt=None):
    if not salt:
        salt = make_salt()
    hashed = hashlib.sha256(str.encode(password + salt)).hexdigest()
    return '{0},{1}'.format(hashed, salt)


def check_pw_hash(password, hashed):
    salt = hashed.split(',')[1]
    if make_pw_hash(password, salt) == hashed:
        return True

    return False
