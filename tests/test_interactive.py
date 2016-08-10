import pytest
from jarvis_cli.exceptions import JarvisPromptError
from jarvis_cli.interactive import for_init as jii


def test_prompt_init_config(tmpdir, monkeypatch):
    some_dir = tmpdir.mkdir("some-user")
    config_map = {}

    def test_set(config_map, answer):
        config_map["somepref"] = answer

    # Test default
    monkeypatch.setitem(__builtins__, 'input', lambda noop: "")
    jii._prompt_config_value(config_map, "sometitle", test_set, "criticalvalue")
    assert config_map["somepref"] == "criticalvalue"

    # Test non-directory input
    monkeypatch.setitem(__builtins__, 'input', lambda noop: "othervalue")
    jii._prompt_config_value(config_map, "sometitle", test_set, "criticalvalue")
    assert config_map["somepref"] == "othervalue"

    # Test directory input
    monkeypatch.setitem(__builtins__, 'input', lambda noop: str(some_dir))
    jii._prompt_config_value(config_map, "sometitle directory", test_set, "criticalvalue")
    assert config_map["somepref"] == str(some_dir)

    monkeypatch.setitem(__builtins__, 'input', lambda noop: "/doesnotexist")
    with pytest.raises(JarvisPromptError):
        jii._prompt_config_value(config_map, "sometitle directory", test_set, "criticalvalue")
