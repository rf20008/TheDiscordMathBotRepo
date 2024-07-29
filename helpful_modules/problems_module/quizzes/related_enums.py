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
import enum
from dataclasses import dataclass
from typing import Dict

# This isn't really used, but it's licensed under AGPLv3
DEFAULT_LICENSE = """This quiz is licensed under a license that allows:
- TheDiscordMathProblemBot to do the processing required with this quiz
- everyone to see the quiz
- everyone to interact with it, including voting for it, trying to solve it, voting against it and talking about it.
- everyone to see its solutions
- Discord to do the processing required with this quiz, and the ability for Discord to follow its Terms of Service, Community Guidelines, Privacy Policy, and other related documents,

but nothing else.
Also, the text of this license is copyrighted by @rf20008 on Github, but is released under the AGPLv3 or any later version (at your option).
"""


class QuizIntensity(float, enum.Enum):
    """An enumeration of quiz"""

    IMPOSSIBLE = float("inf")
    ONLY_GENIUSES_CAN_SOLVE_THIS = 200 << 100
    EXTREMELY_CHALLENGING = 10000.0
    EXTREMELY_HARD = 5000.0
    VERY_HARD = 2000.0
    CHALLENGING = 1000.0
    HARD = 500.0
    MEDIUM_HARD = 400.0
    MEDIUM = 300.0
    BETWEEN_EASY_AND_MEDIUM = 200.0
    EASY = 100.0
    VERY_EASY = 50.0
    VERY_VERY_EASY = 25
    TRIVIAL = 0
    CUSTOM = -1
    TOO_EASY = -float("inf")


class QuizTimeLimit(int, enum.Enum):
    CUSTOM = -1
    ONE_SECOND = 1
    THIRTY_SECONDS = 30
    FORTY_FIVE_SECONDS = 45
    ONE_MINUTE = 60
    FIVE_MINUTES = 300
    TEN_MINUTES = 600
    FIFTEEN_MINUTES = 900
    ONE_THOUSAND_SECONDS = 1000
    SEVENTEEN_MINUTES_AND_THIRTY_SECONDS = 1050
    TWENTY_MINUTES = 1200
    THIRTY_MINUTES = 1800
    TWO_THOUSAND_SECONDS = 2000
    TWO_THOUSAND_AND_TWENTY_TWO_SECONDS = 2022
    FORTY_MINUTES = 2400
    ONE_HOUR = 3600
    SEVENTY_FIVE_MINUTES = 4500
    ONE_AND_A_HALF_HOURS = 5400
    ONE_HUNDRED_FIVE_MINUTES = 6300
    TWO_HOURS = 7200
    TWO_AND_A_HALF_HOURS = 9000
    THREE_HOURS = 10800
    FOUR_HOURS = 14400
    ONE_DAY = 86400
    ONE_WEEK = 604800
    NO_LIMIT = 1 << 100
    UNLIMITED = 1 << 100


## @dataclass()
## class QuizDescription:
##    license: str = DEFAULT_LICENSE,
##    time_limit: QuizTimeLimit
##    intensity: QuizIntensity
##    string_description: str = "The author of this quiz did not add a description"
##
##    def to_dict(self) -> Dict[str, str]:
##        """Convert this instance into a dictionary."""
##        return {
##            "license": self.license,
##            "time_limit": self.time_limit.value,
##            "intensity": self.intensity.value,
##            "string_description": self.string_description,
##        }
##
##    @classmethod
##    def from_dict(cls, data: Dict[str, str]) -> "QuizDescription":
##        """Create an instance from a dictionary."""
##        return cls(
##            license=data.get("license", DEFAULT_LICENSE),
##            time_limit=QuizTimeLimit(data.get("time_limit", "")),
##            intensity=QuizIntensity(data.get("intensity", "")),
##            string_description=data.get("string_description", ""),
##        )
