"""
You can distribute any version of the Software created and distributed *before* 23:17:55.00 July 28, 2024 GMT-4
under the GNU General Public License version 3 or at your option, any  later option.
But versions of the code created and/or distributed *on or after* that date must be distributed
under the GNU *Affero* General Public License, version 3, or, at your option, any later version.

TheDiscordMathProblemBotRepo - Denylistable

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
import time
from typing import Dict

from .dict_convertible import DictConvertible, T
from enum import Enum

class DenylistType(Enum):
    GENERAL_USER_DENYLIST = "General User Denylist"
    UNKNOWN = "Unknown"
    VERIFICATION_CODE_DENYLIST = "Verification code denylist"
    GENERAL_GUILD_DENYLIST = "General Guild Denylist"

class Denylistable(DictConvertible):
    """Objects of this class can be denylisted, removed from the denylist, and have 3 attributes"""
    denylisted: bool
    denylist_reason: str
    denylist_expiry: float
    denylisting_moderator: str
    denylist_type: DenylistType
    def denylist(self, reason: str = "", duration: float = float('inf'), denylisting_moderator: str = "Unknown", denylist_type: DenylistType = DenylistType.UNKNOWN):
        """Denylist this object for a specific duration with a reason"""
        if not isinstance(reason, str):
            raise TypeError("reason is not a str")
        if not isinstance(duration, float):
            raise TypeError("duration is not a float")
        if not isinstance(denylisting_moderator, str):
            raise TypeError("Denylisting_moderator is not a str!")
        if not isinstance(denylist_type, DenylistType) and not isinstance(denylist_type, str):
            raise TypeError("Denylist type is not a DenylistType")
        if isinstance(denylist_type, str):
            if denylist_type not in tuple(DenylistType):
                raise ValueError("Unknown denylist type!")
            denylist_type = DenylistType(denylist_type)
        if duration < 0:
            raise ValueError("You're denylisting for negative time")
        self.denylist_expiry = time.time() + duration
        self.denylisted = True
        self.denylist_reason = reason
        self.denylist_type = denylist_type
        self.denylisting_moderator = denylisting_moderator

    def undenylist(self):
        """Remove the object from the denylist"""
        if not self.is_denylisted():
            raise RuntimeError("This object is not currently denylisted!")
        self.denylisted = False
        self.denylist_expiry = 0.0
        self.denylist_reason = ""
    def is_denylisted(self) -> bool:
        """Check if this object is currently denylisted"""
        if not self.denylisted:
            return False
        return time.time() < self.denylist_expiry

class DenylistMetadata(Denylistable):
    def __init__(self, denylisted: bool, denylist_reason: str, denylist_expiry: float, denylisting_moderator: str, denylist_type: DenylistType | str):
        if not isinstance(denylisted, bool):
            raise TypeError("denylisted is not a bool")
        self.denylisted=denylisted
        if not isinstance(denylist_reason, str):
            raise TypeError("reason is not a str")
        self.denylist_reason=denylist_reason
        if not isinstance(denylist_expiry, float):
            raise TypeError("denylist expiry is not a float")
        self.denylist_expiry=denylist_expiry
        if not isinstance(denylisting_moderator, str):
            raise TypeError("Denylisting_moderator is not a str!")
        self.denylisting_moderator=denylisting_moderator
        if not isinstance(denylist_type, DenylistType) and not isinstance(denylist_type, str):
            raise TypeError("Denylist type is not a DenylistType")
        if isinstance(denylist_type, str):
            if denylist_type not in tuple(DenylistType):
                raise ValueError("Unknown denylist type!")
            denylist_type = DenylistType(denylist_type)
        self.denylist_type=denylist_type

    def to_dict(self) -> Dict:
        return {
            'denylisted': self.denylisted,
            'denylist_reason': self.denylist_reason,
            'denylist_expiry': self.denylist_expiry,
            'denylist_type': str(self.denylist_type),
            'denylisting_moderator': self.denylisting_moderator
        }

    @classmethod
    def from_dict(cls, data: Dict) -> T:
        return cls(
            denylisted=data['denylisted'],
            denylist_reason=data['denylist_reason'],
            denylist_expiry=data['denylisted_expiry'],
            denylist_type=data['denylist_type'],
            denylisting_moderator=data['denylisting_moderator']
        )
