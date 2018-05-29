import pwdsync.utils


class PwdSyncException(Exception):
    pass


class WrongPasswordException(PwdSyncException):
    pass


class NoClipboardException(PwdSyncException):
    pass


class UnsupportedOSException(PwdSyncException):
    def __init__(self):
        super().__init__("{} is currently not supported by PwdSync".format(pwdsync.utils.get_os()))
