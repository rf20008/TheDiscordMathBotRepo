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
import typing
from typing import List

from helpful_modules.problems_module import BaseProblem

from ..dict_convertible import DictConvertible
from ..errors import *
from .quiz_description import QuizDescription
from .quiz_problem import QuizProblem
from .quiz_submissions import QuizSubmission
from .QuizSolvingSession import QuizSolvingSession
from .related_enums import QuizIntensity, QuizTimeLimit

MAX_PROBLEMS_PER_QUIZ = 100  # todo: lower it - character limits


class Quiz(list, DictConvertible):
    """Represents a quiz.
    but it has an additional attribute submissions which is a list of QuizSubmissions"""

    def __init__(
        self,
        id: int,
        authors: List[int],
        quiz_problems: List[QuizProblem],
        category: QuizIntensity = None,
        description: QuizDescription = None,
    ) -> None:
        super().__init__()
        """Create a new quiz. id is the quiz id and iter is an iterable of QuizMathProblems"""
        assert isinstance(authors, list)
        assert all([isinstance(author, int) for author in authors])
        self.description = description
        self._time_limit = description.time_limit
        self.license = description.license
        self.intensity = description.intensity
        self.category = category
        self.authors = authors
        self.problems = quiz_problems
        self.sort(key=lambda problem: problem.id)

        self._id = id

    def add_submission(self, submission: QuizSubmission):
        """Add a submission to this quiz. Note that this does not
        automatically update the cache -- you have to do it yourself.
        Time complexity: O(1)
        :param submission: the submission
        :raises NotImplementedError: This function is deliberately left unimplemented - add submissions yourself
        """
        raise NotImplementedError(
            "This function is deliberately left unimplemented - add submissions yourself"
        )

    def add_problem(
        self, problem: QuizProblem, insert_location: typing.Optional[int] = None
    ):
        """Add a problem to this quiz."""
        if len(self.problems) + 1 > MAX_PROBLEMS_PER_QUIZ:
            raise TooManyProblems(
                f"""There is already the maximum number of problems on this quiz. Therefore, adding a new problem is prohibited... 
            Because this is a FOSS bot, there is no premium version and thus no way to increase the number of problems you can have on a quiz!
            If you want to increase it, you can, if you self-host this bot :)"""
            )
        if insert_location is None:
            insert_location = len(self.problems) - 1
        assert isinstance(problem, QuizProblem)  # Type-checking
        self.problems.insert(problem, insert_location)

    @property
    def quiz_problems(self):
        return self.problems

    @property
    def submissions(self):
        raise AttributeError(
            "This property is being removed! Please use redis to get them..."
        )

    @property
    def id(self):
        return self._id

    @property
    def guild_id(self):
        if self.empty:
            raise MathProblemsModuleException("This quiz is empty!")
        return self.problems[0].guild_id

    @property
    def empty(self) -> bool:
        return len(self.problems) == 0 and len(self.submissions) == 0

    @classmethod
    def from_dict(cls, _dict: dict):
        problems_as_type = list(map(QuizProblem.from_dict, _dict["problems"]))
        submissions = list(map(QuizSubmission.from_dict, _dict["submissions"]))
        problems_as_type.sort(key=lambda problem: problem.id)
        authors = _dict["authors"]
        description = QuizDescription.from_dict(_dict["description"])
        c = cls(
            quiz_problems=problems_as_type,
            id=_dict["id"],
            description=description,
            authors=authors,
        )  # type: ignore
        c.description = description
        c._submissions = submissions
        c._id = _dict["id"]
        return c

    def to_dict(self) -> dict:
        """Convert this instance into a Dictionary!"""
        problems = [problem.to_dict() for problem in self.problems]
        submissions = [submission.to_dict for submission in self.submissions]
        return {
            "problems": problems,
            "submissions": submissions,
            "id": self._id,
            "description": self.description.to_dict(),
            "authors": self.authors,
        }

    async def update_self(self):
        """Update myself!"""
        raise NotImplementedError("Please update this cache yourself!")

    @classmethod
    def from_data(
        cls,
        problems: typing.List[QuizProblem],
        authors: typing.List[int],
        existing_sessions: typing.List[QuizSolvingSession],
        submissions: typing.List[QuizSubmission],
        cache: "MathProblemCache",
    ):
        return cls(
            quiz_problems=problems,
            authors=authors,
            existing_sessions=existing_sessions,
            submissions=submissions,
            cache=cache,
        )  # type: ignore
