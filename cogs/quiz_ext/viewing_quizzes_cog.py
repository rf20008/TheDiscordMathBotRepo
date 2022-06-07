import typing

import disnake
from disnake.ext import commands

from helpful_modules import checks, problems_module
from helpful_modules.custom_bot import TheDiscordMathProblemBot
from helpful_modules.custom_embeds import *
from helpful_modules.problems_module import *

from ..helper_cog import HelperCog
from ._utils import get_attempt_num_for_user, get_quiz_submission


class ViewingQuizzesCog(HelperCog):
    def __init__(self, bot: TheDiscordMathProblemBot):
        super().__init__(bot)
        self.bot = bot
        self.cache = bot.cache

    async def quiz_pages(self, guild_id: int) -> typing.List[str]:
        await self.cache.update_cache()
        pages_list = []
        cur_page = ""
        page_num = 0
        for quiz in filter(
            lambda quiz: quiz.guild_id is None, self.cache.cached_quizzes
        ):
            thing_to_add = str(quiz.description)
            if len(cur_page) + len(thing_to_add) < 4000:
                cur_page += "----------------------"
                cur_page += thing_to_add
            else:
                pages_list[page_num] = cur_page
                cur_page = ""
                page_num += 1

        for quiz in filter(
            lambda quiz: quiz.guild_id == guild_id, self.cache.cached_quizzes
        ):
            thing_to_add = str(quiz.description)
            if len(cur_page) + len(thing_to_add) < 4000:
                cur_page += "----------------------"
                cur_page += thing_to_add
            else:
                pages_list[page_num] = cur_page
                cur_page = ""
                page_num += 1
        return pages_list

    async def can_view_quiz_given_inter(
        self, inter: disnake.ApplicationCommandInteraction, quiz_id
    ) -> bool:
        can_view_quiz: bool = False
        if await self.bot.is_trusted(inter.author):
            # Trusted users are global moderators, so they can view quizzes
            can_view_quiz = True
            return True
        else:
            data = await self.cache.get_guild_data(
                inter.guild.id, default=problems_module.GuildData.default()
            )
            if data.mod_check.check_for_user_passage(inter.author):
                # Mods can view quizzes
                can_view_quiz = True
        if not can_view_quiz:
            try:
                session: problems_module.QuizSolvingSession = await get_quiz_submission(
                    self, inter.author.id, quiz_id
                )
            except problems_module.errors.SessionNotFoundException:
                await inter.send(
                    embed=ErrorEmbed("You don't have a session for this quiz!!")
                )
                return False

            if session.done:
                # Mods can view quizzes, even if they don't have a session
                await inter.send(
                    embed=ErrorEmbed(
                        "You're not allowed to see this quiz because you're not a moderator or a trusted user and your session expired!"
                    )
                )
                return False
            else:
                can_view_quiz = True

        if not can_view_quiz:
            await inter.send(
                embed=ErrorEmbed(
                    "You can't see this quiz! Firstly, you're not a moderator."
                    "Secondly, you're not a trusted user."
                    "Thirdly, you don't have a session, which is required to solve quizzes."
                )
            )
            return False
        return True

    @checks.has_privileges(blacklisted=False)
    @commands.slash_command(name="quiz_view", description="View quizzes!")
    async def quiz_view(self, inter: disnake.ApplicationCommandInteraction):
        """/quiz_view

        View quizzes

        Subcommands:
        /quiz_view entire_quiz
        ---
        View the entire quiz. You must have an existing session for this to work!


        /quiz view ids
        ---
        View the available Quiz IDs


        /quiz view problem

        View the specific quiz problems!"""
        pass

    @quiz_view.sub_command(
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
            await inter.send(
                embed=ErrorEmbed("You must enable show_all_info to see raw data!")
            )
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
                            lambda _session: (
                                _session.overtime
                                and _session.user_id == inter.author.id
                            ),
                            quiz.existing_sessions,
                        )
                    )
                    != 0
                )
                if quiz.description.solvers_can_view_quiz and solved_quiz:
                    allowed = True
                else:
                    # Are they a mod?
                    if inter.guild.id is not None:
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

                    if not allowed:
                        if await self.bot.is_trusted(inter.author):
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
                if inter.guild is not None:
                    _me: disnake.Member = inter.guild.me
                    if not inter.channel.permissions_for(_me).attach_files:
                        return await inter.send(
                            "I don't have the attach files permission. Therefore, I can't send the raw quiz (as it is as sent in a file)."
                        )
                    allowed = False

                if await self.bot.is_trusted(inter.author):
                    allowed = True
        try:
            quiz: Quiz = await self.cache.get_quiz(quiz_id)
        except QuizNotFound:
            await inter.send(embed=ErrorEmbed("Quiz not found"))
            return

        if not await self.can_view_quiz_given_inter(inter, quiz_id):
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
    Author: <@{problem.author}>
    Max Score: {problem.max_score}
    Problem Number: {problem_num}"""
                await inter.send(
                    embed=disnake.Embed(
                        title=f"Problem #{problem_num}",
                        description=problem_str,
                        color=disnake.Color.from_rgb(90, 90, 250),
                    ),
                    allowed_mentions=disnake.AllowedMentions(users=False),
                    ephemeral=False,
                )
                await asyncio.sleep(1)
        elif raw and show_all_info and allowed:
            file: disnake.File = disnake.File(
                BytesIO(json.dumps(quiz.to_dict()), "utf-8"), filename="raw_quiz.json"
            )
            await inter.send("I have attached the file!", file=file, ephemeral=True)
            del file

    @checks.has_privileges(blacklisted=False)
    @quiz_view.sub_command(
        name="single_problem",
        description="View a single problem in a quiz",
        options=[
            disnake.Option(
                name="quiz_id",
                description="The Quiz ID of the quiz to view a single problem from",
                type=disnake.OptionType.integer,
                required=True,
            ),
            disnake.Option(
                name="problem_num",
                description="The problem #",
                type=disnake.OptionType.integer,
                required=True,
            ),
            disnake.Option(
                name="show_all_info",
                description="Whether to show all info about the problem",
                type=disnake.OptionType.boolean,
                required=False,
            ),
            disnake.Option(
                name="raw",
                description="Whether to show JSON-ified problem data",
                type=disnake.OptionType.boolean,
                required=False,
            ),
        ],
    )
    async def single_problem(
        self,
        inter: disnake.ApplicationCommandInteraction,
        quiz_id: int,
        problem_num,
        show_all_info: bool = False,
        raw: bool = False,
    ):
        """/quiz view single_problem
        View a single problem
        Ra"""
        if raw and not show_all_info:
            await inter.send("show_all_info must be set to True if raw is true!")
            return

        allowed = False

        if raw and await self.bot.is_trusted(inter.author):
            allowed = True
        # get the quiz
        try:
            quiz = await self.cache.get_quiz(quiz_id)
        except QuizNotFound:
            await inter.end("Quiz not found!")
            return

        if show_all_info:
            if inter.author.id in quiz.authors:
                allowed = True

            else:
                if inter.guild is not None:
                    data: GuildData = await self.cache.get_guild_data(
                        guild_id, default=problems_module.GuildData.default()
                    )
                    if data.mod_check.check_for_user_passage(inter.author):
                        allowed = True

                if allowed is False:
                    if await self.bot.is_trusted(inter.author):
                        allowed = True

        try:
            problem: QuizProblem = quiz.quiz_problems[problem_id]
        except KeyError:
            await inter.send("Problem number out of range")
            return

        if raw is False and show_all_info is False:

            session = await get_quiz_submission(self, inter.author.id, quiz_id)
            if session.done:
                await inter.send("Your session is done!")
                return
            problem_str = f"""Problem number: {problem_id}
