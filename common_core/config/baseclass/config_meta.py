# -*- coding: utf-8 -*-
import os

from common_core.config.baseclass.config_enums import ConfigEnvVarType
from common_core.config.baseclass.config_field import (
    ConfigField,
    is_valid_envvar_name,
)
from common_core.config.baseclass.config_value import (
    ConfigEnvVarType_Priority,
    ConfigValue,
)
from common_core.utils.baseclass import (
    BaseNestedDataclass,
    YAMLLoader,
    nested_dataclass_factory,
)
from common_core.utils.os_sys import get_abs_path

#  _YAML_FILE_VAR is the name of the class attribute that ConfigMeta will
#  look for in each subclass that points to an optional YAML config file.
_YAML_FILE_VAR = "_YAML_PATH"

# _LOCK_ATTRS_ON_INIT_VAR is the name of the class attribute that ConfigMeta
# will look for in determining if to lock the class attributes once the
# class is created.
# A Locked class cannot add new attributes. (Default: True)
_LOCK_ATTRS_ON_INIT_VAR = "_LOCK_ATTRS_ON_INIT"

# _LOCK_VALUE_ON_INIT_VAR is the name of the class attribute that
# ConfigMeta will look for in determining if to lock the values after
# initialization.
# A Locked class cannot change attribute Values. (Default: True)
_LOCK_VALUES_ON_INIT_VAR = "_LOCK_VALUES_ON_INIT"

_ERR_PFX = "ConfigMeta: "


class ConfigMetaError:
    """Message Literals used for Errors in ConfigValue."""

    ATTRS_LOCKED = (
        _ERR_PFX + "Config `{0}` is locked. Cannot add new attribute"
        " `{1}`.  (Set `_LOCK_ATTRS_ON_INIT` to False to "
        "keep unlocked)"
    )
    VALUES_LOCKED = (
        _ERR_PFX + "Config `{0}` is locked after initialization. Cannot "
        "change attribute values `{1} = {2}`.  (Set "
        "`_LOCK_VALUES_ON_INIT` to False to keep unlocked)"
    )


