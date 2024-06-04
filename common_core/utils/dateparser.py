# -*- coding: utf-8 -*-
from datetime import date, datetime
from typing import Union

import pytz
from dateutil import parser
from google.protobuf.timestamp_pb2 import Timestamp  # noqa
from google.type.date_pb2 import Date as GoogleDate
from google.type.datetime_pb2 import DateTime as GoogleDateTime


def from_proto_timestamp(proto_timestamp: Union[Timestamp, dict]) -> datetime:
    if isinstance(proto_timestamp, dict):
        proto_timestamp = Timestamp(**proto_timestamp)
    return proto_timestamp.ToDatetime(tzinfo=pytz.UTC)


def from_proto_datetime(
    proto_datetime: Union[GoogleDateTime, GoogleDate, dict]
) -> datetime:
    if isinstance(proto_datetime, dict):
        proto_datetime = GoogleDateTime(**proto_datetime)
    return proto_datetime.ToDatetime(tzinfo=pytz.UTC)


class DateParser:
    Timestamp = Timestamp
    GoogleDate = GoogleDate
    GoogleDateTime = GoogleDateTime

    def __init__(self, date_input):
        self._datetime = self.parse_input(date_input)

    @staticmethod
    def parse_input(date_input) -> datetime:
        if date_input is None:
            return None
        elif isinstance(date_input, int):
            return datetime.fromtimestamp(date_input, pytz.UTC)
        elif isinstance(date_input, str):
            dt = parser.parse(date_input)
            return (
                dt.astimezone(pytz.utc) if dt.tzinfo else pytz.utc.localize(dt)
            )
        elif isinstance(date_input, Timestamp):
            return from_proto_timestamp(date_input).astimezone(pytz.utc)
        elif isinstance(date_input, (GoogleDateTime, GoogleDate)):
            return from_proto_datetime(date_input).astimezone(pytz.utc)
        elif isinstance(date_input, datetime):
            return (
                date_input.astimezone(pytz.utc)
                if date_input.tzinfo
                else date_input.replace(tzinfo=pytz.utc)
            )
        elif isinstance(date_input, date):
            dt = datetime.combine(date_input, datetime.min.time())
            return dt.replace(tzinfo=pytz.utc)
        else:
            raise ValueError(f"Unsupported date format: {type(date_input)}")

    @property
    def datetime(self):
        return self._datetime

    @property
    def datetime_naive(self):
        return self._datetime.replace(tzinfo=None) if self._datetime else None

    @property
    def time(self):
        return self._datetime.time() if self._datetime else None

    @property
    def proto_date(self):
        d = self._datetime
        return GoogleDate(year=d.year, month=d.month, day=d.day) if d else None

    @property
    def proto_datetime(self):
        d = self._datetime
        return (
            GoogleDateTime(
                year=d.year,
                month=d.month,
                day=d.day,
                hours=d.hour,
                minutes=d.minute,
                seconds=d.second,
                nanos=d.microsecond * 1000,
            )
            if d
            else None
        )

    @property
    def proto_timestamp(self):
        if self._datetime:
            ts = Timestamp()
            ts.FromDatetime(self._datetime)
            return ts
        return None

    @property
    def timestamp(self):
        return self._datetime.timestamp() if self._datetime else None

    @property
    def isoformat(self):
        return self._datetime.isoformat() if self._datetime else None

    @property
    def date(self):
        return self._datetime.date() if self._datetime else None
