import functools
import json
import os
import sys
import time

import pwdsync.crypto as crypto
import pwdsync.exceptions as exceptions
import pwdsync.utils as utils
from pwdsync.config import config


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


@functools.total_ordering
class HistoryEvent:
    def __init__(self, event, categories, name, time=None):
        self.event = event
        self.time = int(time.time()) if time is None else time
        self.categories = categories if isinstance(categories, str) else "/".join(categories)
        self.name = name

    def __lt__(self, other):
        if isinstance(other, HistoryEvent):
            return (self.time, hash(self)) < (other.time, hash(other))
        return self.time < other

    def __hash__(self):
        return hash(repr(self))

    def __eq__(self, other):
        if isinstance(other, HistoryEvent):
            return (self.time, hash(self)) == (other.time, hash(other))
        return NotImplemented

    def __repr__(self):
        return "<{} at {}: {}/{}>".format(self.event, self.time, self.categories, self.name)

    @staticmethod
    def from_json(dct):
        if dct["event"] == "ADD":
            return AddEvent(dct["categories"], dct["name"], dct["pwd"], dct["time"])
        elif dct["event"] == "EDIT":
            return EditEvent(dct["categories"], dct["name"], dct["key"], dct["value"], dct["time"])
        raise ValueError("Invalid json obj for HistoryEvent: " + repr(dct))


class AddEvent(HistoryEvent):
    def __init__(self, categories, name, pwd, time=None):
        super().__init__("ADD", time, categories, name)
        self.pwd = pwd

    def apply(self, storage):
        pwd = storage.get_pwds(*self.categories.split("/"), create=True)
        pwd[self.name] = self.pwd


class EditEvent(HistoryEvent):
    def __init__(self, categories, name, key, value, time=None):
        super().__init__("EDIT", time, categories, name)
        self.key = key
        self.value = value

    def apply(self, storage):
        pwd = storage.get_pwd(*self.categories.split("/"), self.name)
        setattr(pwd, self.key, self.value)

    def __repr__(self):
        return "<{} at {}: {}/{} - {}: {}>".format(self.event, self.time, self.categories, self.name, self.key, self.value)


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

    def save_data(self, filepath):
        if not self.pwd:
            raise Exception("No password")

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
        pwd = self.get_pwds(*pwd[:-1]).get(pwd[-1])
        if isinstance(pwd, Password):
            return pwd
        return None

    def get_pwds(self, *categories, create=False):
        pwds = self.passwords
        for key in categories:
            if key not in pwds or isinstance(pwds[key], Password):
                if create:
                    pwds[key] = {}
                else:
                    return {}
            pwds = pwds[key]
        return pwds

    def add_pwd(self, pwd, *categories):
        self.history.append(AddEvent(categories, pwd.name, pwd))
        self.get_pwds(*categories, create=True)[pwd.name] = pwd

    def edit_pwd(self, key, value, *pwd_path):
        pwd = self.get_pwd(*pwd_path)
        if not hasattr(pwd, key):
            raise KeyError("Invalid key")
        self.history.append(EditEvent(pwd_path[:-1], pwd.name, key, value))
        setattr(pwd, key, value)

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
