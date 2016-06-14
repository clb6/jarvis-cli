import os
import configparser
from jarvis_cli.exceptions import JarvisCliConfigError
from jarvis_cli.client import DBConn


def get_client_connection(environment):
    config = configparser.ConfigParser()
    config_path = os.path.join(os.environ["HOME"], ".jarvis", "cli_config.ini")

    if config.read(config_path):
        return DBConn(config[environment]["host"], config[environment]["port"])
    else:
        raise JarvisCliConfigError("Configuration not setup: {0}".format(config_path))

