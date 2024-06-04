# -*- coding: utf-8 -*-
import datetime as dt

from common_core.utils.metaclass.json_type import JsonType


def test_json_obj():
    # Create a JsonType object
    my_json_obj = JsonType(
        {"name": "Craig", "birthday": dt.datetime(1973, 8, 30)}
    )

    # Access various object attributes
    assert my_json_obj.obj == {
        "name": "Craig",
        "birthday": dt.datetime(1973, 8, 30, 0, 0),
    }
    assert (
        my_json_obj.str
        == '{"name": "Craig", "birthday": "1973-08-30T00:00:00"}'
    )
    assert my_json_obj.json == {
        "name": "Craig",
        "birthday": "1973-08-30T00:00:00",
    }
