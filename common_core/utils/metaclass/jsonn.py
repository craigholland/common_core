# -*- coding: utf-8 -*-
"""hack to make json Encoder work with datetime objects"""

import ast
import datetime
import functools
import json

import dateutil.parser
import jsonschema

__all__ = ["dumps", "loads"]


class DatetimeJSONEncoder(json.JSONEncoder):
    def __init__(self, **kwargs):
        super(DatetimeJSONEncoder, self).__init__(**kwargs)
        if kwargs.get("default") is not None:
            self.default = kwargs.get("default")

    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        return super(DatetimeJSONEncoder, self).default(obj)


dumps = functools.partial(json.dumps, cls=DatetimeJSONEncoder)


def validate_json(data, schema):
    """Validates a JSON object against a schema."""
    schema_validator = jsonschema.Draft7Validator(schema)
    return schema_validator.validate(data)


def loads(s, schema=None, **kwargs):
    """Loads a JSON string into a Python object."""
    s = json.dumps(ast.literal_eval(s))
    source = json.loads(s, **kwargs)
    if schema:
        validate_json(source, schema)
    return source


def iteritems(source):
    for k, v in source.items():
        if isinstance(v, (list, tuple)):
            for a in v:
                if hasattr(a, "items"):
                    iteritems(a)
        elif isinstance(v, dict):
            iteritems(v)
        elif isinstance(v, str):
            try:
                source[k] = dateutil.parser.parse(v)
            except (ValueError, OverflowError):
                pass
    return source
