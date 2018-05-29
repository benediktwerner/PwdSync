#!/usr/bin/env python3

import pwdsync.terminal as terminal
import pwdsync.utils as utils
import pwdsync.exceptions as exceptions
from pwdsync.config import config
from pwdsync.storage import Password, storage


def load_data():
    while True:
        pwd = terminal.ask_pwd()
        try:
            storage.load_data(pwd)
            break
        except exceptions.WrongPasswordException:
            terminal.error("Wrong password. Try again.")


def save_data():
    filepath = utils.get_pwdsync_file(config.password_file_path)
    storage.save_data(filepath)
    terminal.success("Saved passwords to **{}**".format(filepath))


def show_pwd(*pwd):
    pwd = storage.get_pwd(*pwd)
    if pwd is None:
        terminal.error("No such password")
    else:
        terminal.flash(pwd.password)


def list_passwords(*categories):
    pwds = storage.get_pwds(*categories)
    print_recursively(pwds)


def print_recursively(data, indentation=0):
    for key in sorted(data.keys()):
        value = data[key]
        if isinstance(value, Password):
            terminal.respond(" " * indentation + str(value))
        elif isinstance(value, dict):
            terminal.respond(" " * indentation + key)
            print_recursively(value, indentation + 4)
            print()
        else:
            raise ValueError("Invalid data type in pwd dict: " + type(value))


def copy_pwd(*pwd):
    try:
        storage.to_clipboard(*pwd)
        terminal.success("Copyed to clipboard")
    except KeyError:
        terminal.error("No such password")
    except exceptions.NoClipboardException:
        terminal.error("Copying to clipboard is not supported")


def show_help():
    terminal.error("Help is not yet implemented!")


def main():
    terminal.ascii_art()
    load_data()

    while True:
        command = terminal.ask("What do you want to do?")
        action, *args = command.split(" ")

        # TODO: Real command parser that checks args
        if action == "save":
            save_data()
        elif action == "sync":
            pass
        elif action == "show":
            show_pwd(*args)
        elif action == "list":
            list_passwords(*args)
        elif action == "copy":
            copy_pwd(*args)
        elif action in ("search", "grep"):
            pass
        elif action == "history":
            pass
        elif action in ("h", "help", "?"):
            show_help()
        elif action in ("q", "quit", "exit", "end"):
            terminal.goodbye()
        else:
            terminal.error("Invalid command: **{}**. Use **help** to see all available commands.".format(repr(command)))

        print()


if __name__ == "__main__":
    main()
