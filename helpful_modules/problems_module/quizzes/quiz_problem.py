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
import sqlite3
import sys
import traceback
from typing import *

from helpful_modules.problems_module import BaseProblem

from ..dict_convertible import DictConvertible


class QuizProblem(BaseProblem, DictConvertible):
    """A class that represents a Quiz Math Problem"""

    def __init__(
        self,
        question: str,
        id: int,
        author: int,
        answer: str = "",
        guild_id: int = None,
        voters: List[int] = None,
        solvers: List[int] = None,
        cache=None,
        answers: List[str] = None,
        is_written: bool = False,
        quiz_id: int = None,
        max_score: int = -1,
        quiz=None,
    ):
        """A method that allows the creation of new QuizMathProblems"""
        if not isinstance(quiz, Quiz):
            raise TypeError(
                f"quiz is of type {quiz.__class.__name}, not Quiz"
            )  # Here to help me debug
        if voters is None:
            voters = []
        if solvers is None:
            solvers = []
        if answers is None:
            answers = []
        super().__init__(
            question, answer, id, author, guild_id, voters, solvers, cache, answers
        )  #
        self.is_written = is_written
        if quiz is not None:
            self.quiz_id = quiz.id
        else:
            self.quiz_id = quiz_id
        self.max_score = max_score
        self.min_score = 0
        self.cache = cache

    @property
    def quiz(self):
        """Return my quiz"""
        if self.cache is None:
            return None  # I don't have a cache to get my quiz from!
        else:
            return self.cache.get_quiz(self.quiz_id)

    async def edit(
        self,
        question=None,
        answer=None,
        id=None,
        guild_id=None,
        voters=None,
        solvers=None,
        author=None,
        answers=None,
        is_written=None,
        quiz=None,
        max_score: int = -1,
    ):
        """Edit a problem!"""
        await super().edit(
            question, answer, id, guild_id, voters, solvers, author, answers
        )
        if not isinstance(quiz, Quiz):
            raise TypeError(
                f"quiz is of type {quiz.__class.__name}, not Quiz"
            )  # Here to help me debug
        if not isinstance(is_written, bool) and is_written is not None:
            raise TypeError("is_written is not of type bool")
        else:
            self.quiz_id = quiz.id
        if max_score is not None:
            self.max_score = max_score
        if is_written is not None:
            self.is_written = is_written

        if self.cache:
            self.cache.update_quiz(self.quiz_id, quiz)
        await self.update_self()

    def to_dict(self, show_answer: bool = False):
        d = {
            "type": "QuizMathProblem",
            "question": self.question,
            "id": str(self.id),
            "guild_id": str(self.guild_id),
            "voters": self.voters,
            "solvers": self.solvers,
            "author": self.author,
            "quiz_id": self.quiz_id,
            "is_written": self.is_written,
            "max_score": self.max_score,
        }
        if show_answer:
            d["answer"] = self.answers
        return d

    @classmethod
    def from_dict(cls, _dict: dict, cache=None):
        """Convert a dictionary to a QuizProblem. Even though the bot uses SQL, this is used in the from_row method"""
        _dict.pop("type")
        return cls(**_dict, cache=cache)

    @classmethod
    def from_row(cls, row: dict, cache=None):
        if isinstance(row, sqlite3.Row):
            raise TypeError("Oh no.")
        try:
            _dict = {
                "quiz_id": row["quiz_id"],
                "guild_id": row["guild_id"],
                "voters": row["voters"],
            }
            return cls.from_dict(_dict, cache=cache)
        except BaseException as e:
            traceback.print_exception(
                type(e), e, e.__traceback__, file=sys.stderr
            )  # Log to stderr
            raise MathProblemsModuleException(
                "Oh no... conversion from row failed"
            ) from e  # Re-raise (which wil log)

    async def update_self(self):
        """Update myself"""
        raise DeprecationWarning("THis is being deprecated")
        # if self.cache is not None:
        #    await self.quiz.update_self()
