from enum import Enum
from typing import *

from disnake.utils import format_dt

from .dict_convertible import DictConvertible


class AppealType(Enum):
    DENYKLIST_APPEAL = 0
    GUILD_DENYLIST_APPEAL = 1
    SUPPORT_SERVER_BAN = 2
    SUPPORT_SERVER_MISC_PUNISHMENT = 3
    OTHER = 4


class Appeal(DictConvertible):
    __slots__ = (
        "user_id",
        "appeal_msg",
        "timestamp",
        "appeal_num",
        "cache",
        "special_id",
        "type",
    )

    def __init__(
        self,
        *,
        user_id: int,
        appeal_msg: str,
        timestamp: int,
        appeal_num: int,
        special_id: int,
        type: int,
    ):
        try:
            self.type = AppealType(type)
        except:
            raise ValueError(f"{type} is not a valid AppealType")
        self.user_id = user_id
        self.appeal_msg = appeal_msg
        self.timestamp = timestamp
        self.appeal_num = appeal_num
        self.special_id = special_id

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            user_id=data["user_id"],
            appeal_msg=data["appeal_msg"],
            timestamp=data["timestamp"],
            appeal_num=data["appeal_num"],
            special_id=data["special_id"],
            type=data["type"],
        )

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "appeal_msg": self.appeal_msg,
            "timestamp": self.timestamp,
            "appeal_num": self.appeal_num,
            "special_id": self.special_id,
            "appeal_type": str(self.type.name),
        }

    def __str__(self):
        return f"""
        Appeal from <@{self.user_id}>:
        type: {str(self.type.name)}
        timestamp: {format_dt(self.timestamp)}
        
        Appeal message: {self.appeal_msg}
        
        This is appeal #{self.appeal_num}
        and its special id is {self.special_id}
        
"""
