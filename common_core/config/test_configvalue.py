import pytest
from common_core.config.baseclass import ConfigField, ConfigValue
from common_core.config.baseclass.config_field import (
    ConfigFieldError, VALID_VARNAME_CHARS)


def field_vars():
    return {
        'name': "TEST"
    }


def test_field_valid_names():
    dct = field_vars()
    field = ConfigField(**dct)
    assert field.name == dct['name']

    dct['name'] = 'TEST_WITH_UNDERSCORES'
    field = ConfigField(**dct)
    assert field.name == dct['name']

    dct['name'] = 'TEST_WITH_NUMBERS_0123456789'
    field = ConfigField(**dct)
    assert field.name == dct['name']


def test_field_invalid_names():
    # Field names must:
    # 1) consist of uppercase characters, digits, or underscore
    # 2) be at least 2 characters in length
    # 3) begin with an alpha character.
    for i, bad_name in enumerate(
            ['5TART_WITH_NUMBER',
             'A',
             'lower_case_name',
             'SPEC!@L_CHAR$']
    ):
        dct = field_vars()
        invalid_chars = set(bad_name).difference(VALID_VARNAME_CHARS)
        dct['name'] = bad_name
        if i == 1:
            expected_error = ConfigFieldError.NAME_LENGTH.format(
                'name', dct['name'])
        elif i:
            expected_error = ConfigFieldError.NAME_ILLEGALCHAR.format(
                'name', ', '.join(list(invalid_chars)), dct['name'])
        else:
            expected_error = ConfigFieldError.NAME_STARTSWITH.format(
                'name', dct['name'])

        with pytest.raises(ValueError) as exc:
            _ = ConfigField(**dct)
        assert exc.value.args[0] == expected_error


def test_field_invalid_attrs():
    # Cannot add new/undefined attributes to a field
    dct = field_vars()
    bad_attr = 'invalid_attribute'
    field = ConfigField(**dct)
    expected_error = ConfigFieldError.INVALID_KEY.format(bad_attr)
    with pytest.raises(KeyError) as exc:
        setattr(field, bad_attr, 'test')
    assert exc.value.args[0] == expected_error


def test_field_datatypes():
    dct = field_vars()
    # Default datatype == <str>
    field = ConfigField(**dct)
    assert field.datatype is str

    for my_int in [int, 'int']:
        dct['datatype'] = my_int
        field = ConfigField(**dct)
        assert field.datatype is int

    for my_bool in [bool, 'bool']:
        dct['datatype'] = my_bool
        field = ConfigField(**dct)
        assert field.datatype is bool

    # Multiple datatypes
    dct['datatype'] = [int, bool]
    field = ConfigField(**dct)
    assert isinstance(9, tuple(field.datatype))
    assert isinstance(True, tuple(field.datatype))
    assert not isinstance("True", tuple(field.datatype))
    assert not isinstance([9, True], tuple(field.datatype))


def test_compare_values():
    dct = field_vars()
    field_no_default = ConfigField(**dct)
    value = ConfigValue(
        field=field_no_default
    )
    assert not value.value_set
    assert not value.is_valid

    dct['default'] = 5
    field = ConfigField(**dct)
    value1 = ConfigValue(
        field=field
    )
    assert value1.is_valid   # Default value is active and valid
    assert not value1.value_set  # Value is still not set though
    assert field.datatype is type(dct['default'])
    assert value1.field.datatype is field.datatype
    assert value1.value == dct['default']

    new_value = 1
    value1.value = new_value
    assert value1.value_set
    assert value1.value == new_value

    value2 = ConfigValue(
        field=field
    )
    assert not value2.value_set
    assert value1.common(value2)
    assert value1.compare(value2) == value1  # Value2 is not set yet.

    value2.value = 4
    assert value2.value_set
    assert value1.compare(value2) == value2  # Value2 is set.

