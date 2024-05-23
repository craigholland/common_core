# -*- coding: utf-8 -*-
from enum import Enum, EnumMeta


class CustomEnum(EnumMeta):
    """Custom Enum class to add additional methods to Enum classes"""

    def names(cls):
        """Return a list of names of the Enum members"""
        return [
            member.name
            for member in cls.__members__.values()
            if isinstance(member, Enum)
        ]
