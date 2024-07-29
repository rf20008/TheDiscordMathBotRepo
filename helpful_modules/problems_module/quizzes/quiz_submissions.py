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
from dataclasses import dataclass
from typing import Dict, Optional, Union
from warnings import warn

from ...threads_or_useful_funcs import assert_type_or_throw_exception
from ..dict_convertible import DictConvertible
from ..errors import MathProblemsModuleException


@dataclass
class QuizSubmissionAnswer:
    """A class that represents an answer for a singular problem. This also has metadata."""

    answer: str
    problem_id: Optional[int]
    quiz_id: int
    grade: int

    def __init__(
        self, answer: str = "", problem_id: Optional[int] = None, quiz_id: int = -1
    ):
        """
        Initialize a QuizSubmissionAnswer.
        Parameters
        ----------
        answer : str
            The actual answer to the problem
        problem_id : Optional[int]
            The id of the problem that this QuizSubmissionAnswer is attached to
        quiz_id: int
            The ID of the Quiz that this QuizSubmissionAnswer is attached to

        Raises
        ----------
        TypeError
            You didn't provide an argument of the correct type.
        """
        assert_type_or_throw_exception(answer, str)
        assert_type_or_throw_exception(problem_id, int)
        assert_type_or_throw_exception(quiz_id, int)
        self.answer = answer
        self.problem_id = problem_id
        self.grade = 0
        self.quiz_id = quiz_id

    def set_grade(self, grade):
        self.grade = grade

    def __str__(self):
        return f"<QuizSubmission quiz_id = {self.quiz_id} answer = {self.answer} grade = {self.grade}>"


class QuizSubmission(DictConvertible):
    """A class that represents someone's submission to a graded quiz"""

    mutable: bool
    user_id: Optional[int]
    quiz_id: Optional[int]
    answers: Dict[int, QuizSubmissionAnswer]

    def __init__(self, user_id: int, quiz_id: int):  # type: ignore
        """
        Generate a QuizSubmission given the parameters given!
        Parameters
        ----------
        user_id : py:class:int
            The ID of the user who made the QuizSubmission
        quiz_id : py:class:int
            The ID of the quiz that this QuizSubmission is attached to
        cache : class:MathProblemCache
            The MathProblemCache that
        """
        self.user_id = user_id
        self.quiz_id = quiz_id
        self.mutable = True
        self.answers = (
            {}
        )  # todo: fix the quiz commands to make it a list of QuizSubmissionAnswer(problem_id=quiz_id, guild_id=guild_id
        # with a number

    @property
    def quiz(self):
        """
        Return my quiz!
        (This has been removed since version v0.0.9a!)
        Returns
        ----------
        Quiz
            This is the quiz that t"""
        warnings.warn(
            message="This function has been deprecated! You must use get_my_quiz (which is also deprecated for type-hinting purposes)",
            category=DeprecationWarning,
        )
        raise MathProblemsModuleException("This function is not usable!")

    async def get_my_quiz(self):
        """Return my Quiz! This function is deprecated for type-hinting purposes.
        To escape this deprecation, you normally have the associated `MathProblemCache` (we have it in so many places, probably in the bot.cache), so you can use
        ```py
        # c is the cache we have
        # item is the QuizSubmission we are using
        quiz = await c.get_quiz(item.quiz_id)
        ```
        Returns
        ----------
        Quiz
            Returns the quiz that is associated with this!."""
        raise NotImplementedError("This function is removed!")

    def set_answer(self, problem_id: int, answer: str) -> None:
        """Set the answer of a quiz submission
        Parameters
        ----------
        problem_id : int
            The ID of the problem that the answer corresponds to.
        answer : str
            The actual answer that this submission is sent to

        NOTE THAT THIS DOES NOT CHANGE THE ACTUAL DATABASE! YOU MUST DO IT YOURSELF. <! # todo: make this a note >
        """
        if not self.mutable:
            raise RuntimeError("This instance is not mutable")
        self.answers[problem_id].answer = answer

    def to_dict(self):
        t = {
            "mutable": self.mutable,
            "quiz_id": self.quiz_id,
            "user_id": self.user_id,
            "answer": [],
        }
        for answer in self.answers:
            t["answer"].append(
                {"problem_id": answer.problem_id, "answer": answer.answer}
            )
        return t

    @classmethod
    def from_dict(cls, dict_, cache) -> "QuizSubmission":
        """Convert a dictionary into a QuizSubmission"""
        c = cls(user_id=dict_["user_id"], quiz_id="quiz_id", cache=cache)
        for answer in dict_["answers"]:
            c.answers.append(
                QuizSubmissionAnswer(answer["answer"], problem_id=answer["problem_id"])
            )
        c.mutable = dict_["mutable"]
        return c

    async def submit(
        self,
    ) -> True:  # type: ignore
        raise NotImplementedError("This function doesn't do anything!")
