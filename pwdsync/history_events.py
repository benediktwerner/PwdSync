import functools

from pwdsync.storage import Password, Storage


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
            return AddEvent(dct["categories"], dct["name"], Password.from_json(dct["pwd"]), dct["time"])
        elif dct["event"] == "EDIT":
            return EditEvent(dct["categories"], dct["name"], dct["key"], dct["value"], dct["time"])
        raise ValueError("Invalid json obj for HistoryEvent: " + repr(dct))


class AddEvent(HistoryEvent):
    def __init__(self, categories, name, pwd, time=None):
        super().__init__("ADD", time, categories, name)
        self.pwd = pwd

    def apply(self, storage: Storage):
        category = storage.get_category(*self.categories.split("/"), create=True)
        category[self.name] = self.pwd


class EditEvent(HistoryEvent):
    def __init__(self, categories, name, key, value, time=None):
        super().__init__("EDIT", time, categories, name)
        self.key = key
        self.value = value

    def apply(self, storage: Storage):
        pwd = storage.get_pwd(*self.categories.split("/"), self.name)
        setattr(pwd, self.key, self.value)

    def __repr__(self):
        return "<{} at {}: {}/{} - {}: {}>".format(self.event, self.time, self.categories, self.name, self.key, self.value)
