"""
You can distribute any version of the Software created and distributed *before* 23:17:55.00 July 28, 2024 GMT-4
under the GNU General Public License version 3 or at your option, any  later option.
But versions of the code created and/or distributed *on or after* that date must be distributed
under the GNU *Affero* General Public License, version 3, or, at your option, any later version.

TheDiscordMathProblemBotRepo - DictConvertible

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

from typing import Dict, Protocol, TypeVar

from .errors import OwnershipNotDeterminableException

T = TypeVar("T")


class DictConvertible(Protocol):
    """
    A protocol for types that can be converted to and from dictionaries.

    Subclasses must implement the following methods:
    - `from_dict(cls, data: Dict) -> T`: Create an instance from a dictionary.
    - `to_dict(self) -> Dict`: Convert an instance to a dictionary.
    They must be inverse functions.
    More formally, the following constraint should hold for all instances and dictionaries:
    - For every instance `x` such that `isinstance(x,T)` is True, `T.from_dict(x.to_dict()) == x` must hold.
    - For every dictionary `D` such that `T.from_dict(D)` is defined, the following must hold:
        T.from_dict(D).to_dict() == D
    Throw a FormatException if either function is undefined.
    """

    @classmethod
    def from_dict(cls, data: Dict) -> T: ...

    def to_dict(self) -> Dict: ...

    def belongs_to_user(self, user_id: int):
        """
        Check if this object belongs to a specific user identified by user_id.

        Args:
        - user_id (int): The ID of the user to check ownership against.

        Returns:
        - bool: True if the object belongs to the specified user, False otherwise.

        Raises:
        - OwnershipNotKnownError: If the ownership cannot be determined from the object's dictionary representation.
        """
        self_dict = self.to_dict()
        if self_dict.get("user_id") is not None:
            return self_dict.get("user_id") == user_id
        elif self_dict.get("author") is not None:
            return self_dict.get("author") == user_id
        elif self_dict.get("authors") is not None:
            return user_id in self_dict.get("authors")
        else:
            raise OwnershipNotDeterminableException(
                f"I could not determine whether this object belongs to the user with user id {user_id}"
            )
    def __repr__(self):
        return repr(self.to_dict())