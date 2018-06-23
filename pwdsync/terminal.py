import colorama
import re
import select
import sys
import time
from getpass import getpass

import pwdsync.utils as utils
from pwdsync.config import config


ASK_INDENTATION = 1
RESPONSE_INDENTATION = 3

COLORS = {
    "black": '\033[30m',
    "red": '\033[31m',
    "green": '\033[32m',
    "yellow": '\033[33m',
    "blue": '\033[34m',
    "purple": '\033[35m',
    "cyan": '\033[36m',
    "lightgray": '\033[37m',

    "darkgray": '\033[90m',
    "lightred": '\033[91m',
    "lightgreen": '\033[92m',
    "lightyellow": '\033[93m',
    "orange": '\033[93m',
    "lightblue": '\033[94m',
    "lightpurble": '\033[95m',
    "pink": '\033[95m',
    "lightcyan": '\033[96m',
    "white": '\033[97m',

    "endc": '\033[0m',
    "bold": '\033[1m',
    "underline": '\033[4m'
}


def colorize(text, color=None):
    if color:
        text = "{" + color + "}" + text + "{endc}"
    return text.format(**COLORS)


#                        .$$$$$"
#                       z$$$$$"
#       ____           z$$$$$_____
#      / __ \_      __d$$$/ / ___/__  ______  _____
#     / /_/ / | /| / / __  /\__ \/ / / / __ \/ ___/
#    / ____/| |/ |/ / /_/ /$$_/ / /_/ / / / / /__
#   /_/     |__/|__/\____//____/\__  /_/ /_/\___/
#                       4$P"   /____/
#                      z$"
#                     z"
def logo():
    logo_string = r"""
                       {yellow}.$$$$$"{endc}
                      {yellow}z$$$$$"{endc}
      ____           {yellow}z$$${underline}$${endc}_____
     / __ \_      __{yellow}d{underline}$$${endc}/ / ___/__  ______  _____
    / /_/ / | /| / / __  /\__ \/ / / / __ \/ ___/
   / ____/| |/ |/ / /_/ /{yellow}{underline}$$${endc}/ / /_/ / / / / /__
  /_/     |__/|__/\____//____/\__  /_/ /_/\___/
                      {yellow}4$P"{endc}   /____/
                     {yellow}z$"{endc}
                    {yellow}z"{endc}
"""
    print(colorize(logo_string))


def erase_lines(count=1):
    print("\r\033[1A\033[2K" * (count - 1) + "\033[2K\r", end="")


def goodbye():
    respond("Goodbye!\n", "yellow")
    exit(0)


def ask(text):
    try:
        # color codes don't work with input on windows
        print(" " * ASK_INDENTATION + colorize("{blue}" + text.strip() + " {yellow}"), end="", flush=True)
        tmp = input()
        print(colorize("{endc}"), end="")
        return tmp
    except (EOFError, KeyboardInterrupt):
        try:
            print(colorize("{endc}\n"))
            goodbye()
        except KeyboardInterrupt:
            goodbye()


def ask_pwd(text="Enter password:"):
    try:
        # color codes don't work with input on windows
        print(" " * RESPONSE_INDENTATION + colorize("{orange}" + text.strip() + " {yellow}"), end="", flush=True)
        pwd = getpass("")
        erase_lines(2)
        print(colorize("{endc}"), end="")
        return pwd
    except (EOFError, KeyboardInterrupt):
        erase_lines()
        goodbye()


def highlightify(text, color="blue", end_color="endc"):
    return re.sub(r"\*\*(.*?)\*\*", r"{{{}}}\1{{{}}}".format(color, end_color), text)


def error(text):
    respond(text, "red", "purple")


def success(text):
    respond(text, "green")


def respond(text, color="white", highlight_color="blue"):
    text = highlightify(text, highlight_color, color)
    text = colorize(text, color)
    print(" " * RESPONSE_INDENTATION + text)


def flash(text):
    print(" " * RESPONSE_INDENTATION + text, end="", flush=True)
    if utils.is_windows():
        input()
        erase_lines(2)
    else:
        i, *_ = select.select([sys.stdin], [], [], config.password_show_time)
        if i:
            input()
            erase_lines(2)
        erase_lines()


colorama.init()
