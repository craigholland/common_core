# -*- coding: utf-8 -*-
"""Note: JsonType uses the jsonn module in order to handle datetime
objects more elegantly.

Usage:
import datetime as dt
from common_core.utils.metaclass.json_type import JsonType

# Create a JsonType object
my_json_obj = JsonType({
    "name": "Craig",
    "birthday": dt.datetime(1973, 8, 30)
})

# Access various object attributes
>> my_json_obj.obj  # Returns the object as a Python dict with datetime objects
{'name': 'Craig', 'birthday': datetime.datetime(1973, 8, 30, 0, 0)}

>> my_json_obj.str  # Returns the object as a JSON string
'{"name": "Craig", "birthday": "1973-08-30T00:00:00"}'

>> my_json_obj.json  # Returns the object as a JSON-friendly Python dict
{'name': 'Craig', 'birthday': '1973-08-30T00:00:00'}

"""
from common_core.utils.metaclass import jsonn


class JsonType(dict):
    """A datatype to denote that a value is a JSON-friendly object -- either
    a serializable Python object, a JSON-string, or another JsonType object."""

    def __str__(self):
        return self.str

    def __repr__(self):
        return (
            f"{type(self).__name__}"
            f"({repr(self.obj)}, force_list={self._force_list})"
        )

    def __init__(self, content=None, force_list=None):
        self._data = content or dict()
        self._data_type = None
        self._force_list = force_list is not None
        self.__validate_content()
        if content := self._data:
            super().__init__(content)

    def __validate_content(self):
        data = self._data
        force_list = self._force_list
        while type(data) is type(self):
            # Handle the possibility of nested JsonTypes
            force_list = data._force_list
            data = data._data

        if not self.is_valid_json(data):
            raise Exception(self.__json_error_msg())

        self._data = jsonn.loads(data) if isinstance(data, str) else data
        self._data_type = list if force_list else type(self._data)
        if isinstance(self._data, list):
            self.__init__(
                dict([(i, v) for i, v in enumerate(self._data)]), True
            )

    @property
    def obj(self):
        if self._force_list or self._data_type is list:
            return list(v for v in self._data.values())
        else:
            return self._data

    @property
    def str(self):
        return jsonn.dumps(self.obj)

    @property
    def json(self):
        if self.str:
            return jsonn.loads(self.str)

    @staticmethod
    def is_valid_json(value):
        if isinstance(value, JsonType):
            return True
        try:
            if isinstance(value, str):
                jsonn.loads(value)
            else:
                jsonn.dumps(value)
            return True
        except Exception:
            return False

    def __json_error_msg(self):
        if isinstance(self._data, str):
            load = jsonn.loads(self._data)
            if isinstance(load, str):
                return f"Load failed. Invalid JSON string: {load}"
        else:
            try:
                jsonn.dumps(self._data)
            except TypeError:
                return f"Dump failed. Can't serialize object: {self._data}"
            except ValueError:
                return (
                    f"Dump failed (ValueError). Can't serialize "
                    f"object: {self._data}"
                )
