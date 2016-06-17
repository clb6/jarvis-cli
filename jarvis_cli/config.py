import os
import configparser
from jarvis_cli.exceptions import JarvisCliConfigError
from jarvis_cli.client import DBConn

JARVIS_CLI_DIRECTORY = os.path.join(os.environ["HOME"], ".jarvis")


def _get_config(environment):
    config = configparser.ConfigParser()
    config_path = os.path.join(JARVIS_CLI_DIRECTORY, "cli_config.ini")

    if config.read(config_path):
        return config[environment]
    else:
        raise JarvisCliConfigError("Configuration not setup: {0}".format(config_path))

def get_client_connection(environment):
    config = _get_config(environment)
    return DBConn(config["host"], config["port"])

def get_jarvis_data_directory(environment):
    config = _get_config(environment)
    return config["data_directory"]

def get_jarvis_snapshots_directory(environment):
    config = _get_config(environment)
    return config["snapshots_directory"]

def get_author(environment):
    config = _get_config(environment)
    return config["author"]
