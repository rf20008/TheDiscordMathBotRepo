import asyncio
import json
import typing
import warnings
from io import BytesIO

import disnake
from disnake.ext import commands

from helpful_modules import checks, problems_module
from helpful_modules.custom_bot import TheDiscordMathProblemBot
from helpful_modules.custom_embeds import ErrorEmbed, SuccessEmbed
from helpful_modules.problems_module import *
from helpful_modules.problems_module import MathProblemCache, Quiz, QuizProblem
from helpful_modules.problems_module.quizzes import (
    QuizDescription,
    QuizSolvingSession,
    QuizSubmission,
)
from helpful_modules.problems_module.quizzes.related_enums import (
    QuizIntensity,
    QuizTimeLimit,
)
from helpful_modules.threads_or_useful_funcs import generate_new_id, get_log

from ..helper_cog import HelperCog


class CreatingQuizzesCommandsCog(HelperCog):
    def __init__(self, bot: TheDiscordMathProblemBot):
        super().__init__(bot)
        self.bot = bot
        self.cache = bot.cache

    @checks.has_privileges(denylisted=False)
    @commands.slash_command(
        name="create",
        description="Create a quiz!",
    )
    async def create(self, inter: disnake.ApplicationCommandInteraction) -> None:
        """The base command to create a quiz. This has subcommands.

        Usage:
        /quiz create from_json [json: str]
        Creates a quiz from JSON. I suggest you do not use this.
        /quiz create blank
        Creates a blank quiz."""

    @checks.has_privileges(denylisted=False)
    @create.sub_command(
        name="from_json",
        description="Create a quiz from JSON.",
        options=[
            disnake.Option(
                name="data",
                description="The data (JSON) to convert into a quiz.",
                required=True,
                type=disnake.OptionType.string,
            )
        ],
    )
    async def from_json(
        self, inter: disnake.ApplicationCommandInteraction, data: str
    ) -> None:
        """/quiz create from_json [json: str]
        Create a Quiz from JSON. This is not user-friendly, but it's quick.

        Structure:
        Quiz Problem: list of quiz problem objects. This order will determine the order of the problems in the quiz.
        guild_id: guild id for the quiz. This guild id must be one of the guilds that you share with this bot or `null` for a global quiz. You must specify this or it will fail!
        -------
        Quiz problem:
        legend: key | value type | description
        --------
        question | string | The question to ask the user in this question
        answer | List[string] | The acceptable answers. This is a list of strings.
        points | int | The number of points this problem is worth.
        is_written | boolean (either `true` or `false`) | whether this problem is a written problem. Cannot be used with the `answers` parameter.
        ------
        """

        # Must parse into list
        # If parsing fails, tell the user.

        try:
            _data: dict = json.loads(data)
        except json.JSONDecodeError as e:
            return await inter.send(
                f"""You didn't provide valid JSON, so I don't understand what you mean 

    JSON error: {e}"""
            )
        try:
            guild_id, problems = _data["guild_id"], _data["Quiz Problems"]
        except KeyError:
            return await inter.send(
                "Error: Could not decode guild_id or problems from the given dictionary. You probably copy-pasted something else."
            )
        if not isinstance(problems, list):
            return await inter.send("Problems must be a list.")

        if not isinstance(guild_id, int) or guild_id is None:
            return await inter.send("guild_id must either be an integer or None.")
        if guild_id not in [guild.id for guild in inter.author.mutual_guilds]:
            return await inter.send(
                "You cannot create this quiz because either you or I are not in the guild that you're trying to create the quiz for."
            )
        real_problems: typing.List[QuizProblem] = []
        for problem_num in range(len(problems)):
            problem = problems[problem_num]
            # parse the problem
            if not isinstance(problem, dict):
                return await inter.send(f"Problem#{problem_num} isn't a dictionary.")
            has_answers: bool = "answers" in problem.keys()
            # Parse the question
            try:
                question = problem["question"]
                if not isinstance(question, str):
                    raise TypeError("Question is not a string")
            except KeyError:
                return await inter.send(
                    f"Invalid data - question missing for problem#{problem_num}"
                )
            except TypeError:
                return await inter.send(
                    f"Invalid data - question not a string for problem#{problem_num}"
                )

            # Parse the answer
            if has_answers:
                try:
                    answers: typing.List[str] = problem["answers"]
                    if not isinstance(answers, list):
                        return await inter.send(
                            f"Invalid data - Answers isn't a list (problem#{problem_num})"
                        )
                    for answer_num in range(len(answers)):
                        if not isinstance(answers[answer_num], str):
                            return await inter.send(
                                f"Invalid data - answer #{answer_num} in problem #{problem_num} isn't a string"
                            )
                except KeyError:
                    return await inter.send(
                        f"Invalid data - missing answers for problem #{problem_num}"
                    )
            else:
                answers = []
                try:
                    is_written: bool = problem["is_written"]
                    if not isinstance(is_written, bool):
                        return await inter.send(
                            f"Invalid data - is_written for problem #{problem_num} is not a boolean."
                        )
                except KeyError:
                    return await inter.send(
                        f"Invalid data - missing is_written and answer for problem#{problem_num}. Please try again!"
                    )

            # Parse the number of points this question is worth

            try:
                points: int = problem["points"]
                if not isinstance(points, int):
                    return await inter.send(
                        f"Invalid data -  problem#{problem_num}'s point worth isn't a integer"
                    )
            except KeyError:
                return await inter.send(
                    f"Invalid data - missing point worth for problem#{problem_num}"
                )

            real_problems.append(
                QuizProblem(
                    question=question,
                    answers=answers,
                    max_score=points,
                    cache=self.cache,
                    author=inter.author.id,
                    guild_id=guild_id,
                )
            )
        already_existing_quiz_ids = [
            _quiz.id
            for _quiz in await self.cache.get_quizzes_by_func(func=lambda _quiz: True)
        ]
        while True:
            id = generate_new_id()
            if id not in already_existing_quiz_ids:
                break

        quiz_to_create = Quiz(
            id=id,
            problems=real_problems,
            submissions=[],
            cache=self.cache,
            authors=[inter.author.id],
        )
        await self.cache.add_quiz(quiz_to_create)
        await inter.send("Quiz successfully created!")

    @checks.has_privileges(denylisted=False)
    @create.sub_command(name="blank", description="Create a blank quiz")
    async def blank(self, inter):
        """/quiz create blank
        Create a blank quiz. This is more user-friendly than /quiz create from_json, but it's slower!

        There is currently a bug. Don't use this because there is a bug that makes the quiz not actually be created because there are no problems.

        This command has been deprecated and will be removed in v1 in favor of /create with_existing_problem.
        """

        # TODO: only some people can create quizzes
        warnings.warn("This command has been deprecated", DeprecationWarning)
        already_existing_quiz_ids = [
            quiz.id
            for quiz in await self.cache.get_quizzes_by_func(func=lambda quiz: True)
        ]
        while True:
            id = generate_new_id()
            if id not in already_existing_quiz_ids:
                break
        quiz = Quiz(
            id=id,
            quiz_problems=[],
            submissions=[],
            authors=[inter.author.id],
            cache=self.cache,
        )
        # bug: empty quizzes cannot be added because they are empty
        # TODO: fix
        await self.bot.cache.add_quiz(quiz)
        await inter.send("Successfully created quiz!")

    @checks.has_privileges(denylisted=False)
    @create.sub_command(
        name="with_existing_problem",
        description="Create quizzes with existing problems",
        options=[
            disnake.Option(
                name="question",
                description="The question for the initial problem in the quiz to have",
                type=disnake.OptionType.string,
                required=True,
            ),
            disnake.Option(
                name="answer",
                description="The answer for this problem to have (not required if this is manually graded)",
                # TODO: SHORTEN!
                type=disnake.OptionType.string,
                required=False,
            ),
            disnake.Option(
                name="max_points",
                description="The maximum number of points this question is worth. Defaults to 100",
                type=disnake.OptionType.number,
                required=False,
            ),
            disnake.Option(
                name="is_written",
                description="Whether this problem is written (defaults to False)",
                type=disnake.OptionType.boolean,
                required=False,
            ),
        ],
    )
    async def with_existing_problem(
        self,
        inter: disnake.ApplicationCommandInteraction,
        question: str,
        answer: str = None,
        max_points: float = 100.0,
        is_written: bool = False,
    ):
        if answer is None and is_written is False:
            await inter.send(
                embed=ErrorEmbed(
                    "You must provide an answer or set is_written to True!"
                )
            )
            return
        if max_points < 0:
            return await inter.send(
                embed=ErrorEmbed("Quiz questions must be worth at least 0 points!")
            )
        problem: QuizProblem = QuizProblem(
            question=question,
            answer=answer,
            max_points=max_points,
            is_written=is_written,
        )
        await self.cache.update_cache()
        already_existing_quiz_ids = [quiz.id for quiz in self.cache.cached_quizzes]
        while True:
            quiz_id = generate_new_id()
            if quiz_id not in already_existing_quiz_ids:
                break
            else:
                continue

        quiz: Quiz = Quiz(
            authors=[inter.author.id],
            problems=[problem],
            id=quiz_id,
            submissions=[],
            existing_sessions=[],
            description=QuizDescription(
                author=inter.author.id,
                quiz_id=quiz_id,
                cache=self.cache,
                intensity=QuizIntensity.CUSTOM,
                time_limit=QuizTimeLimit.UNLIMITED,
                description="**This quiz has just been created; there is no description yet**",
                license="""** This quiz has just been created; there is no license yet. 
                By default, a license that allows the bot to process the quiz + allows people to solve the quiz, but doesn't allow people to copy it is used.
                **""",
                # TODO: add to ToS
                guild_id=inter.guild_id,
                solvers_can_view_quiz=True,
            ),
        )
        await self.bot.cache.add_quiz(quiz)


def setup(*args):
    pass
