# -*- coding: utf-8 -*-
"""
NOTE: This module is "Beta" and is still under development. It is not yet
recommended for production use.

MapperMeta is a metaclass that is used to create a Mapper class that
converts data between a dataclass and a protobuf message.

Usage:
from my.path.to.dataclasses import Person as PersonDC
from my.path.to.protos import person_pb2 as PersonProto

class PersonMapper(metaclass=MapperMeta):
    __dataclass__ = PersonDC
    __protobuf__ = PersonProto
    __mapped_fields__ = {       # Optional; maps dc fields to protobuf fields
        "first_name": "firstName",
        "last_name": "lastName",
    }

person = PersonDC(first_name="John", last_name="Doe")
person_mapper = PersonMapper(person)
proto = person_mapper.protobuf  # Returns a PersonProto instance


"""
from dataclasses import fields, is_dataclass

from google.protobuf.message import Message

from common_core.utils.dateparser import DateParser
from common_core.utils.enums.custom_enum import CustomEnum, Enum
from common_core.utils.metaclass.json_type import JsonType


class MapperSource(Enum, metaclass=CustomEnum):
    DATACLASS = 0
    PROTOBUF = 1


class MapMeta:
    def __init__(
        self, dataclass, protobuf, mapped_fields, transforms, child_mapper
    ):
        self.dataclass = dataclass
        self.protobuf = protobuf
        self.mapped_fields = mapped_fields
        self.transforms = transforms
        self.child_mapper = child_mapper


