from common_core.config.baseclass.config_field import ConfigField
from common_core.config.baseclass.config_enums import ConfigEnvVarType
from dataclasses import dataclass, InitVar, MISSING
from typing import Any


ConfigEnvVarType_Priority = [
    # ConfigEnvVarType determines the sequence in which ConfigMeta searches
    # for and defines config variables...with those of lower priority being
    # defined first, but possibly overwritten by those of higher priority.
    # Note: A variable of low priority can be 'locked', thus disabling
    # a higher priority from overwriting it.

    ConfigEnvVarType.CONFIG_INSTANCE,   # Highest Priority
    ConfigEnvVarType.CONFIG_CLASS,
    ConfigEnvVarType.CONFIG_YAML,
    ConfigEnvVarType.OS_ENVIRON         # Lowest Priority
]

_ERR_PFX = "ConfigValue: "


class ConfigValueError:
    """Message Literals used for Errors in ConfigValue."""
    UNCOMMON = (
            _ERR_PFX + "Expected type 'ConfigValue'. Got '{0}' instead.")
    BAD_FIELD = (
            _ERR_PFX + "Config `field` must be of type `ConfigField`. "
                       "Got {0} instead.")
    BAD_SOURCE = (
            _ERR_PFX + "Config `{0}.source` must be of type "
                       "`ConfigEnvVarType`. Got {1} instead.")
    BAD_VALUE = (_ERR_PFX + "Config `{0}.value` must be of type(s) {1}. Got "
                            "{2} instead.")
    REQUIRED_VALUE = (_ERR_PFX + "field '{0}' value is required and no default"
                                 " value was defined.")
    LOCKED = (_ERR_PFX + "Locked. Cannot edit field `{0}`.")


@dataclass
class ConfigValue:
    field: ConfigField
    value: Any = type(MISSING)
    source: ConfigEnvVarType = ConfigEnvVarType.OS_ENVIRON
    source_name: str = ''
    _raise_exception_on_edit: InitVar[bool] = True

    def __post_init__(self, _raise_exception_on_edit):
        self._value = type(MISSING)  # self.value_set == False
        if self.value is not type(MISSING):
            self._value = self.value
        self._initialized = True

    def __getattribute__(self, item):
        if item == 'value' and self.initialized:
            if self._value is type(MISSING):
                if self.field.default:
                    return self.field.default
                else:
                    return None
            return self._value
        return super().__getattribute__(item)

    def __getattr__(self, item):
        if item == 'initialized':
            return False
        return super().__getattr__(item)

    def __setattr__(self, key, value):
        if self.initialized and self.is_locked:
            if self._raise_exception_on_edit:
                raise ValueError(ConfigValueError.LOCKED.format(key))
            return
        elif self.initialized and key == 'value':
            self._value = value
        else:
            super().__setattr__(key, value)
        if self._raise_exception_on_edit and self.initialized and key != '_initialized':
            self.__validate()

    def __validate(self):
        if not isinstance(self.field, ConfigField):
            raise ValueError(ConfigValueError.BAD_FIELD.format(type(self.field)))
        field_name = self.field.name
        if not isinstance(self.source, ConfigEnvVarType):
            raise ValueError(ConfigValueError.BAD_SOURCE.format(field_name, type(self.source)))
        if not self.field.validate_value(self.value):
            if self.value is None and self.field.required:
                raise ValueError(ConfigValueError.REQUIRED_VALUE.format(field_name))
            raise ValueError(ConfigValueError.BAD_VALUE.format(field_name, self.field.datatype, type(self.value)))

    @property
    def value_set(self) -> bool:
        return getattr(self, '_value', type(MISSING)) is not type(MISSING)

    @property
    def is_valid(self) -> bool:
        try:
            self.__validate()
            return True
        except ValueError:
            return False
    @property
    def initialized(self):
        return self.__dict__.get('_initialized', False)




    @property
    def source_priority(self):
        # Lower Number = Higher Priority
        return ConfigEnvVarType_Priority.index(self.source)

    def __ge__(self, config_value):
        return self > config_value or self == config_value

    def __le__(self, config_value):
        return self < config_value or self == config_value
    
    def __gt__(self, config_value):
        if self.common(config_value):
            return self.source_priority < config_value.source_priority
        raise TypeError(ConfigValueError.UNCOMMON.format(type(config_value)))
            
    def __eq__(self, config_value):
        if self.common(config_value):
            return self.source_priority == config_value.source_priority
        raise TypeError(ConfigValueError.UNCOMMON.format(type(config_value)))
        
    def __lt__(self, config_value):
        if self.common(config_value):
            return self.source_priority > config_value.source_priority
        raise TypeError(ConfigValueError.UNCOMMON.format(type(config_value)))

    @property
    def is_locked(self):
        return self.field.locked

    def common(self, config_value):
        return (
                isinstance(config_value, ConfigValue) and
                config_value.field == self.field)

    def compare(self, config_value):
        """Compare 2 ConfigValues and return the one of higher priority IF
        the existing value is not locked; otherwise, return existing
        value regardless of new value's priority.


         The context of the comparison is that 'self' is the existing value

        A 'set' config_value is where its value has explicitly been set.
          Conversely, an 'unset' config_value is where its value has yet to
          be set and, if applicable, a default value is used as the value.

        A 'locked' config_value is where its value cannot be changed once it
         has been explicitly set.

        A 'set' value will always overwrite an 'unset' value, regardless of priority
        A 'locked' value can never be overwritten, regardless of priority
        """

        if self.common(config_value):
            if (
                    not config_value.value_set  # New value is unset, so ignore
                    or (self.value_set and self.is_locked)   # Existing value is locked
                    or (self.value_set and self > config_value)  # Existing value has higher priority
            ):
                return self
            return config_value
        raise TypeError(ConfigValueError.UNCOMMON.format(type(config_value)))

    def copy(self, unlocked=True):
        new_field = self.field
        if unlocked:
            new_field.locked = False
        return ConfigValue(
            new_field,
            self.value,
            self.source
        )
