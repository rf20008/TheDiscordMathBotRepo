import disnake
import threading
import typing
from asyncio import run
from disnake import *
from disnake.ext import commands
from helpful_modules import checks, problems_module
from helpful_modules.custom_bot import TheDiscordMathProblemBot
from helpful_modules.custom_embeds import SimpleEmbed, SuccessEmbed, ErrorEmbed
from helpful_modules.problems_module import *
from helpful_modules.threads_or_useful_funcs import generate_new_id

from .helper_cog import HelperCog

# TODO: implement /edit_problem remove_answer (but only for authors. Warn the user and confirm using buttons if they are removing the last answer of a problem)
# Licensed under GPLv3


class ProblemsCog(HelperCog):
    def __init__(self, bot: TheDiscordMathProblemBot):
        self.bot = bot
        self.cache = bot.cache
        super().__init__(bot)
        checks.setup(bot)

    @commands.cooldown(1, 1, commands.BucketType.user)
    @checks.is_not_blacklisted()
    @commands.slash_command(name="edit_problem", description="edit a problem")
    async def edit_problem(self, inter: disnake.ApplicationCommandInteraction):
        """The base command to edit problems."""
        pass

    @commands.cooldown(1, 1, commands.BucketType.user)
    @checks.is_not_blacklisted()
    @edit_problem.sub_command(
        name="general_edits",
        description="edit a problem",
        options=[
            Option(
                name="problem_id",
                description="problem_id",
                type=OptionType.integer,
                required=True,
            ),
            Option(
                name="guild_id",
                description="the guild id",
                type=OptionType.integer,
                required=False,
            ),
            Option(
                name="new_question",
                description="the new question",
                type=OptionType.string,
                required=False,
            ),
            Option(
                name="new_answer",
                description="the new answer",
                type=OptionType.string,
                required=False,
            ),
        ],
    )
    async def general_edits(
        self,
        inter: disnake.ApplicationCommandInteraction,
        problem_id: int,
        new_question: str = None,
        new_answer: str = None,
        guild_id: int = Exception,
    ) -> typing.Optional[disnake.Message]:
        """/edit_problem general_edits(problem_id: int) [guild_id: int=Exception] [new_question: str] [new_answer: str]
        Allows you to edit a problem. You can change the question or answer but doing so will delete all other answers of the problem.
        You must be the author of the problem to edit it. You can edit a problem that you created regardless of which guild it's in.
        If you do not specify guild_id, it will default to the guild id of the interaction instead of being `Exception`.
        The bot must be in the guild with specified id, or it will error."""
        if guild_id == Exception:
            guild_id = inter.guild.id
        if guild_id is not None and self.bot.get_guild(guild_id) is None:
            await inter.send(
                embed=ErrorEmbed("I'm not in that guild!", custom_title="Uh oh.")
            )
            return
        try:
            problem = await self.cache.get_problem(int(guild_id), int(problem_id))
            if not problem.is_author(inter.author):
                await inter.send(
                    embed=ErrorEmbed(
                        "You are not the author of this problem and therefore can't edit it!"
                    )
                )
                return
        except ProblemNotFound:
            await inter.send(embed=ErrorEmbed("This problem does not exist!"))
            return
        e = "Successfully"
        if new_question is not None:
            if new_answer is not None:
                await problem.edit(question=new_question, answer=new_answer)
                e += f"changed the answer to {new_answer} and question to {new_question}!"
            else:
                await problem.edit(question=new_question)
                e += f"changed the question to {new_question}!"
        else:
            if new_answer is not None:
                await problem.edit(answer=new_answer)
                e += f"changed the answer to {new_answer}"
            else:
                # raise Exception(
                #    "*** No new answer or new question provided. Aborting command...***"
                # )
                # Return error messages in favor of raising exceptions

                return await inter.send("You must provide either a question or answer.")

        await inter.send(embed=SuccessEmbed(e), ephemeral=True)

    @edit_problem.sub_command(
        name="add_answer",
        description="Add an answer to an existing problem",
        options=[
            Option(
                name="problem_id",
                description="The problem to add an answer to",
                type=OptionType.integer,
                required=True,
            ),
            Option(
                name="answer",
                description="The answer to add to the problem",
                type=OptionType.string,
                required=True,
            ),
            Option(
                name="guild_id",
                description="The guild ID of the problem to edit",
                type=OptionType.integer,
                required=False,
            ),
        ],
    )
    async def add_answer(
        self, inter, problem_id: int, answer: str, guild_id: int = Exception
    ):
        if guild_id == Exception:
            guild_id = inter.guild.id
        if guild_id is not None and self.bot.get_guild(guild_id) is None:
            await inter.send(
                embed=ErrorEmbed("I'm not in that guild!", custom_title="Uh oh.")
            )
            return
        try:
            problem = await self.cache.get_problem(int(guild_id), int(problem_id))
            if not problem.is_author(inter.author):
                await inter.send(
                    embed=ErrorEmbed(
                        "You are not the author of this problem and therefore can't edit it!"
                    )
                )
                return
        except ProblemNotFound:
            await inter.send(embed=ErrorEmbed("This problem does not exist!"))
            return
        if len(problem.get_answers()) + 1 >= self.bot.cache.max_answers_per_problem:
            await inter.send("This problem has the maximum number of answers.")
            return
        problem.add_answer(answer)
        await problem.update_self()
        await inter.reply("Successfully added the answer!")

    @commands.slash_command(
        name="show_problem_info",
        description="Show problem info",
        options=[
            Option(
                name="problem_id",
                description="problem id of the problem you want to show",
                type=OptionType.integer,
                required=True,
            ),
            Option(
                name="show_all_data",
                description="whether to show all data (only usable by problem authors and trusted users",
                type=OptionType.boolean,
                required=False,
            ),
            Option(
                name="raw",
                description="whether to show data as json?",
                type=OptionType.boolean,
                required=False,
            ),
            Option(
                name="is_guild_problem",
                description="whether the problem you are trying to view is a guild problem",
                type=OptionType.boolean,
                required=False,
            ),
        ],
    )
    async def show_problem_info(
        self,
        inter: disnake.ApplicationCommandInteraction,
        problem_id: int,
        show_all_data: bool = False,
        raw: bool = False,
        is_guild_problem: bool = False,
    ):
        """/show_problem_info [problem_id: int] (show_all_data: bool = false) (raw: bool = False) (is_guild_problem: bool = false)
        Show the info of a problem.
        If show_all_data is set to true, you must have trusted user permissions or have the administrator permission in the guild! Otherwise, the bot will tell you can't do that.
        The option `raw` is whether to show the problem as a string-ified version of a Python dictionary. Otherwise, it will be shown in a user-friendly manner. This defaults to False.
        The option `is_guild_problem` tells the bot about whether the problem you're trying to show is a guild problem. This defaults to false, which means you are viewing a global problems unless you specify otherwise.
        **If you execute this in a DM, the bot will treat it like you set is_guild_problem to False regardless of what you put in for the option!**"""
        if inter.guild is None:
            # return await inter.send(embed=ErrorEmbed(
            #    "If you're running this command in a DM, I won't know what guild you're trying to run the command in!"
            # ))
            is_guild_problem = False
        if is_guild_problem and inter.guild is None:
            embed1 = ErrorEmbed(
                description="Run this command in the Discord server which has this problem, not a DM!"
            )
            await inter.send(embed=embed1)
            return
        # try:
        #    guild_id = inter.guild.id
        # except AttributeError as exc:
        #    raise Exception(
        #        "*** AttributeError: guild.id was not found! Please report this error or refrain from using it here***"
        #    ) from exc
        #

        # get the real_guild_id
        try:
            if is_guild_problem:
                real_guild_id = inter.guild.id
            else:
                real_guild_id = None
        except AttributeError:
            real_guild_id = None
        try:
            problem = await self.cache.get_problem(
                real_guild_id, int(problem_id)
            )  # get the problem
        except ProblemNotFound:  # Problem not found
            await inter.send(embed=ErrorEmbed("Problem not found!"))
            return
        try:
            Problem_as_str = f"""Question: {problem.get_question()}
            Author: {str(problem.get_author())}
            Number of Voters/Vote Threshold: {problem.get_num_voters()}/{self.bot.vote_threshold}
            Number of solvers: {len(problem.get_solvers())}"""
        except NameError:
            await inter.send(
                "Uh oh - problem not found! This wasn't handled earlier, so I'm raising an error so my developer can figure out why this is the case. :-)"
            )
            raise
        if show_all_data:
            if not (
                (
                    problem.is_author(inter.author)
                    or inter.author.id not in self.bot.trusted_users
                    or (
                        is_guild_problem
                        and inter.author.guild_permissions.administrator
                    )
                )
            ):  # Check for sufficient permissions
                await inter.send(
                    embed=ErrorEmbed("Insufficient permissions!"), ephemeral=True
                )
                return
            Problem_as_str += f"\nAnswer: {problem.get_answer}"

            if raw:
                await inter.send(
                    embed=SuccessEmbed(str(problem.to_dict())), ephemeral=True
                )
                return
            await inter.send(embed=SuccessEmbed(Problem_as_str), ephemeral=True)
        await inter.send(embed=SuccessEmbed(Problem_as_str), ephemeral=True)

    @commands.cooldown(1, 2.5, commands.BucketType.user)
    @commands.slash_command(
        name="list_all_problem_ids",
        description="List all problem ids",
        options=[
            Option(
                name="show_only_guild_problems",
                description="Whether to show guild problem ids",
                required=False,
                type=OptionType.boolean,
            )
        ],
    )
    async def list_all_problem_ids(self, inter, show_only_guild_problems=False):
        """/list_all_problem_ids [show_only_guild_problems: bool = false]
        List all problem ids. If show_only_guild_problems is true, then only ids of guild problems will be shown. Otherwise, only problem ids of problems that are global will be shown."""
        if show_only_guild_problems:
            guild_id = inter.guild.id
            if guild_id is None:
                await inter.send(
                    "Run this command in a Discord server or set show_only_guild_problems to False!",
                    ephemeral=True,
                )
                return
            if show_only_guild_problems:
                guild_problems = await self.bot.cache.get_guild_problems(
                    inter.guild
                )  # TODO: could be lists

            else:
                guild_problems = await self.bot.cache.get_problems_by_func(
                    func=lambda problem, guild_id: problem.guild_id == guild_id,
                    args=[inter.guild.id],
                )
            thing_to_write = [str(problem) for problem in guild_problems]
            await inter.send(
                embed=SuccessEmbed(
                    "\n".join(thing_to_write)[:1950], successTitle="Problem IDs:"
                )
            )
            return

        global_problems = await self.bot.cache.get_global_problems()
        if isinstance(global_problems, dict):
            global_problems = global_problems.values()
        thing_to_write = "\n".join([str(problem.id) for problem in global_problems])
        await inter.send(embed=SuccessEmbed(thing_to_write))

    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.slash_command(
        name="list_all_problems",
        description="List all problems stored with the bot",
        options=[
            Option(
                name="show_solved_problems",
                description="Whether to show solved problems",
                type=OptionType.boolean,
                required=False,
            ),
            Option(
                name="show_guild_problems",
                description="Whether to show solved problems",
                type=OptionType.boolean,
                required=False,
            ),
            Option(
                name="show_only_guild_problems",
                description="Whether to only show guild problems",
                type=OptionType.boolean,
                required=False,
            ),
        ],
    )
    @checks.is_not_blacklisted()
    async def list_all_problems(
        self,
        inter,
        show_solved_problems=False,
        show_guild_problems=True,
        show_only_guild_problems=False,
    ):
        """/list_all_problems [show_solved_problems: bool = false] [show_guild_problems: bool = true] [show_only_guild_problems: bool = false]
        List all problems.
        If show_solved_problems is set to true,"""
        if inter.guild is None and show_guild_problems:
            await inter.send("You must be in a guild to see guild problems!")
            return
        showSolvedProblems = show_solved_problems
        guild_id = inter.guild.id
        # Check for no problems
        if len(await self.bot.cache.get_guild_problems(inter.guild)) == 0:
            await inter.send("No problems currently exist.")
            return
        # if not showSolvedProblems and False not in [inter.author.id in mathProblems[id]["solvers"] for id in mathProblems.keys()] or (show_guild_problems and (show_only_guild_problems and (guildMathProblems[inter.guild.id] == {}) or False not in [inter.author.id in guildMathProblems[guild_id][id]["solvers"] for id in guildMathProblems[guild_id].keys()])) or show_guild_problems and not show_only_guild_problems and False not in [inter.author.id in mathProblems[id]["solvers"] for id in mathProblems.keys()] and False not in [inter.author.id in guildMathProblems[guild_id][id]["solvers"] for id in guildMathProblems[guild_id].keys()]:
        # await inter.send("You solved all the problems! You should add a new one.", ephemeral=True)
        # return
        problem_info_as_str = ""
        problem_info_as_str += "Problem Id \t Question \t numVotes \t numSolvers"
        if show_guild_problems:
            for problem in await self.cache.get_problems_by_guild_id(guild_id):
                if len(problem_info_as_str) >= 1930:
                    problem_info_as_str += "The combined length of the questions is too long.... shortening it!"  # May be removed
                    await inter.send(embed=SuccessEmbed(problem_info_as_str[:1930]))
                    return
                if not showSolvedProblems and problem.is_solver(
                    inter.author
                ):  # If the user solved the problem, don't show the problem
                    continue
                problem_info_as_str += "\n"
                problem_info_as_str += str(problem.id) + "\t"
                problem_info_as_str += str(problem.get_question()) + "\t"
                problem_info_as_str += "("
                problem_info_as_str += (
                    str(problem.get_num_voters())
                    + "/"
                    + str(self.bot.vote_threshold)
                    + ")"
                    + "\t"
                )
                problem_info_as_str += str(len(problem.get_solvers())) + "\t"
                problem_info_as_str += "(guild)"
        if len(problem_info_as_str) > 1930:
            await inter.send(embed=SuccessEmbed(problem_info_as_str[:1930]))
            return
        if show_only_guild_problems:
            await inter.send(problem_info_as_str[:1930])
            return
        global_problems = (await self.bot.get_global_problems()).values()
        for problem in global_problems:
            if len(problem) >= 1930:
                problem_info_as_str += "The combined length of the questions is too long.... shortening it!"
                await inter.send(embed=SuccessEmbed(problem_info_as_str[:1930]))
                return
            if not showSolvedProblems and problem.is_solver(inter.author):
                continue  # Don't show solved problems if the user doesn't want to see solved problems
            # Probably will be overhauled with str(problem)
            problem_info_as_str += "\n"
            problem_info_as_str += str(problem.id) + "\t"
            problem_info_as_str += str(problem.get_question()) + "\t"
            problem_info_as_str += "("
            problem_info_as_str += (
                str(problem.get_num_voters())
                + "/"
                + str(self.bot.vote_threshold)
                + ")"
                + "\t"
            )
            problem_info_as_str += str(len(problem.get_solvers())) + "\t"
        await inter.send(embed=SuccessEmbed(problem_info_as_str[:1930]))

    @commands.slash_command(
        name="delallbotproblems",
        description="delete all automatically generated problems",
    )
    @checks.trusted_users_only()
    @disnake.ext.commands.cooldown(1, 15, commands.BucketType.user)
    async def delallbotproblems(self, inter: disnake.ApplicationCommandInteraction):
        """/delallbotproblems
        Delete all automatically generated problems."""
        await inter.send(
            embed=SimpleEmbed("", description="Attempting to delete bot problems"),
            ephemeral=True,
        )  # may get rid of later? :)

        await self.cache.delete_all_by_user_id(self.bot.user.id)
        # async with aiosqlite.connect(self.bot.cache.db_name) as conn: #
        #    cursor = conn.cursor()
        #    await cursor.execute(
        #        "DELETE FROM problems WHERE user_id = ?", (self.bot.user.id)
        #    )  # Delete every problem made by the bot!
        #    await conn.commit()
        await inter.send(
            embed=SuccessEmbed(
                f"Successfully deleted all automatically generated problems!"
            )
        )

    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.slash_command(
        name="submit_problem",
        description="Create a new problem",
        options=[
            Option(
                name="question",
                description="your question to submit!",
                type=OptionType.string,
                required=True,
            ),
            Option(
                name="answer",
                description="The answer to this problem",
                type=OptionType.string,
                required=True,
            ),
            Option(
                name="guild_question",
                description="Whether it should be a question for the guild",
                type=OptionType.boolean,
                required=False,
            ),
        ],
    )
    async def submit_problem(
        self,
        inter: disnake.ApplicationCommandInteraction,
        answer: str,
        question: str,
        guild_question: bool = False,
    ) -> None:
        """/submit_problem {question:str}, {answer:str}, [guild_question:bool=false]
        Create & submit a new problem with the given question and answer.
        If the problem is a guild problem, it must not be executed in a DM context or the bot will not know which guild the problem is for!"""
        if (
            len(question) > self.cache.max_question_length
        ):  # Check to make sure it's not too long!
            await inter.send(
                embed=ErrorEmbed(
                    f"Your question is too long! Therefore, it cannot be added. The maximum question length is {self.cache.max_question_length} characters.",
                    custom_title="Your question is too long.",
                ),
                ephemeral=True,
            )
            return
        if len(answer) > self.cache.max_answer_length:
            await inter.send(
                embed=ErrorEmbed(
                    description=f"Your answer is longer than {self.cache.max_answer_length} characters. Therefore, it is too long and cannot be added.",
                    custom_title="Your answer is too long",
                ),
                ephemeral=True,
            )
            remover = threading.Thread(
                target=run, args=(self.cache.remove_duplicate_problems,)
            )  # might be removed - DoS attack?
            remover.start()
            return
        if guild_question:
            if inter.guild is None:
                raise RuntimeError(
                    "You're not allowed to submit guild problems because you're executing this in a DM context, or there is a bug with the library"
                )

            guild_id = inter.guild.id
            if guild_id is None:
                await inter.send(
                    embed=ErrorEmbed(
                        "You need to be in the guild to make a guild question!"
                    )
                )
            return
        try:
            assert not (
                guild_question
                and (inter.guild is None or not hasattr(inter.guild, "id"))
            ), "This command may not be used in DMs!"
        except AssertionError:
            await inter.send(
                "In order to submit a problem for your guild, you must not be executing this command in a DM!"
            )
            return
        if (
            inter.guild is None or not guild_question
        ):  # There is no maximum global problem limit
            pass
        elif (
            guild_question
            and len(self.cache.get_guild_problems(inter.guild))
            >= self.cache.max_guild_problems
        ):  # Check to make sure the maximum guild problem limit is not reached
            await inter.send(
                embed=ErrorEmbed(
                    f"You have reached the guild problem limit of {self.cache.max_guild_problems} and therefore cannot create new problems!"
                    + (
                        """This is to prevent spam. 
                        As of right now, there is no way to increase the guild problem limit.
                        This is because there is no premium version of the bot (because it is open-source).
                        However, if you are self-hosting the bot, you can increase the limit in main.py :-)"""
                    )
                )
            )
            return  # Exit the function

        while True:

            problem_id = generate_new_id()
            if problem_id not in [
                problem.id
                for problem in await self.cache.get_problems_by_func(
                    func=lambda problem: True
                )  # Get everything
            ]:  # Make sure this id isn't already used!
                break  # Break the loop if the problem isn't already used
        if guild_question:
            # If this is a guild question, set the guild id
            # to the guild id of the guild this command was run in
            guild_id = inter.guild.id
        else:  # But if it's global, make it global
            guild_id = None

        problem = problems_module.BaseProblem(
            question=question,
            answers=[answer],
            id=problem_id,
            author=inter.author.id,
            guild_id=guild_id,
            cache=self.cache,
        )  # Create the problem!
        print(problem)
        await self.cache.add_problem(
            problem_id=problem_id, problem=problem
        )  # Add the problem

        await inter.send(
            embed=SuccessEmbed(
                "You have successfully made a math problem!",
                successTitle="Successfully made a new math problem.",
            ),
            ephemeral=True,
        )  # Inform the user of success!

        return

    # @commands.slash_command(
    #     name="check_answer",
    #     description="Check your answer to a problem that was submitted",
    #     options=[
    #         Option(
    #             name="problem_id",
    #             description="the id of the problem you are trying to check the answer of",
    #             type=OptionType.integer,
    #             required=True,
    #         ),
    #         Option(
    #             name="answer",
    #             description="your answer",
    #             type=OptionType.string,
    #             required=True,
    #         ),
    #         Option(
    #             name="checking_guild_problem",
    #             description="whether checking a guild problem",
    #             type=OptionType.boolean,
    #             required=False,
    #         ),
    #     ],
    # )
    # @checks.is_not_blacklisted()
    # async def check_answer(
    #         self,
    #         inter: disnake.ApplicationCommandInteraction,
    #         problem_id: int,
    #         answer: str,
    #         checking_guild_problem: bool = False,
    # ):
    #     """/check_answer {problem_id: int} {answer: str} [checking_guild_problem: bool = False]
    #     Check your answer to the problem with the given id.
    #     The bot will tell you whether you got a problem wrong."""
    #     if not inter.guild:
    #         checking_guild_problem = False
    #
    #     await cooldowns.check_for_cooldown(inter, "check_answer", 5)
    #     try:
    #         problem = await self.cache.get_problem(
    #             int(inter.guild.id) if checking_guild_problem else None, int(problem_id)
    #         )
    #         # Make sure the author didn't already solve this problem
    #         if problem.is_solver(inter.author):
    #             await inter.send(
    #                 embed=ErrorEmbed(
    #                     "You have already solved this problem!",
    #                     custom_title="Already solved.",
    #                 ),
    #                 ephemeral=True,
    #             )
    #             return
    #     except (KeyError, problems_module.errors.ProblemNotFound):
    #         await inter.send(
    #             embed=ErrorEmbed(
    #                 "This problem doesn't exist!", custom_title="Nonexistent problem."
    #             ),
    #             ephemeral=True,
    #         )
    #         return
    #     # Should reverse this
    #     if not problem.check_answer(answer):
    #         await inter.send(
    #             embed=ErrorEmbed(
    #                 "You didn't answer the problem correctly! You can vote for the deletion of this problem if it's wrong or breaks copyright rules.",
    #                 custom_title="Sorry, your answer is wrong.",
    #             ),
    #             ephemeral=True,
    #         )
    #     else:
    #         await inter.send(
    #             embed=SuccessEmbed(
    #                 "", successTitle="You answered this question correctly!"
    #             ),
    #             ephemeral=True,
    #         )
    #         await problem.add_solver(inter.author)
    #         return
    #

    # Commented out: duplicate
    @commands.slash_command(
        name="check_answer",
        description="Check if you are right",
        options=[
            Option(
                name="problem_id",
                description="the id of the problem you are trying to check the answer of",
                type=OptionType.integer,
                required=True,
            ),
            Option(
                name="answer",
                description="your answer",
                type=OptionType.string,
                required=True,
            ),
            Option(
                name="checking_guild_problem",
                description="whether checking a guild problem",
                type=OptionType.boolean,
                required=False,
            ),
        ],
    )
    @checks.is_not_blacklisted()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def check_answer(
        self,
        inter: disnake.ApplicationCommandInteraction,
        problem_id: int,
        answer: str,
        checking_guild_problem: bool = False,
    ):
        """/check_answer {problem_id: int} {answer: str} [checking_guild_problem: bool = false]
        Check your answer to the problem with the given id.
        If this command is executed in a DM, then you must set checking_guild_problem to False or the bot will error."""
        if not inter.guild or not hasattr(inter.guild, "id"):
            if checking_guild_problem:
                return await inter.send(
                    embed=ErrorEmbed(
                        "You must run the command with checking_guild_problem set to False! If you set it to True I don't know which guild the problem is in!"
                    )
                )
            checking_guild_problem = False
        try:
            problem = await self.bot.cache.get_problem(
                inter.guild.id if inter.guild is not None else None, int(problem_id)
            )
            if problem.is_solver(inter.author):  # If the user solved the problem
                await inter.send(
                    embed=ErrorEmbed(
                        "You have already solved this problem!",
                        custom_title="Already solved.",
                    ),
                    ephemeral=True,
                )  # Don't let them re-solve the problem
                return
        except (
            ProblemNotFound,
            ProblemNotFoundException,
        ):  # But if the problem wasn't found, then tell them
            await inter.send(
                embed=ErrorEmbed(
                    "This problem doesn't exist!", custom_title="Nonexistent problem."
                ),
                ephemeral=True,
            )
            return

        if not problem.check_answer(answer):
            await inter.send(
                embed=ErrorEmbed(
                    "Sorry..... but you got it wrong! You can vote for the deletion of this problem if it's wrong or breaks copyright rules.",
                    custom_title="Sorry, your answer is wrong.",
                ),
                ephemeral=True,
            )
        else:
            await inter.send(
                embed=SuccessEmbed(
                    "", successTitle="You answered this question correctly!"
                ),
                ephemeral=True,
            )
            problem.solvers.append(inter.author.id)
            await problem.update_self()
            return

    @commands.slash_command(
        name="vote",
        description="Vote for the deletion of a problem!",
        options=[
            Option(
                name="problem_id",
                description="problem id of the problem you are attempting to delete",
                type=OptionType.integer,
                required=True,
            ),
            Option(
                name="is_guild_problem",
                description="problem id of the problem you are attempting to delete",
                type=OptionType.boolean,
                required=False,
            ),
        ],
    )
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def vote(self, inter, problem_id: int, is_guild_problem: bool = False):
        """/vote [problem_id: int] [is_guild_problem: bool = False]
        Vote for the deletion of the problem with the given problem_id.
        if is_guild_problem is true, then the bot looks for the problem with the given problem id and guild id, and makes you vote for it.
        Otherwise, the bot looks for the global problem with given problem id (the guild id is None).
        There is a 5-second cooldown on this command, to prevent spam.
        The data about you voting is not private; it will be given to people who created/solved/voted for problems and use /user_data get_data"""
        try:
            problem = await self.bot.cache.get_problem(
                inter.guild.id
                if is_guild_problem
                else None,  # If it's a guild problem, set the guild id to the guild_id, otherwise set it to None
                problem_id=int(problem_id),  # Will probably have to change
            )  # Get the problem
            if problem.is_voter(
                inter.author
            ):  # You can't vote for a problem you already voted for!
                await inter.send(
                    embed=ErrorEmbed(
                        "You have already voted for the deletion of this problem!"
                    ),
                    ephemeral=True,
                )
                return  # Exit the command
        except problems_module.ProblemNotFound:
            await inter.send(  # The problem doesn't exist
                embed=ErrorEmbed("This problem doesn't exist!"), ephemeral=True
            )
            return
        await problem.add_voter(
            inter.author
        )  # Add the voter. Must be awaited because updating it in the cache is a coroutine.
        string_to_print = "You successfully voted for the problem's deletion! As long as this problem is not deleted, you can always un-vote. There are "
        string_to_print += f"{problem.get_num_voters()}/{self.bot.vote_threshold} votes on this problem!"  # Tell the user how many votes there are now
        await inter.send(
            embed=SuccessEmbed(string_to_print, title="You Successfully voted"),
            ephemeral=True,
        )
        if (
            problem.get_num_voters() >= self.bot.vote_threshold
        ):  # Has it passed the vote threshold?
            # If it did, delete the problem
            await self.bot.cache.remove_problem(
                guild_id=problem.guild_id, problem_id=problem.id
            )  # Remove the problem, after it passes the vote threshold
            await inter.send(  # May cause problems in a DM
                embed=SimpleEmbed(
                    "This problem has surpassed the threshold and has been deleted!"
                ),
                ephemeral=True,
            )
            return

    @commands.slash_command(
        name="unvote",
        description="Vote for the deletion of a problem",
        options=[
            Option(
                name="problem_id",
                description="problem id of the problem you are attempting to delete",
                type=OptionType.boolean,
                required=True,
            ),
            Option(
                name="is_guild_problem",
                description="problem id of the problem you are attempting to delete",
                type=OptionType.boolean,
                required=False,
            ),
        ],
    )
    @commands.cooldown(1, 5, commands.BucketType.user)
    @checks.is_not_blacklisted()
    async def unvote(
        self,
        inter: disnake.ApplicationCommandInteraction,
        problem_id: int,
        is_guild_problem: bool = False,
    ):
        """/unvote [problem_id: int] [is_guild_problem: bool = False]
        Searches for the problem with the given id. If is_guild_problem is True, the guild id of the problem that it searches for will be the guild id of the context.
        Otherwise, it will look for the global problem with the given id.
        After searching for the problem, it removes your vote for deletion of that problem.
        There is a 5-second cooldown on this command."""
        try:
            problem = await self.bot.cache.get_problem(
                inter.guild.id if is_guild_problem else None,
                problem_id=int(problem_id),
            )  # Get the problem!
            if not problem.is_voter(
                inter.author
            ):  # You can't un-vote unless you are voting
                await inter.send(
                    embed=ErrorEmbed(
                        "You can't un-vote because you are not voting for the deletion of this problem!"
                    ),
                    ephemeral=True,
                )
                return
        except problems_module.ProblemNotFound:
            await inter.send(  # The problem doesn't exist, get_problem will raise ProblemNotFound
                embed=ErrorEmbed("This problem doesn't exist!"), ephemeral=True
            )
            return
        problem.voters.remove(inter.author.id)  # Remove the user id from problem
        await problem.update_self()  # Save the changes to the database.

        successMessage = f"You successfully un-voted for the problem's deletion!" + (
            "As long as this problem is not deleted, you can always un-vote."
            + (
                "There are {problem.get_num_voters()}/{self.bot.vote_threshold} votes on this problem!"
            )
        )
        await inter.send(
            embed=SuccessEmbed(successMessage, successTitle="Successfully un-voted!"),
            ephemeral=True,
        )  # Tell the user of the successful un-vote.

    @commands.slash_command(
        name="delete_problem",
        description="Delete a problem",
        options=[
            Option(
                name="problem_id",
                description="Problem ID of the problem you want to delete.",
                type=OptionType.integer,
                required=True,
            ),
        ],
    )
    @commands.cooldown(1, 0.5, commands.BucketType.user)
    @commands.guild_only()
    async def delete_problem(
        self: "ProblemsCog",
        inter: disnake.ApplicationCommandInteraction,
        problem_id: int,
    ) -> typing.Optional[disnake.Message]:
        """/delete_problem (problem_id: int)
        Delete a problem. You must either have the Administrator permission in the guild, and the problem must be a guild problem, or be a trusted user.

        You do not need to specify whether the problem is a guild problem, as the bot can figure it out."""
        if inter.guild is not None:
            guild_id = inter.guild.id
        else:
            guild_id = None
        try:
            problem = await self.bot.cache.get_problem(guild_id, problem_id)
            can_delete: bool = False  # default
            if problem.author == inter.author.id:
                can_delete = True
            elif problem.guild_id is not None:
                if problem.guild_id != guild_id:
                    await inter.send(
                        "Wrong guild; Use this command in the guild with the problem"
                    )
                    return
                elif not inter.author.guild_permissions.administrator:
                    user_data: problems_module.UserData = (
                        await self.bot.cache.get_user_data(
                            user_id=inter.author.id,
                            default=UserData(
                                user_id=inter.author.id,
                                trusted=False,
                                blacklisted=False,
                            ),
                        )
                    )
                    if not user_data.trusted:
                        await inter.send("Insufficient permissions.")
                        return
                can_delete = True
            else:
                user_data: problems_module.UserData = (
                    await self.bot.cache.get_user_data(
                        user_id=inter.author.id,
                        default=UserData(
                            user_id=inter.author.id, trusted=False, blacklisted=False
                        ),
                    )
                )
                if not user_data.trusted:
                    await inter.send("Insufficient permissions.")
                    return
                can_delete = True

        except problems_module.ProblemNotFound:
            return await inter.send(
                embed=ErrorEmbed("Problem not found. Cannot delete")
            )
        if not can_delete:
            await inter.send(
                embed=ErrorEmbed("You don't have permission to delete this problem!"),
                ephemeral=True,
            )
            return
        await self.cache.remove_problem(guild_id, problem_id)
        await inter.send(
            embed=SuccessEmbed(
                f"Successfully deleted problem the problem with id {problem_id}!"
            ),
            ephemeral=True,
        )


def setup(bot: disnake.ext.commands.Bot):
    bot.add_cog(ProblemsCog(bot))


def teardown(bot: disnake.ext.commands.Bot):
    bot.remove_cog(ProblemsCog)