Question: {problem.question}
Author: <@{problem.author}>
Is written: {problem.is_written}
Max Score: {problem.max_score}
"""
            await inter.send(
                embed=SuccessEmbed(
                    title="Here is the problem information!", description=problem_str
                ),
                ephemeral=False,
            )
            return
        elif raw and allowed:
            data: dict = problem.to_dict()
            file = disnake.File(
                BytesIO(json.dumps(data), "utf-8"), filename="the_problem.json"
            )
            await inter.send("The problem information is attached", file=file)
            return

        elif show_all_info and raw and allowed:
            problem_str = f"""Problem number: {problem_id}
            Question: {problem.question}
            Author: <@{problem.author}>
            Answer: {problem.answer}
            Is written: {problem.is_written}
            Max Score: {problem.max_score}
            """
            await inter.send(
                embed=SuccessEmbed(
                    title="Here is the problem information!", description=problem_str
                ),
                allowed_mentions=disnake.AllowedMentions(users=False),
            )
            return

        else:
            await inter.send("You're not allowed to do this!")
            return

    @checks.has_privileges(blacklisted=False)
    @quiz_view.sub_command(
        name="ids",
        description="View the Quiz IDs of the available quizzes and a short description",
        options=[
            disnake.Option(
                name="page_num",
                description="The page #",
                type=disnake.OptionType.integer,
                required=False,
            )
        ],
    )
    async def ids(self, inter, page_num: int = 0) -> None:
        """/quiz_view ids [page_num: int=0]
        View the Quiz IDs and a
        Page num is the page number"""
        try:
            return await inter.send(
                embed=SuccessEmbed((await self.quiz_pages(inter.guild_id))[page_num])
            )
        except IndexError:
            return await inter.send(
                embed=ErrorEmbed(
                    f"Page number out of range (there are only {len(await self.quiz_pages(inter.guild_id))} pages)"
                )
            )


def setup(*args):
    pass
