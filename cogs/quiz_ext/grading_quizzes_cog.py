import typing

import disnake
from disnake.ext import commands

from helpful_modules import checks, problems_module
from helpful_modules.custom_bot import TheDiscordMathProblemBot
from helpful_modules.my_modals import MyModal
from helpful_modules.problems_module import *

from ..helper_cog import HelperCog
from ._utils import get_quiz_submission
from .grading_views_and_ui_components import GradingModal, GradingQuizView


class GradingQuizzesCog(HelperCog):
    def __init__(self, bot: TheDiscordMathProblemBot):
        super().__init__(bot)

    async def can_grade_quiz(self, inter, quiz_id):
        """Return whether the user can grade the quiz and respond no to the interaction if not."""
        if quiz_id is ...:
            await inter.send("You didn't provide a quiz id!")
            return False

        try:
            quiz = await self.cache.get_quiz(quiz_id)
        except problems_module.QuizNotFound:
            await inter.send(embed=ErrorEmbed("Quiz not found!"))
            return False

        if quiz.empty:
            await inter.send("You can't grade this quiz because it's empty!")
            return False

        if quiz.guild_id is not None and quiz.guild_id not in [
            guild.id for guild in inter.author.mutual_guilds
        ]:
            await inter.send("This quiz isn't in any of your mutual guilds!")
            return False

        if quiz.guild_id is not None and quiz.guild_id != inter.guild_id:
            await inter.send(
                f"This is the wrong guild for the quiz -- the right guild is the one with the id {quiz.guild_id}"
            )
            return False

        if inter.author.id not in quiz.authors:
            await inter.send("You don't have permission to grade this quiz.")
            return False
        return True

    @commands.slash_command(name="quiz_grade", description="Grade quizzes!")
    async def quiz_grade(self, inter: disnake.ApplicationCommandInteraction):
        """This is a slash command that is meant to be used to grade quizzes!"""
        pass

    @checks.is_not_denylisted()
    @quiz_grade.sub_command(
        name="view_submission_users",
        description="View the users who submitted submissions to this quiz",
    )
    async def view_submission_users(
        self, inter, quiz_id: int = commands.Param(large=True)
    ) -> typing.Optional[typing.Union[disnake.InteractionMessage, disnake.Message]]:
        """/quiz_grade view_submission_users

        View the list of users who did the quiz. You must be an author to run this command.
        """
        if not await self.can_grade_quiz(inter, quiz_id):
            return
        users_with_submissions = set()
        for submission in quiz.submissions:
            users_with_submissions.add(submission.user_id)

        string_to_send = f"""
        Users who have submitted answers to this quiz
        -------------
        """
        for user_id in users_with_submissions:
            string_to_send += f"<@{user_id}>\n"
        string_to_send += (
            f"({len(users_with_submissions)} users)"  # TODO: use a paginator
        )
        await inter.send(
            embed=SuccessEmbed(string_to_send),
            allowed_mentions=disnake.AllowedMentions(users=False),
        )
        del users_with_submissions
        del string_to_send
        return
    @checks.is_not_denylisted()
    @quiz_grade.sub_command(name="manual_grade", description="Manually grade quizzes")
    async def manual_grade(
        self,
        inter: disnake.ApplicationCommandInteraction,
        quiz_id: int = commands.Param(description="The quiz to grade"),
        user: disnake.User = commands.Param(description="The user to grade"),
        attempt_num: int = commands.Param(
            description="The attempt number to grade (defaults to 0)", le=0
        ),
    ):
        """/quiz_grade manual_grade

        Manually grade a user's submission to a quiz. You must be an author of the quiz you want to grade!
        The bot will send modals about reasoning and grade, which you will have to complete in 1 hour.
        After that, you will need to press a button that will send the next modal, labeled Continue Grading.
        If you stop, your changes will be saved!
        """  # noqa: E501
        if not await self.can_grade_quiz(inter, quiz_id):
            return

        # This user can grade the quiz
        # Fetch the quiz again
        # It is known that the quiz exists, or it would have been handled in await self.can_grade_quiz
        quiz = await self.cache.get_quiz(quiz_id)
        user_submissions = [
            submission
            for submission in quiz.submissions
            if submission.user_id == user.id
            and submission.attempt_num == attempt_num
            and submission.done
        ]
        if user_submissions is []:
            return await inter.send(
                "That user didn't submit to this quiz with attempt number #"
                + attempt_num
                + " !"
            )
        submission = user_submissions[0]
        qn = 0
        for question_num in range(len(quiz.problems)):
            try:
                question = quiz.problems[question_num]
            except KeyError:
                break

            if question.is_written:
                break
            qn = question_num
            if quiz.problems[submission.problem_id].is_written is False:
                # Automatically grade
                if submission.answer in quiz_problems[submission.problem_id].answers:
                    # Give them the full grade
                    submission.set_grade(quiz.problems[submission.problem_id].max_score)
                    submission.reasoning = (
                        "Matched one of the specified correct answers"
                    )

        view = GradingQuizView(
            quiz_id=quiz_id,
            user_id=user_id,
            bot=self.bot,
            attempt_num=attempt_num,
            problem_num=qn,
            grader_user_id=inter.author.id,
            timeout=600,
        )
        await inter.send(view=view, content="Click a button to grade!")
        raise NotImplementedError("This part of the logic is not yet implemented!")


def setup(*args):
    pass
