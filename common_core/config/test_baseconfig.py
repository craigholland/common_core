import pytest
from common_core.config.baseclass import (
    ConfigMeta,
    ConfigField,
    ConfigValue
)


def test_baseconfig_yaml_defaults():
    # These keys/values match those found in testdata/configs_by_default.yaml
    yaml_values = {
        "STR_BY_DEFAULT": "baseconfig",
        "INT_BY_DEFAULT": 1,
        "BOOL_BY_DEFAULT": False
    }

    class Config(metaclass=ConfigMeta):
        _YAML_PATH = "testdata/configs_by_default.yaml"

    # Confirm Config has lowercase version of YAML key
    for key in yaml_values.keys():
        assert getattr(Config, key, None) is None
        assert hasattr(Config, key.lower())

    # Confirm values match
    for key, value in yaml_values.items():
        assert yaml_values[key] == getattr(Config, key.lower())

    # Confirm correct metadata
    for key, value in yaml_values.items():
        cvalue = Config._values.get(key, None)
        assert isinstance(cvalue, ConfigValue)
        cfield = cvalue.field
        assert cfield.name == key
        assert cfield.datatype == type(value)
        assert cfield.required is False
        assert cfield.default == value
        assert cfield.locked is False


def test_inherited_config_override():
    yaml_values = {
        "STR_BY_DEFAULT": "baseconfig",
        "INT_BY_DEFAULT": 1,
        "BOOL_BY_DEFAULT": False
    }

    class Config(metaclass=ConfigMeta):
        _YAML_PATH = "testdata/configs_by_default.yaml"

    child_values = {
        "STR_BY_DEFAULT": "childconfig",
        "INT_BY_DEFAULT": 2,
    }

    class ChildConfig(Config):
        STR_BY_DEFAULT = child_values["STR_BY_DEFAULT"]
        INT_BY_DEFAULT = child_values["INT_BY_DEFAULT"]

    # Confirm Config has lowercase version of YAML key
    for key in yaml_values.keys():
        assert getattr(Config, key, None) is None
        assert hasattr(Config, key.lower())

    # Confirm values match
    assert ChildConfig.str_by_default == child_values["STR_BY_DEFAULT"]
    assert ChildConfig.int_by_default == child_values["INT_BY_DEFAULT"]
    assert ChildConfig.bool_by_default == yaml_values["BOOL_BY_DEFAULT"]


def test_inherited_config_lock():
    class Config(metaclass=ConfigMeta):
        STR_BY_DEFAULT = "baseconfig", 'locked'
        INT_BY_DEFAULT = 1, 'locked'
        BOOL_BY_DEFAULT = False

    class ChildConfig(Config):
        STR_BY_DEFAULT = "childconfig"
        INT_BY_DEFAULT = 2
        BOOL_BY_DEFAULT = True

    assert Config.str_by_default == "baseconfig"
    assert ChildConfig.str_by_default == "baseconfig"  # Locked

    assert Config.int_by_default == 1
    assert ChildConfig.int_by_default == 1  # Locked

    assert Config.bool_by_default is False
    assert ChildConfig.bool_by_default is True  # Not locked

    # Also confirm that Config class is locked and its attrs and values
    # cannot be changed.
    with pytest.raises(AttributeError):
        Config.str_by_default = "new_value"

    with pytest.raises(AttributeError):
        Config.int_by_default = 3

    with pytest.raises(AttributeError):
        Config.bool_by_default = False

    with pytest.raises(AttributeError):
        Config.new_attr = "new_value"


