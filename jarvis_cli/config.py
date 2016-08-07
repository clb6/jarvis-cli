import os
from functools import partial
import configparser
from contextlib import contextmanager
from jarvis_cli.exceptions import JarvisCliConfigError
from jarvis_cli.client import DBConn

JARVIS_CLI_CONFIG_PATH = os.path.join(os.environ["HOME"], ".jarvis", "cli_config.ini")


@contextmanager
def create_config(environment, config_path):
    config = configparser.ConfigParser()
    config.add_section(environment)

    yield config[environment]

    with open(config_path, 'w') as f:
        config.write(f)

def get_config_map(environment, config_path):
    config = configparser.ConfigParser()

    if config.read(config_path):
        return config[environment]
    else:
        raise JarvisCliConfigError("Configuration not setup: {0}".format(config_path))

def _get_config_param(key, config_map):
    return config_map[key]

get_host = partial(_get_config_param, "host")
get_port = partial(_get_config_param, "port")
get_jarvis_data_directory = partial(_get_config_param, "data_directory")
get_jarvis_snapshots_directory = partial(_get_config_param, "snapshots_directory")
get_author = partial(_get_config_param, "author")

def get_client_connection(config_map):
    host = get_host(config_map)
    port = get_port(config_map)
    return DBConn(host, port)

def _set_config_param(key, config_map, value):
    config_map[key] = value

set_host = partial(_set_config_param, "host")
set_port = partial(_set_config_param, "port")
set_jarvis_data_directory = partial(_set_config_param, "data_directory")
set_jarvis_snapshots_directory = partial(_set_config_param, "snapshots_directory")
set_author = partial(_set_config_param, "author")
