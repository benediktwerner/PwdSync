import atexit
from threading import Timer

import pwdsync.crypto as crypto
import pwdsync.exceptions as exceptions
from pwdsync.config import config

try:
    import pyperclip
    HAS_PYPERCLIP = True
except ImportError:
    HAS_PYPERCLIP = False


cliphash = None
timer = None


@atexit.register
def clear_clipboard():
    global cliphash
    if cliphash is not None and crypto.sha256(pyperclip.paste()) == cliphash:
        pyperclip.copy("")
        cliphash = None


def copy(pwd):
    global cliphash, timer
    if not HAS_PYPERCLIP:
        raise exceptions.NoClipboardException()

    pyperclip.copy(pwd)
    cliphash = crypto.sha256(pwd)
    timer = Timer(config.clipboard_timeout, clear_clipboard)
    timer.daemon = True
    timer.start()
