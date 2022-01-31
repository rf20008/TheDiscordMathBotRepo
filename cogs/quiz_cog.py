import asyncio
from io import BytesIO
import json
import typing

import disnake
from disnake.ext import commands

from helpful_modules import problems_module
from helpful_modules.custom_embeds import ErrorEmbed, SuccessEmbed
from helpful_modules.problems_module import *
from helpful_modules.problems_module import MathProblemCache, Quiz, QuizProblem
from helpful_modules.problems_module.quizzes import (QuizSolvingSession,
                                                     QuizSubmission)
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

        There is currently a bug. Don't use this because there is a bug that makes the quiz not actually be created because there are no problems."""

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
            points: typing.Optional[float] = 0.5
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
                        trusted=False, blacklisted=False, user_id=inter.author.id
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
                max_score=points_worth
                if points_worth is not None
                else problem.max_score,  # Similar logic
                is_written=is_written
                if is_written is not None
                else is_written,  # Similarly here
            )  # Edit the problem
            return await inter.send("You have successfully modified the problem!")

        # TODO: use QuizSessions to keep track of people solving quizzes!

    @quiz.sub_command_group(name="view", description="View quizzes!")
    def view(self, inter: disnake.ApplicationCommandInteraction):
        """/quiz view

        View quizzes

        Subcommands:
        /quiz view entire_quiz
        ---
        View the entire quiz. You must have an existing session for this to work!


        /quiz view ids
        ---
        View the available Quiz IDs


        /quiz view problem

        View the specific quiz problems!"""
        pass

    @view.sub_command(
        name="entire_quiz",
        description="View the entire quiz. You must have a session!",
        options=[
            disnake.Option(
                name="quiz_id",
                description="The Quiz ID of the quiz you wish to view",
                type=disnake.OptionType.integer,
                required=True,
            ),
            disnake.Option(
                name="raw",
                description="Whether to view the problem raw. You must either be a moderator or be a trusted user to do this!",
                type=disnake.OptionType.boolean,
                required=False,
            ),
            disnake.Option(
                name="show_all_info",
                description="Whether to show all the info. This permission is normally not granted to normal users.",
                type=disnake.OptionType.boolean,
                required=False,
            ),
        ],
    )
    @commands.max_concurrency(7, commands.BucketType.default, wait=True)
    async def entire_quiz(
            self,
            inter: disnake.ApplicationCommandInteraction,
            quiz_id: int,
            raw: bool = False,
            show_all_info: bool = False,
    ):
        """/quiz view entire_quiz [quiz_id: int] (raw: bool = False) (show_all_data: bool = False)
        Raw: Show the data as JSON. You must be trusted to do this!
        show_all_data: Whether to show all data. You must have either solved the quiz (and the quiz owner has to enable quiz solvers seeing the quiz, which is not implemented yet), or you need to be a moderator, or you need to be a trusted user.


        View the entire quiz. Due to Discord limitations, it will be sent in multiple embeds and multiple messages, which might trigger spam filters."""
        await inter.response.defer()
        if raw and not show_all_info:
            await inter.send(embed=ErrorEmbed("You must enable show_all_info to see raw data!"))
            return
        allowed = False
        if raw or show_all_info:
            allowed = False
            if show_all_info:
                # Did they solve it?
                try:
                    quiz: Quiz = await self.cache.get_quiz(quiz_id)
                except QuizNotFoundException:
                    await inter.send(embed=ErrorEmbed("Quiz not found"))
                    return
                solved_quiz: bool = (
                                            len(
                                                filter(
                                                    lambda submission: submission.user_id == inter.author.id,
                                                    quiz.submissions,
                                                )
                                            )
                                            != 0
                                    ) or (
                                            len(
                                                filter(
                                                    lambda _session: (_session.overtime
                                                                      and _session.user_id == inter.author.id),
                                                    quiz.existing_sessions,
                                                )
                                            )
                                            != 0
                                    )
                if quiz.description.solvers_can_view_quiz and solved_quiz:
                    allowed = True
                else:
                    # Are they a mod?
                    data: problems_module.GuildData = (
                        await self.bot.cache.get_guild_data(
                            inter.guild.id,
                            default=problems_module.GuildData.default(
                                guild_id=inter.guild.id
                            ),
                        )
                    )
                    if data.mod_check.check_for_user_passage(inter.author):
                        # They're a mod!
                        allowed = True
                    else:
                        user_data: problems_module.UserData = (
                            await self.bot.cache.get_user_data(
                                user_id=inter.author.id,
                                default=problems_module.UserData(
                                    user_id=inter.author.id,
                                    trusted=False,
                                    blacklisted=False,
                                ),
                            )
                        )
                        if user_data.trusted:
                            allowed = True
            if not allowed:
                await inter.send(
                    embed=ErrorEmbed(
                        """You didn't pass the checks required to pass. Firstly, you didn't solve the quiz, or you did, but people who solve this quiz can't see the answers.
                Secondly, you're not a moderator.
                Finally, you're not trusted. 
                For these reasons, you are not allowed to see all data for the quiz"""
                    )
                )
            if raw:
                allowed = False
                user_data: problems_module.UserData = await self.bot.cache.get_user_data(
                    user_id=inter.author.id,
                    default=problems_module.UserData(
                        user_id=inter.author.id, trusted=False, blacklisted=False
                    )
                )
                if user_data.trusted:
                    allowed = True

        try:
            session: QuizSolvingSession = await self._get_quiz_submission(
                inter.author.id, quiz_id
            )
        except problems_module.errors.SessionNotFoundException:
            await inter.send(embed=ErrorEmbed("Session not found!"))
            return

        if session.overtime:
            await inter.send(
                embed=ErrorEmbed(
                    "Sorry, but you ran out of time, so you'll need to try again!"
                )
            )
            return

        thing_to_send: str = f"Quiz id #{quiz_id}"
        try:
            quiz_problems: typing.List[QuizProblem] = list(
                (await self.cache.get_quiz(quiz_id)).quiz_problems
            )
        except problems_module.QuizNotFound:
            await inter.send(
                embed=ErrorEmbed(
                    "Apparently the quiz was deleted while you were solving... :("
                )
            )
            return
        if not raw and not show_all_info:
            await inter.send(embed=disnake.Embed(thing_to_send))
            for problem_num, problem in quiz_problems.items():
                problem_str = f"""
                Question: {problem.question}
                Is Written: {'yes' if problem.is_written else 'no'}
                Max Score: {problem.max_score}
                Problem Number: {problem_num}
"""
                await inter.send(
                    embed=disnake.Embed(
                        title=f"Problem #{problem_num}",
                        description=problem_str,
                        color=disnake.Color.from_rgb(20, 200, 30),
                    )
                )
                await asyncio.sleep(1)  # To avoid rate-limiting

        if not allowed:
            await inter.send("You are not allowed to do this!")
        elif show_all_info and not raw and allowed:
            await inter.send(thing_to_send)
            for problem_num, problem in quiz.quiz_problems.items():
                problem_str = f"""
Question: {problem.question}
Answer: {problem.answer if problem.is_written else '(This problem is a written problem)'}
Is Written: {problem.is_written}
Max Score: {problem.max_score}
Problem Number: {problem_num}"""
                await inter.send(
                    embed=disnake.Embed(
                        title=f"Problem #{problem_num}",
                        description=problem_str,
                        color=disnake.Color.from_rgb(90, 90, 250)
                    )
                )
                await asyncio.sleep(1)
        elif raw and show_all_info and allowed:
            file: disnake.File = disnake.File(BytesIO(
                json.dumps(
                    quiz.to_dict()
                ),
                'utf-8'),
                filename='raw_quiz.json')
            await inter.send('I have attached the file!', file=file)
            del file

    async def _get_quiz_submission(
            self, user_id: int, quiz_id: int, attempt_num: typing.Optional[int] = None
    ) -> typing.Optional[
        typing.Union[QuizSolvingSession, typing.List[QuizSolvingSession]]
    ]:
        quiz: Quiz = await self.cache.get_quiz(quiz_id)

        def check(session: QuizSolvingSession) -> bool:
            works: bool = True
            if attempt_num is not None:
                works = session.attempt_num == attempt_num
            return session.user_id == user_id and works

        sessions = filter(check, quiz.existing_sessions)
        if sessions is []:
            raise problems_module.QuizSessionNotFoundException("Quiz session not found")

        return (
            sessions[0]
            if len(sessions) == 1
            else max(sessions, key=lambda session: session.attempt_num)
        )

    @quiz.sub_command_group(name="solve", description="Solve quizzes")
    def solve(self, inter: disnake.ApplicationCommandInteraction):
        pass

    @solve.sub_command(
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
        Initalize quiz solving. This will create a session for you!"""
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
                await self._get_attempt_num_for_user(inter.author.id, quiz_id=quiz_id) + 1
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

    async def _get_attempt_num_for_user(self, user_id: int, quiz_id: int) -> int:
        """Get the latest attempt number for the user for this quiz"""
        quiz: Quiz = await self.cache.get_quiz(quiz_id)

        def check(session: QuizSolvingSession) -> bool:
            """A function to determine whether this submission should be included"""
            return session.user_id == user_id

        # basically: use filter() to make sure the sessions we check only are from the user.
        # From that, we use list comprehension to create a list of the attempt numbers of the sessions given
        # Then we use max() to find the maximum of that created list and return it
        return max([item.attempt_num for item in filter(check, quiz.existing_sessions)])

    @solve.sub_command(
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
    def solve_quiz_problem_given_id(self, inter: disnake.ApplicationCommandInteraction, quiz_id: int, problem_num: int, answer: str):
        """/quiz solve solve_quiz_problem_given_id (quiz_id: int) (problem_num: int)

        The only way to solve quizzes. """
