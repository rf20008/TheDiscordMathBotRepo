"""
The Discord Math Problem Bot Repo - UserData
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

Author: Samuel Guo (64931063+rf20008@users.noreply.github.com)
"""

import time
from .denylistable import Denylistable


class UserData(Denylistable):
    """A dataclass to store user data for the bot!"""

    __slots__ = ('trusted', 'denylisted', 'user_id', 'denylist_expiry', 'denylist_reason')

    def __init__(
        self, *, user_id: int, trusted: bool = False, denylisted: bool = False, denylist_reason: str = "", denylist_expiry: float = 0.0
    ):
        if not isinstance(user_id, int):
            raise TypeError("user_id is not an integer")
        if not isinstance(trusted, bool):
            raise TypeError("trusted isn't a boolean")
        if not isinstance(denylisted, bool):
            raise TypeError("denylisted isn't a boolean")
        if not isinstance(denylist_reason, str):
            raise TypeError("denylist_reason isn't a str")
        if not isinstance(denylist_expiry, float):
            raise TypeError("denylist_expiry isn't a float")

        self.user_id = user_id
        self.trusted = trusted
        self.denylisted = denylisted
        self.denylist_reason = denylist_reason
        self.denylist_expiry = denylist_expiry

    @classmethod
    def from_dict(cls, dict: dict) -> "UserData":
        """Create UserData from a dictionary"""
        return cls(
            user_id=dict["user_id"],
            trusted=dict["trusted"],
            denylisted=dict["denylisted"],
            denylist_expiry=dict["denylist_expiry"],
            denylist_reason=dict["denylist_reason"]
        )

    def to_dict(self) -> dict:
        """Convert UserData to a dictionary"""
        return {
            "user_id": self.user_id,
            "trusted": self.trusted,
            "denylisted": self.denylisted,
            "denylist_expiry": self.denylist_expiry,
            "denylist_reason": self.denylist_reason
        }

    @classmethod
    def default(cls, user_id: int):
        """Return a default UserData instance"""
        return cls(user_id=user_id, trusted=False, denylisted=False, denylist_reason="", denylist_expiry=0.0)


