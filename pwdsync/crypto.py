import base64
import hashlib
import string

import Cryptodome.Random
from Cryptodome.Random.random import choice as random_choice
from Cryptodome.Cipher import AES
from Cryptodome.Protocol.KDF import scrypt

from pwdsync.exceptions import WrongPasswordException

SALT_SIZE = 16
NONCE_SIZE = 16
MAC_TAG_SIZE = 16
KEY_LENGTH = 32

PASSWORD_ALPHABET = string.ascii_letters + string.digits + string.punctuation

def sha256(text):
    if isinstance(text, str):
        text = text.encode()
    return hashlib.sha256(text).digest()


def gen_pwd(length=20):
    password = ""
    for _ in range(length):
        password += random_choice(PASSWORD_ALPHABET)
    return password


def gen_key(pwd, salt):
    if isinstance(pwd, str):
        pwd = pwd.encode()
    return scrypt(pwd, salt, KEY_LENGTH, 524288, 8, 1)


def encrypt(text, pwd):
    salt = Cryptodome.Random.get_random_bytes(SALT_SIZE)
    key = gen_key(pwd, salt)
    cipher = AES.new(key, AES.MODE_EAX)

    ciphertext, tag = cipher.encrypt_and_digest(text.encode())
    return base64.b64encode(salt + cipher.nonce + tag + ciphertext).decode()


def decrypt(text, pwd):
    text = base64.b64decode(text)
    salt = text[:SALT_SIZE]
    text = text[SALT_SIZE:]

    nonce = text[:NONCE_SIZE]
    text = text[NONCE_SIZE:]

    tag = text[:MAC_TAG_SIZE]
    text = text[MAC_TAG_SIZE:]

    key = gen_key(pwd, salt)
    cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)

    try:
        decrypted = cipher.decrypt_and_verify(text, tag)
    except ValueError:
        raise WrongPasswordException()

    return decrypted.decode()
