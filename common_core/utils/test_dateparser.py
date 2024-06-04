# -*- coding: utf-8 -*-
import datetime as dt

import pytz
from google.protobuf.timestamp_pb2 import Timestamp  # noqa
from google.type.date_pb2 import Date as GoogleDate
from google.type.datetime_pb2 import DateTime as GoogleDateTime

from common_core.utils.dateparser import DateParser


def test_dateparser():
    now = dt.datetime.now()
    my_date_obj = DateParser(now)

    assert my_date_obj.datetime == now.replace(tzinfo=pytz.utc)
    assert my_date_obj.datetime_naive == now.replace(tzinfo=None)
    assert my_date_obj.time == now.time()
    assert my_date_obj.date == now.date()
    assert my_date_obj.timestamp == now.replace(tzinfo=pytz.utc).timestamp()

    assert isinstance(my_date_obj.proto_date, GoogleDate)
    assert (
        my_date_obj.proto_date.year,
        my_date_obj.proto_date.month,
        my_date_obj.proto_date.day,
    ) == (now.year, now.month, now.day)
    assert isinstance(my_date_obj.proto_datetime, GoogleDateTime)
    assert isinstance(my_date_obj.proto_timestamp, Timestamp)
    assert my_date_obj.proto_timestamp.seconds == int(
        now.replace(tzinfo=pytz.utc).timestamp()
    )
