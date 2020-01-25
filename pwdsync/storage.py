import json
import os
import sys
import time

import pwdsync.crypto as crypto
import pwdsync.exceptions as exceptions
import pwdsync.utils as utils
from pwdsync.config import config
from pwdsync.history_events import HistoryEvent, AddEvent, EditEvent


def load_encrypted_data(path=None):
    if not path:
        path = utils.get_pwdsync_file(config.password_file_path)
    if not os.path.isfile(path):
        return None
    with open(path) as f:
        return f.read()


def json_object_hook(dct):
    if "password" in dct:
        return Password.from_json(dct)
    elif "event" in dct:
        return HistoryEvent.from_json(dct)
    return dct


class PwdJsonEncoder(json.JSONEncoder):
    # pylint: disable=E0202
    def default(self, obj):
        if isinstance(obj, Password) or isinstance(obj, HistoryEvent):
            return obj.__dict__
        return json.JSONEncoder.default(self, obj)


def from_json(data):
    return json.loads(data, object_hook=json_object_hook)


def to_json(data):
    return json.dumps(data, cls=PwdJsonEncoder)


class Password:
    def __init__(self, name, username, password, password2=None, comment=None):
        self.name = name
        self.username = username
        self.password = password
        self.password2 = password2
        self.comment = comment

    @staticmethod
    def from_json(json_obj):
        for key in ("name", "username", "password"):
            if key not in json_obj:
                raise ValueError("{} not specified".format(key))

        return Password(
            json_obj["name"],
            json_obj["username"],
            json_obj["password"],
            json_obj.get("password2", None),
            json_obj.get("comment", None))

    def __str__(self):
        return "{}\t\t{}".format(self.name, self.username)


class Storage:
    def __init__(self):
        self.pwd = None
        self.history = []
        self.passwords = {}

    def save_data(self, filepath=None):
        if not self.pwd:
            raise exceptions.PwdSyncException("Failed to save data: No password")

        if not filepath:
            filepath = utils.get_pwdsync_file(config.password_file_path)

        data = {
            "history": self.history,
            "passwords": self.passwords
        }
        encrypted = crypto.encrypt(to_json(data), self.pwd)
        with open(filepath, "w") as f:
            f.write(encrypted)

    def load_data(self, pwd, path=None):
        self.pwd = crypto.sha256(pwd)
        encrypted = load_encrypted_data(path)
        if encrypted:
            decrypted = crypto.decrypt(encrypted, self.pwd)
            data = from_json(decrypted)
        elif not path and config.test:
            with open("test_data.json") as f:
                data = json.load(f, object_hook=json_object_hook)
        else:
            return
        self.history = data["history"]
        self.passwords = data["passwords"]

    def get_pwd(self, *pwd):
        pwd = self.get_category(*pwd[:-1]).get(pwd[-1])
        if isinstance(pwd, Password):
            return pwd
        return None

    def get_category(self, *categories, create=False):
        category = self.passwords
        for key in categories:
            if key not in category:
                if create:
                    category[key] = {}
                else:
                    return None
            elif isinstance(category[key], Password):
                raise exceptions.PwdSyncException("Category is a Password")
            category = category[key]
        return category

    def add_pwd(self, pwd, *categories):
        event = AddEvent(categories, pwd.name, pwd)
        self.history.append(event)
        event.apply(self)

    def edit_pwd(self, key, value, *pwd_path):
        pwd = self.get_pwd(*pwd_path)
        if not hasattr(pwd, key):
            raise KeyError("Invalid key")

        event = EditEvent(pwd_path[:-1], pwd.name, key, value)
        self.history.append(event)
        event.apply(self)

    def merge(self, other):
        self.__merge_history(other.history)
        self.__build_from_history()

    def __merge_history(self, history):
        self.history = list(sorted(set(self.history + history)))

    def __build_from_history(self):
        self.passwords = {}
        for event in self.history:
            event.apply(self)


storage = Storage()
