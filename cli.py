#!/usr/bin/env python3

import traceback

import pwdsync.crypto as crypto
import pwdsync.utils as utils
import pwdsync.clipboard as clipboard
import pwdsync.exceptions as exceptions
import pwdsync.terminal as terminal
from pwdsync.config import config
from pwdsync.storage import Password, storage, Storage


def load_data():
    terminal.ask_pwd(storage.load_data)


def save_data():
    storage.save_data()
    terminal.success("Passwords saved")


def flash_pwd(*pwd):
    pwd = storage.get_pwd(*pwd)
    if pwd is None:
        terminal.error("No such password")
    else:
        terminal.flash(pwd.password)


def list_passwords(*categories):
    pwds = storage.get_category(*categories)
    print_recursively(pwds)


def print_recursively(data, indentation=0):
    for key in sorted(data.keys()):
        value = data[key]
        if isinstance(value, Password):
            terminal.respond(" " * indentation + str(value))
        elif isinstance(value, dict):
            terminal.respond(" " * indentation + key)
            print_recursively(value, indentation + 2)
            print()
        else:
            raise ValueError("Invalid data type in pwd dict: " + type(value))


def copy_pwd(*pwd):
    try:
        pwd = storage.get_pwd(*pwd)
        if not pwd:
            return terminal.error("No such password")
        clipboard.copy(pwd.password)
        terminal.success("Copyed to clipboard")
    except KeyError:
        terminal.error("No such password")
    except exceptions.NoClipboardException:
        terminal.error("Copying to clipboard is not supported. Have you installed **pyperclip**?")


def add_pwd():
    name = terminal.ask("Name:")
    categories = terminal.ask("Categories:").split(" ")
    pwd_id = categories + [name]
    if storage.get_pwd(*pwd_id):
        terminal.error("A password with the same name and category already exists!")
        return

    username = terminal.ask("Username:")
    password = terminal.ask("Password:")
    password2 = terminal.ask("Password2:")
    comment = terminal.ask("Comment:")

    if not password:
        password = crypto.gen_pwd()
    if not password2:
        password2 = None
    if not comment:
        comment = None
    pwd = Password(name, username, password, password2, comment)
    storage.add_pwd(pwd, *categories)

    print()
    if terminal.ask_yes_no("Do you want to save?"):
        save_data()


def show_pwd(*pwd):
    pwd = storage.get_pwd(*pwd)
    terminal.respond(pwd.name)
    terminal.respond("Username: {}".format(pwd.username))
    terminal.respond("Password: [hidden]")
    if pwd.password2:
        terminal.respond("Password2: [hidden]")
    terminal.respond("Comment: {}".format(pwd.comment))


def edit_pwd(*pwd_path):
    show_pwd(*pwd_path)
    changes = False

    while True:
        print()
        key = terminal.ask("Which field do you want to edit? (Press Enter to exit)")
        if not key:
            break

        if key.startswith("password"):
            value = terminal.get_pass("Enter new " + key + ":")
        else:
            value = terminal.ask("Enter new " + key + ":")

        try:
            storage.edit_pwd(key, value, *pwd_path)
            changes = True

            if key.startswith("password"):
                if not value:
                    terminal.success("Removed " + key)
                else:
                    terminal.success("Changed " + key)
            else:
                terminal.success("Changed **{}** to '**{}**'".format(key, value))
        except KeyError:
            terminal.error("Invalid field name: **{}**".format(key))

    if changes and terminal.ask_yes_no("Do you want to save?"):
        save_data()


def merge(path):
    to_merge = Storage()
    terminal.ask_pwd(lambda pwd: to_merge.load_data(pwd, path))
    storage.merge(to_merge)


