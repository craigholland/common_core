# -*- coding: utf-8 -*-
from common_core.config.baseclass import ConfigMeta


class BaseConfig(metaclass=ConfigMeta):
    """A base Config Class for all services."""

    """
    This is just an example...don't inherit BaseConfig as your top-level
    Config class.  Simply create your own class and set the metaclass to
    `ConfigMeta` as above.

    Config variables/values can be set at multiple levels:
        -   os.environ['var_name']
        -   as a Class attribute (here or a subclass)
        -   in a referenced YAML file (pointed to by _YAML_FILE)
        -   at the instance-level

    The priority to which each of these levels has over the others is
    defined in the list `ConfigEnvVarType_Priority`
    (found in: common_core.config.baseclass.config_value.py)
    """

    # `_YAML_PATH` is the file location of desired YAML-file relative to the
    # particular Config() class.
    _YAML_PATH = "config.yaml"
