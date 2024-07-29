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
import time
import typing
import warnings
from asyncio import run

from helpful_modules.problems_module.errors import *
from helpful_modules.threads_or_useful_funcs import generate_new_id

from ..dict_convertible import DictConvertible
from .quiz_problem import QuizProblem
from .quiz_submissions import QuizSubmission, QuizSubmissionAnswer

# Licensed under GPLv3 (as all other code in this repository is)


class QuizSolvingSession(DictConvertible):
    def __init__(
        self, user_id: int, quiz_id: int, cache, guild_id: int, attempt_num: int
    ):
        self.user_id = user_id
        self.quiz_id = quiz_id
        self.special_id = generate_new_id()
        self.is_final = False
        self.answers: typing.Dict[int, QuizSubmissionAnswer] = {}
        self.start_time = time.time()
        self._quiz = self._get_quiz()
        self.guild_id = guild_id
        self.attempt_num = attempt_num

        try:
            self.expire_time: int = self.start_time + self._quiz.time_limit
        except AttributeError:
            raise NotImplementedError(
                "Quiz descriptions + other metadata needs to be fully implemented!"
            )

        # try:
        #    self.guild_id = self._quiz.guild_id
        # except MathProblemsModuleException as MPME:
        #    raise RuntimeError(
        #        "This quiz does not have a guild id, or it is None."
        #    ) from MPME

        self._reset()

    def _reset(self):
        """Reset myself"""
        pass

    def _get_quiz(self) -> "Quiz":
        """Get the quiz for this QuizSubmissionSession and return it"""
        raise NotImplementedError("This is being removed")

    def add_submission_answer(self, submission_answer: QuizSubmissionAnswer):
        """Add a submission answer to this session!"""
        problem_num = submission_answer.problem_id
        self.answers[problem_num] = submission_answer
        return submission_answer

    def _get_submission_answer(self, problem_num: int):
        """Get this submission answer or raise KeyError if it isn't found"""
        return self.answers[problem_num]

    @property
    def overtime(self: "QuizSolvingSession") -> bool:
        return time.time() > self.expire_time

    @property
    def is_finished(self: "QuizSolvingSession"):
        return self.overtime

    @classmethod
    def better_init(
        cls,
        *,
        user_id: int,
        quiz_id: int,
        cache,
        is_finished: bool,
        answers: typing.List[QuizSubmissionAnswer],
        guild_id: int,
        start_time: int,
        expire_time: int,
        special_id: int
    ) -> "QuizSolvingSession":
        QuizSession: "QuizSolvingSession" = cls(
            cache=cache, quiz_id=quiz_id, user_id=user_id
        )
        QuizSession.is_finished = is_finished
        QuizSession.answers = answers
        QuizSession.guild_id = guild_id
        QuizSession._quiz = run(cache.get_quiz(quiz_id))
        QuizSession.start_time = start_time
        QuizSession.expire_time = expire_time
        QuizSession.special_id = special_id
        return QuizSession

    @classmethod
    def from_sqlite_dict(cls, dict: dict) -> "QuizSolvingSession":
        """Convert a dict returned from sql into a QuizSolvingSession"""
        return cls.better_init(
            start_time=dict["start_time"],
            expire_time=dict["expire_time"],
            user_id=dict["user_id"],
            quiz_id=dict["quiz_id"],
            guild_id=dict["guild_id"],
            answers=list(
                map(QuizSubmissionAnswer.to_dict, dict["answers"])
            ),  # TODO: don't use pickle because RCE
            special_id=dict["special_id"],
            attempt_num=dict["attempt_num"],
        )

    @classmethod
    def from_mysql_dict(cls, dict: dict) -> "QuizSolvingSession":
        return cls.better_init(
            start_time=dict["start_time"],
            user_id=dict["user_id"],
            quiz_id=dict["quiz_id"],
            guild_id=dict["guild_id"],
            expire_time=dict["expire_time"],
            is_finished=dict["is_finished"],
            answers=dict["answers"],
            special_id=dict["special_id"],
            attempt_num=dict["attempt_num"],
        )

    def to_dict(self) -> dict:
        return {
            "start_time": self.start_time,
            "user_id": self.user_id,
            "quiz_id": self.quiz_id,
            "guild_id": self.guild_id,
            "expire_time": self.expire_time,
            "is_finished": self.is_finished,
            "answers": [answer.to_dict() for answer in self.answers.values()],
        }

    async def update_self(self):
        """Update myself in SQL"""
        raise NotImplementedError("THIS IS BEING REMOVED!")

    def add_answer(self, answer_to_add: QuizSubmissionAnswer):
        """Add an answer"""
        if self.editable:
            raise QuizSessionOvertimeException("Quiz session overtime")
        assert isinstance(answer_to_add, QuizSubmissionAnswer)
        try:
            self.answers[answer_to_add.problem_id] = answer_to_add
        except IndexError:
            raise MathProblemsModuleException("Question number out of range")

        warnings.warn(DeprecationWarning, "You need to update it manually now")

    @property
    def editable(self):
        return (not self.overtime) and (not self.is_final)

    def modify_answer(self, new_answer: QuizSubmissionAnswer, index: int):
        if self.editable:
            raise QuizSessionOvertimeException("Quiz session overtime")

        assert isinstance(new_answer, QuizSubmissionAnswer)
        try:
            self.answers[new_answer.problem_id] = new_answer
        except IndexError:
            raise MathProblemsModuleException("Question number out of range")
        warnings.warn(DeprecationWarning, "You need to update it manually now")

    def get_answer(self, index: int) -> "QuizSubmissionAnswer":
        try:
            return self.answers[index]
        except IndexError:
            raise IndexError("There is no such index")