class CommandParser:
    def __init__(self):
        self.commands = {}
        self.add_command(
            ["h", "help", "?"],
            "Show this help",
            self.show_help
        )

    def add_command(self, names, description, fun=None, args=()):
        if isinstance(args, str):
            args = args.split(" ")
        if isinstance(names, str):
            names = [names]
        min_count, max_count = self.get_min_max(args)

        data = [description, args, names, fun, min_count, max_count]
        for name in names:
            self.commands[name] = data

    def get_min_max(self, args):
        min_count = 0
        max_count = 0
        for arg in args:
            if arg[0] == "[" and arg[-1] == "]":
                if arg[1] == "*":
                    min_count = 0
                    max_count = float("inf")
                    break
                max_count += 1
            elif arg[0] == "*":
                min_count = 1
                max_count = float("inf")
                break
            else:
                min_count += 1
                max_count += 1
        return min_count, max_count

    def show_help(self):
        terminal.respond("Available commands:\n")

        commands = {}
        max_len = 0
        for cmd in self.commands:
            description, args, aliases, fun, *_ = self.commands[cmd]
            if cmd != aliases[0]:
                continue

            if fun is None:
                description += " **(Not yet implemented!)**"

            cmd_str = ", ".join(" ".join([name] + list(args)) for name in aliases)
            max_len = max(len(cmd_str), max_len)
            commands[cmd] = (cmd_str, description)

        fmt_str = "{:" + str(max_len + 4) + "}{}"
        for cmd in sorted(commands):
            cmd_str, description = commands[cmd]
            terminal.respond(fmt_str.format(cmd_str, description))

    def parse_command(self, cmd):
        if cmd == "":
            return
        print()

        action, *args = cmd.split(" ")
        command = None
        if action in self.commands:
            command = action
        else:
            possible_commands = tuple(filter(lambda c: c.startswith(cmd), self.commands))
            if len(possible_commands) == 1:
                command = possible_commands[0]
            elif len(possible_commands) > 1:
                terminal.error("Multiple possible commands: {white}" + ", ".join(possible_commands))
            else:
                terminal.error("Invalid command: **{}**. Use **help** to see all available commands.".format(repr(cmd)))

        if command is None:
            print()
            return

        *_, fun, min_count, max_count = self.commands[command]
        if fun is None:
            terminal.error("**{}** is not yet implemented".format(command))
        elif min_count <= len(args) <= max_count:
            fun(*args)
        elif max_count == float("inf"):
            terminal.error("**{}** expects at least 1 argument but got {}.".format(command, len(args)))
        elif min_count == max_count:
            terminal.error("**{}** expects exactly {} arguments but got {}.".format(command, min_count, len(args)))
        else:
            terminal.error("**{}** expects between {} and {} arguments but got {}.".format(command,
                                                                                           min_count, max_count, len(args)))
        print()


def main():
    terminal.logo()
    load_data()

    parser = CommandParser()
    parser.add_command("save", "Save the passwords to file", save_data)
    parser.add_command("sync", "Sync passwords to server")
    parser.add_command("merge", "Merge another pwd database", merge, "FILE")
    parser.add_command(["pwd", "flash"], "Show the password", flash_pwd, "*PWD")
    parser.add_command("show", "Show the password metadata", show_pwd, "*PWD")
    parser.add_command("list", "List all passwords. Optionally filter by category", list_passwords, "[*CATEGORIES]")
    parser.add_command("copy", "Copy the password to clipboard", copy_pwd, "*PWD")
    parser.add_command("add", "Add a new password", add_pwd)
    parser.add_command("edit", "Edit an existing password", edit_pwd, "*PWD")
    parser.add_command(
        ["search", "grep"],
        "Search the password database",
        args="KEYWORD"
    )
    parser.add_command("history", "Show the history of password changes")
    parser.add_command(
        ["q", "quit", "exit", "end"],
        "Quit PwdSync",
        terminal.goodbye
    )

    while True:
        command = terminal.ask("What do you want to do?")
        if command is None:
            terminal.goodbye()
        try:
            parser.parse_command(command)
        except Exception as e:
            print()
            terminal.error("Error: " + str(e))
            if config.test or config.show_tracebacks:
                print()
                traceback.print_exc()
            else:
                terminal.respond("For more details enable **show_tracebacks** in the config.")
            print()


if __name__ == "__main__":
    main()
