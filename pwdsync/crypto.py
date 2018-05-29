import base64
import hashlib

import Cryptodome.Random
from Cryptodome.Cipher import AES

from pwdsync.exceptions import WrongPasswordException

SALT_SIZE = 16
KEY_GEN_ITERATIONS = 20
AES_MULTIPLE = 16
DATA_PREFIX = "[ENCRYPTED_PWDSYNC_DATA]"


def sha256(text):
    if isinstance(text, str):
        text = text.encode()
    return hashlib.sha256(text).digest()


def gen_key(pwd, salt):
    if isinstance(pwd, str):
        pwd = pwd.encode()
    key = pwd + salt
    for _ in range(KEY_GEN_ITERATIONS):
        key = sha256(key)
    return key


def pad(text):
    to_pad = AES_MULTIPLE - (len(text) % AES_MULTIPLE)
    return text + to_pad * chr(to_pad)


def unpad(text):
    pad = ord(text[-1])
    return text[:-pad]


def encrypt(text, pwd):
    text = DATA_PREFIX + text
    salt = Cryptodome.Random.get_random_bytes(SALT_SIZE)
    cipher = AES.new(gen_key(pwd, salt), AES.MODE_ECB)
    ciphertext = cipher.encrypt(pad(text).encode())
    return base64.b64encode(salt + ciphertext).decode()


def decrypt(text, pwd):
    text = base64.b64decode(text)
    salt = text[0:SALT_SIZE]
    cipher = AES.new(gen_key(pwd, salt), AES.MODE_ECB)
    decrypted = cipher.decrypt(text[SALT_SIZE:])
    if not decrypted.startswith(DATA_PREFIX.encode()):
        raise WrongPasswordException()
    decrypted = decrypted[len(DATA_PREFIX):]
    return unpad(decrypted.decode())