class ConfigMeta(type):
    """Base metaclass for Config classes that can be loaded from environment
    and designed to manage subclassed and multiple inheritances."""

    """
    Usage:
    class MyConfig(metaclass=ConfigMeta):
        _YAML_PATH = 'config.yaml'  # Optional
        _LOCK_ATTRS_ON_INIT = True  # Optional
        _LOCK_VALUES_ON_INIT = True  # Optional
        attr1: str = 'default'
        attr2: int = 1
        attr3: bool = False

    my_config = MyConfig()
    """

    def __new__(mcs, name, bases, attrs, *args, **kwargs):
        new_class = super().__new__(mcs, name, bases, attrs)
        # Class Metadata
        new_class._metadata: BaseNestedDataclass
        new_class._local_meta: BaseNestedDataclass = mcs._build_metadata(
            new_class
        )

        new_class.__init_subclass__ = classmethod(mcs.init_subclass())
        local_defined_init_func = new_class.__init__
        new_class.__init__ = mcs.init(new_class, local_defined_init_func)
        new_class.__setattr__ = classmethod(mcs.set_attr(new_class))
        new_class._values: dict = {}

        #  Get the absolute path of the YAML file, if provided
        if rel_yaml_file := getattr(new_class, _YAML_FILE_VAR, None):
            abs_yaml_file = get_abs_path(rel_yaml_file, new_class)
            setattr(new_class, _YAML_FILE_VAR, abs_yaml_file)

        #  Import values from YAML and class attributes
        mcs.__import_values(new_class)

        new_class._local_meta.class_built = True
        return new_class

    @classmethod
    def _build_metadata(mcs, klass):
        mro_keys = BaseNestedDataclass.get_mro_keys(klass)
        lock_attrs = getattr(klass, _LOCK_ATTRS_ON_INIT_VAR, True)
        lock_values = getattr(klass, _LOCK_VALUES_ON_INIT_VAR, True)

        if len(mro_keys) == 1:
            default_fields = {
                "lock_attrs": lock_attrs,
                "lock_values": lock_values,
                "class_built": False,
                "initialized": False,
                "subclassed": False,
                "top_parent": False,
            }
            klass._metadata = nested_dataclass_factory(
                mro_keys[0], default_fields
            )
            klass._metadata.top_parent = True
            return klass._metadata
        else:
            child_meta = klass._metadata.get_child(
                *mro_keys[1:], auto_create=True
            )
            child_meta.lock_attrs = lock_attrs
            child_meta.lock_values = lock_values
            return child_meta

    def __setattr__(cls, key, value):
        if meta := getattr(cls, "_local_meta", {}):
            if meta.class_built and meta.lock_attrs and key != "_local_meta":
                raise AttributeError("Class attributes locked")
            if meta.initialized and meta.lock_values:
                if value != getattr(cls, key):
                    raise AttributeError("Class values locked")
        super().__setattr__(key, value)

    @classmethod
    def set_attr(mcs, cls):
        def _set_attr(cls, key, value):
            if (
                not cls._local_meta.lock_values
                or not cls._local_meta.initialized
            ):
                super().__setattr__(key, value)
            else:
                raise Exception("Class values locked")

        return _set_attr

    @classmethod
    def init(mcs, cls, local_init):
        def _init(self, *args, **kwargs):
            if cls._local_meta.top_parent:
                # Pre_init_code here
                print(f"Running pre-init from {cls.__name__}")
            super(cls, self).__init__(*args, **kwargs)

            local_init(self, *args, **kwargs)
            cls._local_meta.initialized = True

        return _init

    @staticmethod
    def init_subclass():
        def _init_subclass(cls, **kwargs):
            cls._local_meta.subclassed = True

        return _init_subclass

    @staticmethod
    def __generate_config_field(
        name: str, metadata: dict = None, by_value=None
    ):
        metadata = metadata or {}
        metadata["name"] = name
        if by_value is not None:
            metadata["datatype"] = type(by_value)
            metadata["default"] = by_value
        if (
            metadata.get("default", None) is not None
            and metadata.get("datatype", None) is None
        ):
            metadata["datatype"] = type(metadata["default"])
        return ConfigField(**metadata)

    @classmethod
    def __import_values(mcs, klass):
        existing_values = {}
        for base in klass.__bases__:
            if isinstance(base, ConfigMeta):
                existing_values.update(base._values)
            else:
                # TODO: figure out how to import non-ConfigMeta attrs
                pass

        fields = mcs.__class_fields(klass)
        new_values = mcs.__class_values(klass, fields)

        for value in new_values:
            if existing_value := existing_values.get(value.field.name, None):
                value = existing_value.compare(value)
            existing_values[value.field.name] = value
        klass._values = existing_values

        # Replace UPPER_CASE attributes with lower_case ones.
        for attr, config_value in klass._values.items():
            new_attr = config_value.field.alt_name or attr
            setattr(klass, new_attr.lower(), config_value.value)
            if hasattr(klass, attr):
                delattr(klass, attr)

    @classmethod
    def __class_fields(mcs, klass):
        fields = []

        # Get child YAML
        if yaml_file := getattr(klass, _YAML_FILE_VAR, None):
            yaml_data = YAMLLoader(yaml_file).asdict
            for k, v in yaml_data.items():
                if isinstance(v, (dict, type(None))):
                    fields.append(mcs.__generate_config_field(k, v))
                else:
                    fields.append(mcs.__generate_config_field(k, by_value=v))

        # Get Class
        for attr in [
            a
            for a in vars(klass)
            if a != _YAML_FILE_VAR and is_valid_envvar_name(a)
        ]:
            val = getattr(klass, attr)
            if isinstance(val, ConfigField):
                fields.append(val)
            elif isinstance(val, dict):
                if not set(val.keys()).difference(
                    set(ConfigField._fields.keys())
                ):
                    fields.append(klass.generate_config_field(attr, val))
            elif isinstance(val, tuple):
                metadata = {}
                try:
                    for i, item in enumerate(val):
                        if i == 0:  # first index is the value
                            metadata["datatype"] = type(item)
                        elif isinstance(item, str):
                            if item.lower() == "locked":
                                metadata["locked"] = True
                            elif item.lower() == "required":
                                metadata["required"] = True
                            elif item.startswith(
                                "metadata={"
                            ) and item.endswith("}"):
                                field_meta = {}
                                for metastr in [
                                    s.strip() for s in item.split(",")
                                ]:
                                    kw, val = parse_keyword_str(metastr)
                                    field_meta[kw] = val
                                metadata["metadata"] = field_meta
                            elif set(item).intersection({"=", ":"}):
                                kw, val = parse_keyword_str(item)
                                metadata[kw] = val
                    fields.append(mcs.__generate_config_field(attr, metadata))
                except Exception:
                    pass
            else:
                fields.append(mcs.__generate_config_field(attr, by_value=val))
        return fields

    @classmethod
    def __class_values(mcs, klass, class_fields):
        yaml_data = {}
        if yaml_file := getattr(klass, _YAML_FILE_VAR, None):
            yaml_data = YAMLLoader(yaml_file).asdict
        values = []
        for field in class_fields:
            value = None
            for priority in reversed(ConfigEnvVarType_Priority):
                new_value = None
                if (
                    priority == ConfigEnvVarType.OS_ENVIRON
                    and field.name in os.environ
                ):
                    new_value = os.environ.get(field.name)
                    new_value = ConfigValue(
                        field, new_value, priority, klass.__name__
                    )
                elif (
                    priority == ConfigEnvVarType.CONFIG_CLASS
                    and field.name in vars(klass)
                ):
                    new_value = getattr(klass, field.name)
                    if isinstance(new_value, tuple):
                        new_value = new_value[0]
                    new_value = ConfigValue(
                        field, new_value, priority, klass.__name__
                    )
                elif (
                    priority == ConfigEnvVarType.CONFIG_YAML
                    and field.name in yaml_data
                ):
                    yaml_value = yaml_data[field.name]
                    if not isinstance(yaml_value, (dict, type(None))):
                        if isinstance(yaml_value, tuple):
                            yaml_value = yaml_value[0]
                        new_value = ConfigValue(
                            field, yaml_value, priority, klass.__name__
                        )
                else:
                    continue
                if new_value:
                    value = value.compare(new_value) if value else new_value
                elif field.default is not None:
                    new_value = ConfigValue(
                        field,
                        field.default,
                        ConfigEnvVarType.CONFIG_CLASS,
                        klass.__name__,
                    )
                    value = value.compare(new_value) if value else new_value
            if value:
                values.append(value)
        return values


def parse_keyword_str(kw_str):
    """takes str 'keyword=my value' and returns {keyword: 'my_value'}"""
    delimiters = ["=", ":"]

    # Find first instance of any delimiter
    sep = min(
        [i for i in [kw_str.find(d) for d in delimiters] if i >= 0] or [-1]
    )
    if 0 >= sep or sep == len(kw_str) - 1:
        # (delimiter not found or is first/last character)
        raise Exception(f"bad format: {kw_str}")
    else:
        kw, val = kw_str[:sep], kw_str[sep + 1 :]

    quotes = ("'", '"')
    if val[0] in quotes and val[-1] in quotes and val[0] == val[-1]:
        return kw, val[1:-1]
    elif val.lower() == "true":
        return kw, True
    elif val.lower() == "false":
        return kw, False
    else:
        try:
            return kw, int(val)
        except ValueError:
            try:
                return kw, float(val)
            except ValueError:
                return kw, val
