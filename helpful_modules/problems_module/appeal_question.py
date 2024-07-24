"""
This file is part of The Discord Math Problem Bot Repo

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
from typing import Dict

import orjson
from disnake.ui import TextInput
from disnake import TextInputStyle
from .dict_convertible import DictConvertible
from .errors import TooLongQuestion, OwnershipNotDeterminableException, FormatException
from ..threads_or_useful_funcs import generate_custom_id
from .appeal import AppealType

MAX_QUESTION_LENGTH = 45
MAX_CHAR_LIMIT = 4000
MAX_DESCRIPTION_LIMIT = 0


APPEAL_QUESTION_TYPE_NAMES = {
    AppealType.DENYLIST_APPEAL: "user_denylist",
    AppealType.GUILD_DENYLIST_APPEAL: "guild_denylist",
    AppealType.SUPPORT_SERVER_BAN: "support_server_ban",
    AppealType.SUPPORT_SERVER_MISC_PUNISHMENT: "support_server_misc_punishment",
    AppealType.NOT_SET: "not_set",
    AppealType.UNKNOWN: "unknown"
}

class AppealQuestion(DictConvertible):
    question: str
    char_limit: int
    long_prompt: str
    style: TextInputStyle
    def __init__(self, question: str, char_limit: int = -1, long_prompt: str = "Answer the question to the best of your abilities.", style: int | TextInputStyle = TextInputStyle.long):

        if not isinstance(question, str):
            raise TypeError("Your question is not actually a str")

        if len(question) > MAX_QUESTION_LENGTH:
            raise TooLongQuestion(f"Your question {question} is too long")
        self.question = question

        if char_limit == -1:
            char_limit = MAX_CHAR_LIMIT
        if not isinstance(char_limit, int):
            raise TypeError("char_limit is not actually an int")
        if char_limit > MAX_CHAR_LIMIT:
            raise ValueError(f"The character limit you specified is {char_limit} but the maximum character limit allowed is {MAX_CHAR_LIMIT}")
        if char_limit < 0:
            raise ValueError("Maximum character limit must be positive")
        self.char_limit = char_limit

        if not isinstance(long_prompt, str):
            raise TypeError("long_prompt is not actually a str")
        self.long_prompt = long_prompt

        if not isinstance(style, (int, TextInputStyle)):
            raise TypeError("style is not a TextInputStyle")

        if isinstance(style, int):
            self.style = TextInputStyle(style)
        else:
            self.style = style

    def belongs_to_user(self, user_id: int):
        raise OwnershipNotDeterminableException("Appeal questions do not belong to anyone")

    @classmethod
    def from_dict(cls, data: Dict) -> "AppealQuestion":
        try:
            return cls(
                question=data.get('question'),
                char_limit=data.get("char_limit"),
                long_prompt=data.get("long_prompt"),
                style=data.get("style")
            )
        except KeyError as err:
            raise FormatException("One or more fields are missing") from err
        except (TypeError, ValueError) as err:
            raise FormatException("This is an invalid question!!!") from err

    def to_dict(self) -> Dict:
        return {
            "question": self.question,
            "char_limit": self.char_limit,
            "long_prompt": self.long_prompt,
            "style": int(self.style)
        }
    def to_textinput(self) -> TextInput:
        return TextInput(
            label=self.question,
            custom_id=generate_custom_id(),
            style=self.style,
            max_length=self.char_limit
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AppealQuestion):
            return False
        return (self.question == other.question and
                self.char_limit == other.char_limit and
                self.long_prompt == other.long_prompt and
                self.style == other.style)

    def __hash__(self) -> int:
        return hash((self.question, self.char_limit, self.long_prompt, self.style))