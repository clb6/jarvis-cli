import os
from collections import namedtuple
from jarvis_cli import config
from jarvis_cli.exceptions import JarvisPromptError


def _prompt_config_value(config_map, title, set_func, default):
    while True:
        answer = input("{0} [{1}]: ".format(title, default)) or default

        if "directory" in title and not os.path.exists(answer):
            raise JarvisPromptError("Directory {0} does not exist".format(answer))

        try:
            set_func(config_map, answer)
            break
        except TypeError as e:
            print("Not a valid value. Try again.")

def prompt_init_config(environment, config_path):
    ConfigParam = namedtuple("ConfigParam", ["title", "set_func", "default"])
    config_params = [
            ConfigParam("Your name", config.set_author, os.getlogin()),
            ConfigParam("Jarvis API hostname", config.set_host, "localhost"),
            ConfigParam("Jarvis API port", config.set_port, 3000),
            ConfigParam("Jarvis API data directory",
                config.set_jarvis_data_directory, "/opt/jarvis"),
            ConfigParam("Jarvis API snapshots directory",
                config.set_jarvis_snapshots_directory,
                config.JARVIS_CLI_DEFAULT_SNAPSHOTS_DIR) ]

    with config.create_config(environment, config_path) as config_map:
        for cp in config_params:
            _prompt_config_value(config_map, cp.title, cp.set_func, cp.default)
