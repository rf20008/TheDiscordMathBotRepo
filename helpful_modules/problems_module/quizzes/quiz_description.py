"""
You can distribute any version of the Software created and distributed *before* 23:17:55.00 July 28, 2024 GMT-4
under the GNU General Public License version 3 or at your option, any  later option.
But versions of the code created and/or distributed *on or after* that date must be distributed
under the GNU *Affero* General Public License, version 3, or, at your option, any later version.

This file is part of The Discord Math Problem Bot Repo

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
import typing as t
from dataclasses import dataclass

from .related_enums import DEFAULT_LICENSE
from ..dict_convertible import DictConvertible
from ..errors import FormatException
from .related_enums import QuizIntensity, QuizTimeLimit


@dataclass
class QuizDescription(DictConvertible):
    """A dataclass that holds quiz description"""

    category: str
    intensity: t.Union[QuizIntensity, int]
    description: str
    license: str
    time_limit: t.Union[int, QuizTimeLimit]
    guild_id: int
    author: int

    def __init__(
        self,
        *,
        cache: "MathProblemCache",
        quiz_id: int,
        author: int,
        guild_id: int,
        category: str = "Unspecified",
        intensity: t.Union[QuizIntensity, float] = QuizIntensity.IMPOSSIBLE,
        description="No description given",
        license: str = DEFAULT_LICENSE,
        time_limit=QuizTimeLimit.UNLIMITED
    ):
        self.guild_id = guild_id
        self.author = author
        self.quiz_id = quiz_id
        self.cache = cache
        self.category = category
        self.intensity = intensity
        self.description = description
        self.license = license
        self.time_limit = time_limit

    @classmethod
    def from_dict(cls, data: dict) -> "QuizDescription":
        try:
            return cls(
                author=data["author"],
                quiz_id=data["quiz_id"],
                category=data["category"],
                intensity=data["intensity"],
                description=data["description"],
                license=data["license"],
                time_limit=data["timelimit"],
                guild_id=data["guild_id"],
            )
        except KeyError as ke:
            raise FormatException("Bad formatting!") from ke

    @property
    def id(self):
        return self.quiz_id + self.author

    def to_dict(self):
        return {
            "author": self.author,
            "quiz_id": self.quiz_id,
            "category": self.category,
            "intensity": self.intensity,
            "description": self.description,
            "license": self.license,
            "time_limit": self.license,
            "guild_id": self.guild_id,
        }
