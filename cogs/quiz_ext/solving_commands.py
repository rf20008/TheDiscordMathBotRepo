import asyncio
import json
import typing
from io import BytesIO

import disnake
from disnake.ext import commands

from helpful_modules import checks, problems_module
from helpful_modules.custom_bot import TheDiscordMathProblemBot
from helpful_modules.custom_embeds import ErrorEmbed, SuccessEmbed
from helpful_modules.problems_module import *
from helpful_modules.problems_module import MathProblemCache, Quiz, QuizProblem
from helpful_modules.problems_module.quizzes import QuizSolvingSession, QuizSubmission
from helpful_modules.threads_or_useful_funcs import generate_new_id, get_log

from ..helper_cog import HelperCog


class QuizSolveCog(HelperCog):
    def __init__(self, bot: TheDiscordMathProblemBot):
        super().__init__(bot)
        self.bot = bot
        self.cache = bot.cache

    @checks.has_privileges(denylisted=False)
    @commands.slash_command(name="solve_quiz", description="Solve quizzes")
    async def solve_quiz(self, inter: disnake.ApplicationCommandInteraction):
        """This is a command used to solve quizzes

        Usage:
        /solve_quiz solve_quiz_problem_given_id [quiz_id: int] [problem_num: int] [answer: str]
        Solve a quiz (given the quiz id & problem num, even though the bot uses QuizSolvingSessions)
        """
        pass

    @solve_quiz.sub_command(
        name="solve_quiz_problem_given_id",
        description="Solve a quiz problem given the id",
        options=[
            disnake.Option(
                name="quiz_id",
                description="The Quiz ID containing the problem to solve",
                type=disnake.OptionType.integer,
                required=True,
            ),
            disnake.Option(
                name="problem_num",
                description="The problem number of the problem you intend to solve",
                type=disnake.OptionType.integer,
                required=True,
            ),
            disnake.Option(
                name="answer",
                description="The answer you give",
                type=disnake.OptionType.integer,
                required=True,
            ),
        ],
    )
    async def solve_quiz_problem_given_id(
        self,
        inter: disnake.ApplicationCommandInteraction,
        quiz_id: int,
        problem_num: int,
        answer: str,
    ):
        """/quiz solve solve_quiz_problem_given_id (quiz_id: int) (problem_num: int) (answer: str)

        The only way to solve quizzes.

        WARNING: This will overwrite your older answer!

        """
        try:
            quiz = await self.cache.get_quiz(quiz_id)
        except QuizNotFound:
            await inter.send("Quiz not found")
            return

        session = await get_quiz_submission(self, inter.author.id, quiz_id)
        if session.done:
            await inter.send(
                "Your session is done, so you are not allowed to solve this problem!"
            )
            return

        try:
            _: QuizProblem = quiz.problems[problem_num]
        except KeyError:
            await inter.send(
                embed=ErrorEmbed(
                    f"Problem number out of range (the quiz does not have a problem #{problem_num})"
                )
            )
            return

        answer = QuizSubmissionAnswer(
            answer=answer,
            problem_id=problem_num,
            quiz_id=quiz_id,
            grade=None,
            reasoning=None,
        )

        await session.modify_answer(answer_to_add=answer, index=problem_num)
        await self.cache.update_quiz(quiz)
        await inter.send(
            "You have successfully set your answer to the one specified.",
            ephemeral=True,
        )
        return

    @checks.has_privileges(denylisted=False)
    @solve_quiz.sub_command(
        name="initialize_quiz_solving",
        description="Initialize solving a quiz",
        options=[
            disnake.Option(
                name="quiz_id",
                description="The ID of the quiz you wish to initialize solving",
                type=disnake.OptionType.integer,
                required=True,
            )
        ],
    )
    async def initialize_quiz_solving(
        self, inter: disnake.ApplicationCommandInteraction, quiz_id: int
    ):
        """/quiz solve initialize_quiz_solving
        Initialize quiz solving. This will create a session for you!"""
        # Make sure the quiz exists before creating the session
        try:
            quiz: Quiz = await self.bot.cache.get_quiz(quiz_id)
            if quiz.guild_id != inter.guild_id and quiz.guild_id is not None:
                await inter.send(
                    embed=ErrorEmbed(
                        "This quiz exists, but it doesn't belong to this guild."
                    )
                )
                return
        except problems_module.errors.QuizNotFound:
            await inter.send(embed=ErrorEmbed("Quiz not found"))
            return
        attempt_num: int = (
            await get_attempt_num_for_user(self, inter.author.id, quiz_id=quiz_id) + 1
        )
        submission_to_add = problems_module.QuizSolvingSession(
            user_id=inter.author.id,
            guild_id=inter.guild_id,
            quiz_id=quiz_id,
            attempt_num=attempt_num,
        )
        quiz.existing_sessions.append(submission_to_add)
        await quiz.update_self()
        await inter.send("I have successfully created a session for you!")


def setup(*args):
    pass
