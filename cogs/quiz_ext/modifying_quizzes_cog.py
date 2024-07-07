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

import asyncio
import json
import typing
from io import BytesIO
from os import urandom

import disnake
from disnake.ext import commands

from helpful_modules import checks, problems_module
from helpful_modules.custom_embeds import ErrorEmbed, SuccessEmbed
from helpful_modules.my_modals import MyModal
from helpful_modules.problems_module import *
from helpful_modules.problems_module import MathProblemCache, Quiz, QuizProblem
from helpful_modules.problems_module.quizzes import QuizSolvingSession, QuizSubmission
from helpful_modules.threads_or_useful_funcs import generate_new_id, get_log

from ..helper_cog import HelperCog


class ModifyingQuizzesCog(HelperCog):
    @checks.has_privileges(denylisted=False)
    @commands.slash_command(name="quiz_edit", description="Edit quizzes")
    async def quiz_edit(self, inter: disnake.ApplicationCommandInteraction):
        """/quiz edit

        Edit quizzes

        Usage:
        /quiz edit add_problem (quiz_id: int) (insert_loc: int) (question: str) (answer1: str) [numPoints: int=1]
        /quiz edit add_answer (quiz_id: int) (problem_num: int) (answer: str)
        /quiz edit modify_problem (quiz_id: int) (problem_num: int) [new_question: str = None] [new_answer: str = None] [points_worth: int = None] [is_written: bool = None]
        /quiz edit delete_problem (quiz_id: int) (problem_num: int)"""
        pass

    @checks.has_privileges(denylisted=False)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @quiz_edit.sub_command(
        name="add_answer",
        description="Add an answer to a quiz problem",
        options=[
            disnake.Option(
                name="quiz_id",
                description="The ID of the quiz that contains the problem to add the answer to",
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

    @checks.has_privileges(denylisted=False)
    @commands.cooldown(1, 30, commands.BucketType.user)
    @quiz_edit.sub_command(
        name="add_problem",
        description="Add a problem to a quiz. You must be an author of the quiz to add a problem",
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
                description="Whether this problem is a written problem and manually graded",
                type=disnake.OptionType.boolean,
                required=False,
            ),
            disnake.Option(
                name="points",
                description="The number of points this question is worth. This must be greater than 0!",
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

    @checks.has_privileges(denylisted=False)
    @commands.cooldown(1, 60, commands.BucketType.user)
    @quiz_edit.sub_command(
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

    @checks.has_privileges(denylisted=False)
    @quiz_edit.sub_command(
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

    @checks.has_privileges(denylisted=False)
    @quiz_edit.sub_command(
        name="modify_quiz_description",
        description="Modify the quiz description of a quiz",
        options=[
            disnake.Option(
                name="quiz_id",
                description="The quiz id of the quiz you wish to modify",
                type=disnake.OptionType.integer,
                required=True,
            ),
            disnake.Option(
                name="new_description",
                description="A new description for the quiz - this will be shown to others",  # TODO: add to ToS
                type=disnake.OptionType.string,
                required=False,
            ),
            disnake.Option(
                name="time_limit",
                description="A new time limit for this quiz (the amount of time allowed in seconds)",
                type=disnake.OptionType.integer,
                required=False,
            ),
            disnake.Option(
                name="difficulty",
                description="The new difficulty of this quiz",
                choices={
                    "IMPOSSIBLE": "225179981368524800",
                    "ONLY_GENIUSES_CAN_SOLVE_THIS": "219902325555200",
                    "EXTREMELY_CHALLENGING": "10000.0",
                    "EXTREMELY_HARD": "5000.0",
                    "VERY_HARD": "2000.0",
                    "CHALLENGING": "1000.0",
                    "HARD": "500.0",
                    "MEDIUM_HARD": "400.0",
                    "MEDIUM": "300.0",
                    "BETWEEN_EASY_AND_MEDIUM": "200.0",
                    "EASY": "100.0",
                    "VERY_EASY": "50.0",
                    "VERY_VERY_EASY": "25",
                    "TRIVIAL": "0",
                    "CUSTOM": "-1",
                    "TOO_EASY": "-219902325555200",
                },
                required=False,
            ),
            disnake.Option(
                name="solvers_can_view_quiz",
                description="Whether solvers can view the quiz, including answers",
                type=disnake.OptionType.boolean,
                required=False,
            ),
        ],
    )
    async def modify_description(
        self,
        inter,
        quiz_id: int,
        new_description: str = None,
        time_limit: int = None,
        difficulty: int = None,
        solvers_can_view_quiz: bool = None,
    ):
        """/quiz_edit modify_description [quiz_id: int] [new_description: str] [time_limit: int] [difficulty:IMPOSSIBLE|ONLY_GENIUSES_CAN_SOLVE_THIS|EXTREMELY_CHALLENGING|EXTREMELY_HARD|VERY_HARD|CHALLENGING|HARD|MEDIUM_HARD|MEDIUM|BETWEEN_EASY_AND_MEDIUM|EASY|VERY_EASY|VERY_VERY_EASY|TRIVIAL|CUSTOM|TOO_EASY] [solvers_can_view_quiz: bool]'
        Modify the description of a quiz

        If you set difficulty to -1, it will send a modal asking you to clarify (which you'll have 30 seconds to answer
        """
        difficulty = int(difficulty)
        # Make sure the quiz exists
        try:
            quiz: Quiz = await self.bot.cache.get_quiz(quiz_id)
        except QuizNotFound:
            await inter.send("Quiz not found")
            return
        # Make sure the user can actually modify the quiz
        if inter.author.id not in quiz.authors:
            await inter.send(
                embed=ErrorEmbed("You don't have permission to modify this quiz!")
            )
            return
        if (
            difficulty is None
            and solvers_can_view_quiz is None
            and time_limit is None
            and solvers_can_view_quiz is None
        ):
            await inter.send("You need to provide inputs!")
            return

        if difficulty == -1:
            # Send a modal asking them for a better description of the quiz description
            quiz_difficulty_custom_id = urandom(16).hex()
            text_inputs = [
                disnake.ui.TextInput(
                    label="The integer value of this quiz's difficulty",
                    custom_id=quiz_difficulty_custom_id,
                    placeholder="Type in an integer representing this quiz's difficulty!",
                    max_length="200",
                )
            ]

            async def _callback(s, inter: disnake.ModalInteraction):
                diff = inter.text_inputs[quiz_difficulty_custom_id]
                if not diff.isnumeric():
                    await inter.send(embed=ErrorEmbed("You didn't type in a number"))
                    return
                if int(diff) < 0:
                    await inter.send("Difficulty is too small")
                    return
                nonlocal difficulty
                difficulty = int(diff)

                await inter.send("Thanks for clarifying!")
                return

            modal_custom_id = urandom(16).hex()
            modal_to_send = MyModal(
                callback=_callback,
                custom_id=modal_custom_id,
                components=[],
                timeout=30,
                inter=inter,
            )
            modal_to_send.append_component(text_inputs)
            await inter.response.send_modal(modal_to_send)
            try:
                modal_inter = await self.bot.wait_for(
                    "modal_submit",
                    check=lambda modal_inter: modal_inter.custom_id == modal_custom_id,
                    timeout=35,
                )
                if modal_inter == -1:
                    raise RuntimeError("Uh oh - modal_inter is still -1")
            except asyncio.TimeoutError:
                await inter.send("You didn't send the modal fast enough!")
                return
        new_description = QuizDescription(
            description=(
                quiz.description.description
                if new_description is None
                else new_description
            ),
            time_limit=(
                quiz.description.time_limit if time_limit is None else time_limit
            ),
            difficulty=(
                quiz.description.difficulty if difficulty is None else difficulty
            ),
            cache=self.cache,
            guild_id=quiz.guild_id,
            author=inter.author.id,
            solvers_can_view_quiz=(
                quiz.description.solvers_can_view_quiz
                if solvers_can_view_quiz is None
                else solvers_can_view_quiz
            ),
        )
        quiz.description = new_description
        await quiz.update_self()

        await inter.send("I have successfully updated the quiz description!")


def setup(*args):
    pass
