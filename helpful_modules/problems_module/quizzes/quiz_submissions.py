from dataclasses import dataclass
from typing import Union, Optional, Dict
from ....threads_or_useful_funcs import assert_type_or_throw_exception
from ..errors import MathProblemsModuleException
from warnings import warn

@dataclass
class QuizSubmissionAnswer:
    """A class that represents an answer for a singular problem. This also has metadata."""
    answer: str
    problem_id: Optional[int]
    quiz_id: int
    grade: int

    def __init__(self, answer: str = "", problem_id: Optional[int] = None, quiz_id: int = -1):
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


class QuizSubmission:
    """A class that represents someone's submission to a graded quiz"""
    mutable: bool
    user_id: Optional[int]
    cache: "MathProblemCache" # type: ignore
    quiz_id: Optional[int]
    answers: Dict[int, QuizSubmission]

    def __init__(self, user_id: int, quiz_id: int, cache: "MathProblemCache"): # type: ignore
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
        self.answers = {
            question.id: QuizSubmissionAnswer(problem_id=question.id, quiz_id=quiz_id)
            for question in self.get_my_quiz()
        }
        self.cache = cache

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
            category = DeprecationWarning
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
        return await self.cache.get_quiz(self.quiz_id)

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

    def submit(self, cache: "MathProblemCache") -> True: # type: ignore

        self.mutable = False
        if self in self.quiz.submissions:
            raise QuizAlreadySubmitted
        quiz = await self.cache.get_quiz()
        return True
