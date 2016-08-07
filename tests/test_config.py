from collections import namedtuple
import pytest
from jarvis_cli import config as jc

def test_config_use(tmpdir):
    home_dir = tmpdir.mkdir("some-user")
    config_path = str(home_dir.join("cli_config.ini"))
    data_dir = str(home_dir.join("data_directory"))
    snapshots_dir = str(home_dir.join("snapshots_directory"))

    ConfigFixture = namedtuple("ConfigFixture", ["set_func", "get_func", "expected_value"])
    fixtures = [ ConfigFixture(jc.set_host, jc.get_host, "someurl.com"),
            ConfigFixture(jc.set_port, jc.get_port, 8080),
            ConfigFixture(jc.set_jarvis_data_directory,
                jc.get_jarvis_data_directory, data_dir),
            ConfigFixture(jc.set_jarvis_snapshots_directory,
                jc.get_jarvis_snapshots_directory, snapshots_dir),
            ConfigFixture(jc.set_author, jc.get_author, "Joe Schmo") ]

    env = "test"

    with jc.create_config(env, config_path) as config_map:
        for fixture in fixtures:
            fixture.set_func(config_map, fixture.expected_value)

        with pytest.raises(TypeError):
            jc.set_port(config_map, "should be an integer")

    config_map = jc.get_config_map(env, config_path)

    for fixture in fixtures:
        assert fixture.expected_value == fixture.get_func(config_map)