class MapperMeta(type):
    _mappermeta_attrs = [
        ("dataclass", None),
        ("protobuf", None),
        ("transforms", {}),
        ("mapped_fields", {}),
        ("child_mapper", {}),
    ]

    def __new__(mcs, name, bases, dct):
        mapper_attr = dict(
            [(k, dct.get(f"__{k}__", v)) for k, v in mcs._mappermeta_attrs]
        )
        dc_class, pr_class, mapped_fields = mcs._validate_mapper(mapper_attr)
        map_meta = MapMeta(
            dataclass=dc_class,
            protobuf=pr_class,
            mapped_fields=mapped_fields,
            transforms=mapper_attr["transforms"],
            child_mapper=mapper_attr["child_mapper"],
        )
        mapper_cls = super().__new__(mcs, name, bases, {"meta": map_meta})
        mapper_cls.__init__ = mcs._init(mapper_cls)
        mapper_cls._convert = mcs._convert(mapper_cls)
        mapper_cls._convert_proto_to_dataclass = (
            mcs._convert_proto_to_dataclass(mapper_cls)
        )
        mapper_cls._convert_dataclass_to_proto = (
            mcs._convert_dataclass_to_proto(mapper_cls)
        )
        mapper_cls.dataclass = property(
            lambda self: self._convert(MapperSource.DATACLASS)
        )
        mapper_cls.protobuf = property(
            lambda self: self._convert(MapperSource.PROTOBUF)
        )
        return mapper_cls

    @classmethod
    def _init(cls, klass):
        def init(self, input_data):
            self._source_type = None
            self._input_data = input_data

            if isinstance(input_data, self.meta.dataclass):
                self._source_type = MapperSource.DATACLASS
            elif isinstance(input_data, self.meta.protobuf):
                self._source_type = MapperSource.PROTOBUF
            else:
                raise ValueError(
                    "Input data must be either a dataclass or protobuf "
                    "instance."
                )

        return init

    @classmethod
    def _convert(cls, klass):
        def convert(self, target_type: MapperSource):
            if target_type == self._source_type:
                return self._input_data
            elif target_type == MapperSource.PROTOBUF:
                return self._convert_dataclass_to_proto(
                    self._input_data,
                    self.meta.protobuf,
                    self.meta.mapped_fields,
                )
            elif target_type == MapperSource.DATACLASS:
                return self._convert_proto_to_dataclass(
                    self._input_data,
                    self.meta.dataclass,
                    self.meta.mapped_fields,
                )
            return None

        return convert

    @classmethod
    def _convert_proto_to_dataclass(cls, klass):
        def convert_proto_to_dataclass(
            self, proto_instance, dataclass_cls, mapped_fields
        ):
            dataclass_instance = dataclass_cls()
            for dc_field, pr_field in mapped_fields.items():
                if hasattr(dataclass_instance, dc_field) and hasattr(
                    proto_instance, pr_field
                ):
                    setattr(
                        dataclass_instance,
                        dc_field,
                        getattr(proto_instance, pr_field),
                    )
            return dataclass_instance

        return convert_proto_to_dataclass

    @classmethod
    def _convert_dataclass_to_proto(cls, klass):
        def convert_dataclass_to_proto(
            self, dataclass_instance, proto_cls, mapped_fields
        ):
            proto_instance = proto_cls()
            for dc_field, pr_field in mapped_fields.items():
                if hasattr(dataclass_instance, dc_field) and hasattr(
                    proto_instance, pr_field
                ):
                    mtype = proto_cls.DESCRIPTOR.fields_by_name[
                        pr_field
                    ].message_type
                    if mtype:
                        if mtype.full_name == "google.protobuf.Timestamp":
                            dc_value = getattr(dataclass_instance, dc_field)
                            try:
                                getattr(proto_instance, pr_field).CopyFrom(
                                    DateParser(dc_value).proto_timestamp
                                )
                            except Exception as e:
                                raise ValueError(
                                    f"Error converting dataclass.{dc_field}"
                                    f" value '{dc_value}' to "
                                    f"proto.{pr_field}: {e}"
                                )

                    else:
                        setattr(
                            proto_instance,
                            pr_field,
                            getattr(dataclass_instance, dc_field),
                        )
            return proto_instance

        return convert_dataclass_to_proto

    @staticmethod
    def _get_proto(pr_input):
        """Returns the Message class if pr_input is a Message instance or
        a Message class. Otherwise, returns None."""

        # pr_input must be a Message instance or a Message class
        if issubclass(pr_input, Message):
            if isinstance(pr_input, Message):
                return type(pr_input)
            else:
                return pr_input
        return None

    @staticmethod
    def _get_dataclass(dc_input):
        """Returns the dataclass class if dc_input is a dataclass instance or
        a dataclass class. Otherwise, returns None."""

        # dc_input must be a dataclass instance or a dataclass class
        if is_dataclass(dc_input):
            return dc_input if isinstance(dc_input, type) else type(dc_input)
        return None

    @staticmethod
    def _map_fields(dc_class, pr_class, mapped_fields):
        """Returns a dictionary of mapped fields where the keys are the
        dataclass field names and the values are the protobuf field names."""
        new_map = {}
        dc_keys = [f.name for f in fields(dc_class)]
        pr_keys = [f.name for f in pr_class.DESCRIPTOR.fields]
        for dc_key, pr_key in mapped_fields.items():
            if dc_key in dc_keys and pr_key in pr_keys:
                new_map[dc_key] = pr_key
            elif dc_key in dc_keys:
                raise ValueError(f"Invalid protobuf field: {pr_key}")
            else:
                raise ValueError(f"Invalid dataclass field: {dc_key}")
        for dc_key in dc_keys:
            if dc_key not in new_map and dc_key in pr_keys:
                new_map[dc_key] = dc_key
        for pr_key in pr_keys:
            if pr_key not in new_map and pr_key in dc_keys:
                new_map[pr_key] = pr_key
        return new_map

    @staticmethod
    def _validate_mapper(mapper_dct):
        """Validates the MapperMeta attributes and returns the dataclass and
        protobuf classes."""
        dc_class, pr_class, mapped_fields = None, None, {}
        if dc_input := mapper_dct["dataclass"]:
            dc_class = MapperMeta._get_dataclass(dc_input)
            if dc_class is None:
                raise ValueError(
                    f"Invalid dataclass definition. Got: {dc_input}"
                )
        else:
            raise ValueError("Missing MapperMeta.__dataclass__ attribute")

        if pr_input := mapper_dct["protobuf"]:
            pr_class = MapperMeta._get_proto(pr_input)
            if pr_class is None:
                raise ValueError(
                    f"Invalid protobuf definition. Got: {pr_input}"
                )
        else:
            raise ValueError("Missing MapperMeta.__protobuf__ attribute")
        mapped_fields = MapperMeta._map_fields(
            dc_class, pr_class, mapper_dct["mapped_fields"]
        )

        return dc_class, pr_class, mapped_fields


#
# import datetime as dt
# from dataclasses import dataclass
#
#
# @dataclass
# class PersonDC:
#     id: str
#     first_name: str
#     middle_name: str
#     last_name: str
#     date_of_birth: dt.date
#
#
# from solidpy_proto.protopy.solidpy_test_pb2 import Person as PersonProto

#
# class PersonMapper(metaclass=MapperMeta):
#     __dataclass__ = PersonDC
#     __protobuf__ = PersonProto
#
#
# person = PersonDC(
#     id="1a2b",
#     first_name="John",
#     middle_name="Doe",
#     last_name="Smith",
#     date_of_birth=dt.date(1973, 8, 30),
# )  # noqa


