"""
The Discord Math Problem Bot Repo - DictConvertible
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

from typing import Dict, Protocol, TypeVar

from .errors import FormatException

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
    def from_dict(cls, data: Dict) -> T:
        ...

    def to_dict(self) -> Dict:
        ...
