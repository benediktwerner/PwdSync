import json
import os
import sys

import pwdsync.crypto as crypto
import pwdsync.exceptions as exceptions
import pwdsync.utils as utils
from pwdsync.config import config


def load_encrypted_data():
    path = utils.get_pwdsync_file(config.password_file_path)
    if not os.path.isfile(path):
        return None
    with open(path) as f:
        return f.read()


def json_object_hook(dct):
    if "password" in dct:
        return Password(dct)
    return dct


class PwdJsonEncoder(json.JSONEncoder):
    # pylint: disable=E0202
    def default(self, obj):
        if isinstance(obj, Password):
            return obj.__dict__
        return json.JSONEncoder.default(self, obj)


def from_json(data):
    return json.loads(data, object_hook=json_object_hook)


def to_json(data):
    return json.dumps(data, cls=PwdJsonEncoder)


class Password:
    def __init__(self, json_obj):
        for key in ("name", "username", "password"):
            if key not in json_obj:
                raise ValueError("{} not specified".format(key))

        self.name = json_obj["name"]
        self.username = json_obj["username"]
        self.password = json_obj["password"]
        self.password2 = json_obj.get("password2", None)
        self.comment = json_obj.get("comment", None)

    def __str__(self):
        return "{}\t\t{}".format(self.name, self.username)


class Storage:
    def __init__(self):
        self.pwd = None
        self.data = None

    def save_data(self, filepath):
        if not self.pwd:
            raise Exception("No password")

        encrypted = crypto.encrypt(to_json(self.data), self.pwd)
        with open(filepath, "w") as f:
            f.write(encrypted)

    def load_data(self, pwd):
        self.pwd = crypto.sha256(pwd)
        encrypted = load_encrypted_data()
        if encrypted:
            decrypted = crypto.decrypt(encrypted, self.pwd)
            self.data = from_json(decrypted)
        elif config.test:
            with open("test_data.json") as f:
                self.data = json.load(f, object_hook=json_object_hook)
        else:
            self.data = {
                "history": [],
                "passwords": {}
            }

    def get_pwd(self, *pwd):
        pwd = self.get_pwds(*pwd[:-1]).get(pwd[-1])
        if isinstance(pwd, Password):
            return pwd
        return None

    def get_pwds(self, *categories):
        pwds = self.data["passwords"]
        for key in categories:
            if key not in pwds or isinstance(pwds[key], Password):
                return {}
            pwds = pwds[key]
        return pwds


storage = Storage()