class MapperMeta_old(type):
    def __new__(mcs, name, bases, dct):
        dataclass = dct.get("__dataclass__", None)
        protobuf = dct.get("__protobuf__", None)
        mapped_fields = dct.get("__mapped_fields__", {})
        transforms = dct.get("__transforms__", {})
        child_mapper = dct.get("__child_mapper__", {})

        if dataclass is None or protobuf is None:
            raise ValueError(
                "Both __dataclass__ and __protobuf__ must be "
                "defined in the mapper class."
            )

        cls = super().__new__(mcs, name, bases, dct)
        cls.__init__ = mcs.__init
        cls.dataclass = property(mcs.dataclass)
        cls.protobuf = property(mcs.protobuf)
        cls._transforms = transforms
        cls._mapped_fields = mapped_fields
        cls._child_mapper = child_mapper
        cls.transform_value = staticmethod(mcs.__transform_value)
        cls.dataclass_cls = dataclass
        cls.proto_cls = protobuf
        cls.fields = dataclass.fields()

        # Set default methods in MapperClass
        cls._convert_to_protobuf = mcs.__default_convert_to_protobuf(cls)
        cls._convert_to_dataclass = mcs.__default_convert_to_dataclass(cls)
        cls._mapped_fields = mapped_fields
        return cls

    @staticmethod
    def __transform_value(func, source):
        idx = None
        if isinstance(func, tuple):
            func, idx = func
        val = func(source)
        if idx is not None:
            val = val[idx]
        return val

    @staticmethod
    def __init(self, input_data):
        if isinstance(input_data, self.dataclass_cls):
            self._source_type = "dataclass"
        elif isinstance(input_data, self.proto_cls):
            self._source_type = "protobuf"
        else:
            raise ValueError(
                "Input data must be either a dataclass or protobuf instance."
            )

        self._input_data = input_data
        self._dataclass_instance = None
        self._protobuf_instance = None

    def dataclass(self):
        if self._source_type == "dataclass":
            return self._input_data
        elif self._source_type == "protobuf":
            if self._dataclass_instance is None:
                self._dataclass_instance = self._convert_to_dataclass(
                    self._input_data
                )
            return self._dataclass_instance

    def protobuf(self):
        if self._source_type == "protobuf":
            return self._input_data
        elif self._source_type == "dataclass":
            if self._protobuf_instance is None:
                self._protobuf_instance = self._convert_to_protobuf(
                    self._input_data
                )
            return self._protobuf_instance

    # Default conversion methods
    @staticmethod
    def __default_convert_to_protobuf(class_object):
        def convert_to_proto(self, dataclass_instance):
            # Default method to convert dataclass to protobuf...
            transform = self._transforms.get("protobuf", {})
            pb = self.proto_cls()
            dc_data = self._input_data
            for field, meta in self.dataclass_cls.fields().items():
                pb_field = self._mapped_fields.get(field, field)

                # Enum fields
                if field in self.dataclass_cls.enum_fields():
                    if enum_obj := getattr(dc_data, field, None):
                        setattr(pb, pb_field, enum_obj.value)

                # Date and datetime fields
                elif field in self.dataclass_cls.datetime_fields():
                    if dt_obj := getattr(dc_data, field, None):
                        parser = DateParser(dt_obj)
                        getattr(pb, pb_field).FromDatetime(parser.datetime)

                # Json fields
                elif field in self.dataclass_cls.json_fields():
                    js = JsonType(getattr(dc_data, field, ""))
                    setattr(pb, pb_field, js.str)

                # Relationship fields
                elif field in self.dataclass_cls.relationship_fields():
                    values = getattr(dc_data, field, [])
                    for value in values:
                        child = getattr(pb, pb_field).add()
                        if mapper := self._child_mapper.get(field, None):
                            child_mapper = mapper(value)
                            child.CopyFrom(child_mapper.protobuf)
                        else:
                            child.CopyFrom(value)

                # Metadata fields
                elif field in self.dataclass_cls.metadata_fields():
                    meta_obj = getattr(dc_data, field)
                    setattr(pb, pb_field, meta_obj.str)
                # Other fields set directly based on defined
                # datatype in proto
                elif val := getattr(dc_data, field, None):
                    if pb_field := pb.DESCRIPTOR.fields_by_name.get(
                        pb_field, None
                    ):
                        if func := transform.get(field):
                            val = self.transform_value(func, self)
                        # Strings
                        if pb_field.type in [
                            pb_field.TYPE_STRING,
                            pb_field.TYPE_BYTES,
                        ]:
                            val = str(val)
                        # Integers
                        elif pb_field.type in [
                            pb_field.TYPE_INT32,
                            pb_field.TYPE_INT64,
                        ]:
                            val = int(val)
                        # Floats
                        elif pb_field.type in [
                            pb_field.TYPE_DOUBLE,
                            pb_field.TYPE_FLOAT,
                        ]:
                            val = float(val)
                        setattr(pb, field, val)

            for field in transform.keys():
                value = self.transform_value(transform[field], self)
                setattr(pb, field, value)
            return pb

        return convert_to_proto

    @staticmethod
    def __default_convert_to_dataclass(class_object):
        def convert_to_dc(self, protobuf_instance):
            # Default method to convert protobuf to dataclass...
            return True

        return convert_to_dc
