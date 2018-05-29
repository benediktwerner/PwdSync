import os
import sys
import yaml

import pwdsync.utils as utils


CONFIG_FILE_NAME = "config.yml"
CONFIG_DEFAULTS = {
    "password_file_path": "$pwdsync/passwords",
    "lock_timeout": 60,
    "clipboard_timeout": 30,
    "password_show_time": 5,
    "test": False,
    "show_tracebacks": False
}


def load_config():
    config = CONFIG_DEFAULTS
    path = utils.get_pwdsync_file(CONFIG_FILE_NAME)
    if os.path.isfile(path):
        with open(path) as f:
            config.update(yaml.load(f))
    else:
        with open(path, "w") as f:
            yaml.dump(config, f, default_flow_style=False)
    return resolve_path_vars(config)


def resolve_path_vars(config):
    for key, value in config.items():
        if isinstance(value, str):
            config[key] = value.replace("$pwdsync", utils.get_pwdsync_dir())
        elif isinstance(value, dict):
            resolve_path_vars(value)
    return config


class Config:
    def __init__(self):
        self.config = load_config()

    def __getattr__(self, name):
        return self.config[name]

    def __getitem__(self, name):
        return self.config[name]


config = Config()
