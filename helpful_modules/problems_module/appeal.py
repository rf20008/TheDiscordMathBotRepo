"""
You can distribute any version of the Software created and distributed *before* 23:17:55.00 July 28, 2024 GMT-4
under the GNU General Public License version 3 or at your option, any  later option.
But versions of the code created and/or distributed *on or after* that date must be distributed
under the GNU *Affero* General Public License, version 3, or, at your option, any later version.

TheDiscordMathProblemRepo - Appeal/AppealType/AppealViewInfo


This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

Author: Samuel Guo (64931063+rf20008@users.noreply.github.com)
"""
from enum import Enum
from typing import *

import orjson
from disnake.utils import format_dt

from .dict_convertible import DictConvertible


class AppealType(Enum):
    DENYLIST_APPEAL = 0
    GUILD_DENYLIST_APPEAL = 1
    SUPPORT_SERVER_BAN = 2
    SUPPORT_SERVER_MISC_PUNISHMENT = 3
    OTHER = 4
    NOT_SET = 5
    UNKNOWN = 6
    def __int__(self):
        return self.value

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
            type=AppealType(data["type"]),
        )

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "appeal_msg": self.appeal_msg,
            "timestamp": self.timestamp,
            "appeal_num": self.appeal_num,
            "special_id": self.special_id,
            "appeal_type": int(self.type),
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


class AppealViewInfo(DictConvertible):
    def __init__(
        self, message_id: int, user_id: int, guild_id: int, done: bool = False, pages: list[str] = None, appeal_type: AppealType | int = AppealType.NOT_SET
    ):
        self.message_id = message_id
        self.user_id = user_id
        self.guild_id = guild_id
        self.done = done
        if not pages:
            pages = []
        if isinstance(pages, str):
            pages = orjson.loads(pages)
        self.pages = pages
        if isinstance(appeal_type, int):
            appeal_type = AppealType(appeal_type)
        self.appeal_type = appeal_type

    def mark_done(self):
        self.done = True

    def to_dict(self):
        return {
            "message_id": self.message_id,
            "user_id": self.user_id,
            "guild_id": self.guild_id,
            "done": self.done,
            "pages": self.pages,
            "appeal_type": int(self.appeal_type)
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            message_id=data["message_id"],
            user_id=data["user_id"],
            guild_id=data["guild_id"],
            done=data.get("done", False),
            pages = data.get("pages", []),
            appeal_type = AppealType(data.get("appeal_type", AppealType.NOT_SET.value))
        )

    def __repr__(self):
        return f"AppealViewInfo(message_id={self.message_id}, user_id={self.user_id}, guild_id={self.guild_id}, done={self.done} type={self.appeal_type})"
