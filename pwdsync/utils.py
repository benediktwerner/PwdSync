import os
import platform
from pathlib import Path

import pwdsync.exceptions as exceptions
from pwdsync.cache import cached


@cached
def get_os():
    return platform.system()


@cached
def get_user_home():
    return os.path.expanduser("~")


@cached
def get_pwdsync_dir():
    os_name = get_os()
    if os_name == "Windows":
        path = os.path.join(get_user_home(), "Documents", "pwdsync")
    elif os_name == "Linux":
        path = os.path.join(get_user_home(), ".pwdsync")
    else:
        raise exceptions.UnsupportedOSException()

    if not os.path.isdir(path):
        os.makedirs(path, exist_ok=True)
    return path


def get_pwdsync_file(*path, create=False):
    filepath = os.path.join(get_pwdsync_dir(), *path)
    if create and not os.path.isfile(filepath):
        Path(filepath).touch()
    return filepath
