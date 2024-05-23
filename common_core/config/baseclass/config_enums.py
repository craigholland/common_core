from enum import Enum
from common_core.utils.enums.custom_enum import CustomEnum


class SystemEnvironment(Enum, metaclass=CustomEnum):
    LOCAL = 0
    TEST = 1
    STAGING = 2
    UAT = 3
    PRODUCTION = 4


class ConfigEnvVarType(Enum, metaclass=CustomEnum):
    OS_ENVIRON = 1
    CONFIG_YAML = 2
    CONFIG_CLASS = 3
    CONFIG_INSTANCE = 4


