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
            ConfigParam("Jarvis api url", config.set_api_url, "http://localhost"),
            ConfigParam("Jarvis api username", config.set_api_user, ""),
            ConfigParam("Jarvis api password", config.set_api_password, ""),
            ConfigParam("Jarvis api data directory",
                config.set_jarvis_data_directory, "/opt/jarvis"),
            ConfigParam("Jarvis API snapshots directory",
                config.set_jarvis_snapshots_directory,
                config.JARVIS_CLI_DEFAULT_SNAPSHOTS_DIR) ]

    with config.create_config(environment, config_path) as config_map:
        for cp in config_params:
            _prompt_config_value(config_map, cp.title, cp.set_func, cp.default)
