"""
You can distribute any version of the Software created and distributed *before* 23:17:55.00 July 28, 2024 GMT-4
under the GNU General Public License version 3 or at your option, any  later option.
But versions of the code created and/or distributed *on or after* that date must be distributed
under the GNU *Affero* General Public License, version 3, or, at your option, any later version.

This file is part of TheDiscordMathProblemBotRepo

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
import json
import typing

import disnake
from disnake.ext import commands

from helpful_modules import problems_module
from helpful_modules.custom_embeds import ErrorEmbed, SuccessEmbed
from helpful_modules.problems_module import *
from helpful_modules.problems_module import MathProblemCache, Quiz, QuizProblem
from helpful_modules.threads_or_useful_funcs import generate_new_id, get_log

from .helper_cog import HelperCog

log = get_log(__name__)


# Licensed under GPLv3 (or later)
# TODO: implement everything!


class QuizCog(HelperCog):
    """An incomplete cog which will eventually store all quiz-related commands"""

    def __init__(self, bot: disnake.ext.commands.Bot):
        super().__init__(bot)
        self.bot = bot
        self.cache: MathProblemCache = bot.cache
        # TODO: quiz commands :-)

    @commands.slash_command(
        name="quiz", description="Interact with a quiz. This has subcommands."
    )
    async def quiz(self, inter):
        """/quiz ...
        Interact with a quiz. This has subcommands.
        Usage:
        /quiz create from_json [json: str]
        Creates a quiz from JSON. I suggest you do not use this.
        /quiz create blank
        Create a blank quiz.
        """

    @quiz.sub_command_group(
        name="create",
        description="Create a quiz. However, interacting with quizzes has not been implemented!",
    )
    async def create(self, inter: disnake.ApplicationCommandInteraction) -> None:
        """The base command to create a quiz. This has subcommands.

        Usage:
        /quiz create from_json [json: str]
        Creates a quiz from JSON. I suggest you do not use this.
        /quiz create blank
        Creates a blank quiz."""

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

        # TODO: quiz creation rules: make it possible to ensure that only some people can create quizzes to prevent spam
        try:
            _data: dict = json.loads(data)
        except json.JSONDecodeError as e:
            return await inter.send(
                f"""You didn't provide valid JSON, so I don't understand what you mean :(

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
            quiz.id
            for quiz in await self.cache.get_quizzes_by_func(func=lambda quiz: True)
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

    @create.sub_command(name="blank", description="Create a blank quiz")
    async def blank(self, inter):
        """/quiz create blank
        Create a blank quiz. This is more user-friendly than /quiz create from_json, but it's slower!

        There is currently a bug. Don't use this because there is a bug that makes the quiz not actually be created because there are no problems.
        """

        # TODO: only some people can create quizzes
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

    @quiz.sub_command_group(name="edit", description="Edit quizzes")
    async def edit(self, inter: disnake.ApplicationCommandInteraction):
        """/quiz edit

        Edit quizzes

        Usage:
        /quiz edit add_problem (quiz_id: int) (insert_loc: int) (question: str) (answer1: str) [numPoints: int=1]
        /quiz edit add_answer (quiz_id: int) (problem_num: int) (answer: str)"""
        pass

    @commands.cooldown(1, 5, commands.BucketType.user)
    @edit.sub_command(
        name="add_answer",
        description="Add an answer to a quiz problem",
        options=[
            disnake.Option(
                name="quiz_id",
                description="The ID of the quiz that contains the problem to add the answer to",  # TODO: shorten
                type=disnake.OptionType.integer,
                required=True,
            ),
            disnake.Option(
                name="problem_num",
                description="The problem # to add the answer to",
                type=disnake.OptionType.integer,
                required=True,
            ),
            disnake.Option(
                name="answer",
                description="The answer to add",
                type=disnake.OptionType.string,
                required=False,
            ),
        ],
    )
    async def add_answer(
        self: "QuizCog",
        inter: disnake.ApplicationCommandInteraction,
        quiz_id: int,
        problem_num: int,
        answer: str,
    ):
        """/quiz edit add_answer (quiz_id: int) (problem_num: int) (answer: str)

        Add an answer to a quiz problem (found by getting the quiz with provided id and getting the problem from the quiz), provided you are the problem author.
        There is a 5-second cooldown!"""
        if problem_num < 0:
            await inter.send("Problem num must be greater than 0")
            return

        try:
            quiz = await self.bot.cache.get_quiz(quiz_id)
        except problems_module.QuizNotFound:
            await inter.send(embed=ErrorEmbed("Quiz not found!"))
            return

        try:
            problem = quiz.quiz_problems[problem_num]
        except IndexError:
            await inter.send(
                embed=ErrorEmbed(
                    f"The quiz with id {quiz_id} doesn't have a problem with id {problem_num}."
                )
            )
            return
        if not problem.is_author(inter.author):
            await inter.send("You aren't the author of this problem!")
            return

        if len(problem.answers) > self.cache.max_answers_per_problem:
            await inter.send("This problem has reached the maximum number of answers!")
            return
        problem.add_answer(answer)
        await inter.send("Successfully added an answer!")

    @commands.cooldown(1, 30, commands.BucketType.user)
    @edit.sub_command(
        name="add_problem",
        description="Add a problem to a quiz. You must be an author of the quiz to add a problem",  # TODO: shorten
        options=[
            disnake.Option(
                name="quiz_id",
                description="The ID of the quiz to add the problem to",
                type=disnake.OptionType.integer,
                required=True,
            ),
            disnake.Option(
                name="problem_to_insert_before",
                description="The problem to insert this question before. Defaults to the last question in the quiz.",
                type=disnake.OptionType.integer,
                required=True,
            ),
            disnake.Option(
                name="question",
                description="The question to ask in this problem",
                type=disnake.OptionType.string,
                required=True,
            ),
            disnake.Option(
                name="answer",
                description="A possible answer for this problem.",
                type=disnake.OptionType.string,
                required=False,
            ),
            disnake.Option(
                name="is_written",
                description="Whether this problem is a written problem and manually graded",  # TODO: shorten
                type=disnake.OptionType.boolean,
                required=False,
            ),
            disnake.Option(
                name="points",
                description="The number of points this question is worth. This must be greater than 0!",
                # TODO: shorten
                type=disnake.OptionType.number,
                required=False,
            ),
        ],
    )
    async def add_problem(
        self,
        inter: disnake.ApplicationCommandInteraction,
        quiz_id: int,
        problem_to_insert_before: int,
        question: str,
        answer: typing.Optional[str] = None,
        is_written: bool = False,
        points: typing.Optional[float] = 0.5,
        # ...
    ) -> None:
        """/quiz edit add_problem (quiz_id: int) (problem_to_insert_before: int) (question: str) [answer: str = None], [is_written: bool = False] [points: float = 0.5]
        Add a problem to a quiz. You must be an author of the quiz (which means that you are one of the people who created a problem for the quiz) to add the problem to the quiz.
        There is a 30-second cooldown on this to prevent spam!

        """
        if answer is None and is_written is False:
            return await inter.send(
                "You must provide an answer or make the problem a written problem!"
            )
        try:
            quiz: Quiz = await self.bot.cache.get_quiz(quiz_id)
        except QuizNotFound:
            return await inter.send("Quiz not found!")
        try:
            problem = QuizProblem(
                question=question,
                answers=[answer] if answer is not None else [],
                quiz=quiz,
                guild_id=quiz.guild_id,
                is_written=is_written,
                author=inter.author.id,
                voters=[],
                solvers=[],
                max_score=points,
                cache=self.cache,
            )
        except MathProblemsModuleException as e:
            if str(e) == "This quiz is empty!":
                return await inter.send(
                    "This quiz is empty! Please help me fix this bug!"
                )
            raise
        else:
            if inter.author.id not in quiz.authors:
                return await inter.send(
                    embed=ErrorEmbed(
                        "You don't have permission to add a problem to this quiz. :("
                    )
                )
            await quiz.add_problem(problem, problem_to_insert_before)
            return await inter.send("Successfully added the problem!")

    @commands.cooldown(1, 60, commands.BucketType.user)
    @edit.sub_command(
        name="delete_problem",
        description="Delete a problem in a quiz. You must be the author of it or be an admin to delete it.",
        options=[
            disnake.Option(
                name="quiz_id",
                description="The quiz id of the quiz that contains the problem that you want to delete",
                type=disnake.OptionType.integer,
                required=True,
            ),
            disnake.Option(
                name="problem_to_delete",
                description="The problem number of the problem you want to delete",
                type=disnake.OptionType.integer,
                required=True,
            ),
        ],
    )
    async def delete_problem(
        self,
        inter: disnake.ApplicationCommandInteraction,
        quiz_id: int,
        problem_to_delete: int,
    ):
        """/quiz edit delete_problem (quiz_id: int) (problem_to_delete: int)
        Delete a problem in a quiz, provided that you authored the problem, have the `Administrator` permission the guild, or are a trusted user.
        There is a 60-second cooldown on this command that is not reducible."""
        # First make sure the problem exists
        await inter.response.defer()
        try:
            quiz = await self.cache.get_quiz(quiz_id=quiz_id)
        except QuizNotFound:
            return await inter.send("Quiz not found.")

        try:
            problem = quiz.problems[problem_to_delete]  # Get the problem
            can_delete: bool = False

            # Check the permissions
            if inter.author.id == problem.author:
                can_delete = True
            elif inter.author.guild_permissions.administrator:
                can_delete = True

            if not can_delete:
                user_data: UserData = await self.bot.cache.get_user_data(
                    user_id=inter.author.id,
                    default=UserData(
                        trusted=False, denylisted=False, user_id=inter.author.id
                    ),
                )
                if user_data.trusted:
                    can_delete = True

                if can_delete:
                    # They have permissions to delete
                    # Firstly, I need to shift it all 1 down after
                    for problem_num in range(problem_to_delete, len(quiz.problems), 1):
                        problem_num.id -= 1  # This has to be done or there will be skips and that will be bad
                    del quiz.problems[problem_to_delete]
                    await quiz.update_self()
                    await inter.send(
                        embed=SuccessEmbed("Successfully deleted the problem!")
                    )
                    return
                else:
                    return await inter.send(
                        embed=ErrorEmbed(
                            "You don't have permission to delete this problem!"
                        )
                    )
        except IndexError:
            return await inter.send("This problem in the quiz was not found.")

    @edit.sub_command(
        name="modify_problem",
        description="Modify a problem, changing its question/answer/point worth/etc...",
        options=[
            disnake.Option(
                name="quiz_id",
                description="The ID of the quiz that contains the problem to change!",
                type=disnake.OptionType.integer,
                required=True,
            ),
            disnake.Option(
                name="problem_num",
                description="The problem number to change in the quiz",
                type=disnake.OptionType.integer,
                required=True,
            ),
            disnake.Option(
                name="new_question",
                description="The new question to have",
                type=disnake.OptionType.string,
                required=False,
            ),
            disnake.Option(
                name="new_answer",
                description="The new answer to replace the already existing answers with!",
                type=disnake.OptionType.string,
                required=False,
            ),
            disnake.Option(
                name="points_worth",
                description="The new number of points this problem will be worth",
                type=disnake.OptionType.integer,
                required=False,
            ),
            disnake.Option(
                name="is_written",
                description="Whether the problem will be written or not!",
                type=disnake.OptionType.boolean,
                required=False,
            ),
        ],
    )
    async def modify_problem(
        self,
        inter: disnake.ApplicationCommandInteraction,
        quiz_id: int,
        problem_num: int,
        new_question: str = None,
        new_answer: str = None,
        points_worth: int = None,
        is_written: bool = None,
    ):
        """/quiz edit modify problem (quiz_id: int) (problem_num: int) [new_question: str = None] [new_answer: str= None] [points_worth: int = None] [is_written: bool = None]
        Edit the problem with the given quiz id and problem number, replacing the question, answer, points worth, etc. with what is provided.
        You must be the author of the problem to edit it!
        """
        try:
            quiz: Quiz = await self.bot.cache.get_quiz(quiz_id)
        except QuizNotFound:
            return await inter.send(embed=ErrorEmbed("Quiz not found."))
        try:
            problem: QuizProblem = quiz.quiz_problems[problem_num]
        except IndexError:
            return await inter.send(
                embed=ErrorEmbed(
                    f"There is no problem with quiz id {quiz_id} and problem id {problem_num}!"
                )
            )
        if not problem.author == inter.author.id:
            return await inter.send(
                "You did not author this problem. Therefore, you can't edit it!"
            )
        else:
            await problem.edit(
                question=new_question if new_question is not None else problem.question,
                # The question if there's a new question, otherwise the original question
                answers=[new_answer] if new_answer is not None else problem.answer,
                # The new answer (which replaces all the other answers) if there is a new answer. Otherwise, use the original answer!
                max_score=(
                    points_worth if points_worth is not None else problem.max_score
                ),  # Similar logic
                is_written=(
                    is_written if is_written is not None else is_written
                ),  # Similarly here
            )  # Edit the problem
            return await inter.send("You have successfully modified the problem!")

        # TODO: use QuizSessions to keep track of people solving quizzes!
