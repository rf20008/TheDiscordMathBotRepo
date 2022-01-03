"""Admin-related commands. Licensed under GPLv3"""
import random
import typing
from copy import copy

import disnake
from disnake import *
from disnake.ext import commands

from helpful_modules import checks
from helpful_modules import cooldowns, the_documentation_file_loader
from helpful_modules import problems_module
from helpful_modules.custom_bot import TheDiscordMathProblemBot
from helpful_modules.custom_embeds import *
from helpful_modules.save_files import FileSaver
from helpful_modules.threads_or_useful_funcs import generate_new_id
from .helper_cog import HelperCog

slash = None


class DeveloperCommands(HelperCog):
    def __init__(self, bot: TheDiscordMathProblemBot):

        super().__init__(bot)
        self.bot: TheDiscordMathProblemBot = bot
        # checks = self.checks
        checks.setup(bot)

    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.slash_command(
        name="force_load_files",
        description="Force loads files to replace dictionaries. THIS WILL DELETE OLD DICTS!",
    )
    @checks.trusted_users_only()
    async def force_load_files(
            self, inter: disnake.ApplicationCommandInteraction
    ) -> None:
        """Forcefully load files. You must be a trusted user to do this command.
        This command does not take any user-provided arguments."""

        if inter.author.id not in self.bot.trusted_users:
            await inter.send(
                ErrorEmbed(
                    """You aren't a trusted user.
                    Therefore, you don't have permission to force-load files."""
                )
            )
            return
        try:
            FileSaver3 = FileSaver(enabled=True, printSuccessMessagesByDefault=False)
            FileSaverDict = FileSaver3.load_files(self.bot.cache)
            (guildMathProblems, self.bot.trusted_users, self.bot.vote_threshold) = (
                FileSaverDict["guildMathProblems"],
                FileSaverDict["trusted_users"],
                FileSaverDict["vote_threshold"],
            )
            FileSaver3.goodbye()
            del guildMathProblems
            await inter.send(
                embed=SuccessEmbed("Successfully forcefully loaded files!")
            )
            return
        except RuntimeError:
            await inter.send(embed=ErrorEmbed("Something went wrong..."))
            # return
            raise  # I actually want to fix this bug!

    @commands.cooldown(1, 5)
    @commands.slash_command(
        name="force_save_files",
        description="Forcefully saves files (can only be used by trusted users).",
    )
    @checks.trusted_users_only()
    async def force_save_files(self, inter: disnake.ApplicationCommandInteraction):
        """/force_save_files.
        Forcefully saves files. Takes no arguments. Mostly for debugging purposes.
        You must be a trusted user to do this!
        There is a 5-second cooldown on this command."""

        if inter.author.id not in self.bot.trusted_users:
            await inter.send(
                embed=ErrorEmbed(
                    "You aren't trusted and therefore don't have permission to force save files."
                )
            )
            return
        try:
            FileSaver2 = FileSaver(enabled=True)
            FileSaver2.save_files(
                self.bot.cache,
                True,
                {},
                self.bot.vote_threshold,
                {},
                self.bot.trusted_users,
            )
            FileSaver2.goodbye()
            await inter.send(embed=SuccessEmbed("Successfully saved 4 files!"))
        except RuntimeError as exc:
            await inter.send(embed=ErrorEmbed("Something went wrong..."))
            raise exc

    @commands.is_owner()
    @checks.trusted_users_only()
    @commands.cooldown(1, 5, type=disnake.ext.commands.BucketType.user)
    @commands.slash_command(
        name="raise_error",
        description="⚠ This command will raise an error. Useful for testing on_slash_command_error",
        options=[
            Option(
                name="error_type",
                description="The type of error",
                choices=[OptionChoice(name="Exception", value="Exception")],
                required=True,
            ),
            Option(
                name="error_description",
                description="The description of the error",
                type=OptionType.string,
                required=False,
            ),
        ],
    )
    async def raise_error(
            self,
            inter: disnake.ApplicationCommandInteraction,
            error_type: typing.Literal["Exception"],  # type: ignore
            error_description: str = None,
    ) -> None:
        """/raise_error {error_type: str|Exception} [error_description: str = None]
        This command raises an error (of type error_type) that has the description of the error_description.
        You must be a trusted user and the bot owner to run this command!
        The purpose of this command is to test the bot's on_slash_command_error event!"""
        if (
                inter.author.id not in self.bot.trusted_users
        ):  # Check that the user is a trusted user
            await inter.send(
                embed=ErrorEmbed(
                    f"⚠ {inter.author.mention}, you do not have permission to intentionally raise errors for debugging purposes.",
                    custom_title="Insufficient permission to raise errors.",
                ),
                allowed_mentions=disnake.AllowedMentions(
                    everyone=False, users=[], roles=[], replied_user=False
                ),
            )
            return
        if error_description is None:
            error_description = f"Manually raised error by {inter.author.mention}"
        if error_type == "Exception":
            error = Exception(error_description)
        else:
            raise RuntimeError(f"Unknown error: {error_type}")
        await inter.send(
            embed=SuccessEmbed(
                f"Successfully created error: {str(error)}. Will now raise the error.",
                successTitle="Successfully raised error.",
            )
        )
        raise error

    @commands.slash_command(
        name="debug",
        description="Helpful for debugging :-)",
        options=[
            Option(
                name="raw",
                description="raw debug data?",
                type=OptionType.boolean,
                required=False,
            ),
            Option(
                name="send_ephemerally",
                description="Send the debug message ephemerally?",
                type=OptionType.boolean,
                required=False,
            ),
        ],
    )
    async def debug(
            self,
            inter: disnake.ApplicationCommandInteraction,
            raw: bool = False,
            send_ephermally: bool = True,
    ):
        """/debug [raw: bool = False] [send_ephermally: bool = False]
        Provides helpful debug information :-)"""
        guild = inter.guild  # saving me typing trouble!
        if inter.guild is None:
            await inter.send(content="This command can only be ran in servers!")
            return
        me = guild.me
        my_permissions = me.guild_permissions
        debug_dict = {
            "guild_id": inter.guild.id,
            "author_id": inter.author.id,
            "problem_limit": self.bot.cache.max_guild_problems,
            "reached_max_problems": "✅"
            if len(await self.bot.cache.get_guild_problems(inter.guild))
               >= self.bot.cache.max_guild_problems
            else "❌",
            "num_guild-problems": len(
                await self.bot.cache.get_guild_problems(inter.guild)
            ),
        }
        correct_permissions = {
            "read_message_history": "✅" if my_permissions.read_messages else "❌",
            "read_messages": "✅"
            if my_permissions.read_messages
            else "❌",  # can I read messages?
            "send_messages": "✅"
            if my_permissions.send_messages
            else "❌",  # can I send messages?
            "embed_links": "✅"
            if my_permissions.embed_links
            else "❌",  # can I embed links?
            "use_application_commands": "✅"
            if my_permissions.use_slash_commands
            else "❌",
        }
        debug_dict["correct_permissions"] = correct_permissions
        if raw:
            await inter.send(str(debug_dict), ephemeral=send_ephermally)
            return
        else:
            text = ""
            for item in debug_dict:
                if not isinstance([item], dict):
                    text += f"{item}: {debug_dict.get(item)}\n"
                else:
                    for item2 in item:
                        if not isinstance(item2, dict):
                            text += f"{item.get(item2)}: {debug_dict[item]}"
                        else:
                            raise RecursionError("uh oh") from Exception(
                                "***Nested too much***"
                            )

        await inter.send(text, ephemeral=send_ephermally)

    @commands.slash_command(
        name="generate_new_problems",
        description="Generates new problems",
        options=[
            Option(
                name="num_new_problems_to_generate",
                description="the number of problems that should be generated",
                type=OptionType.integer,
                required=True,
            )
        ],
    )
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def generate_new_problems(
            self,
            inter: disnake.ApplicationCommandInteraction,
            num_new_problems_to_generate: int,
    ) -> typing.Optional[disnake.Message]:
        """/generate_new_problems [num_new_problems_to_generate: int]
        Generate new Problems."""
        # TODO: problem_generator class (and use formulas :-))
        await inter.response.defer()
        if inter.author.id not in self.bot.trusted_users:
            await inter.send(embed=ErrorEmbed("You aren't trusted!"), ephemeral=True)
            return
        if num_new_problems_to_generate > 200:
            return await inter.send(
                embed=ErrorEmbed(
                    "You are trying to create too many problems. Try something smaller than or equal to 200."
                ),
                ephemeral=True,
            )

        for i in range(num_new_problems_to_generate):  # basic problems for now.... :(
            # TODO: linear equations, etc

            operation = random.choice(["+", "-", "*", "/", "^"])
            if operation == "^":
                num1 = random.randint(1, 20)
                num2 = random.randint(1, 20)
            else:
                num1 = random.randint(-1000, 1000)
                num2 = random.randint(-1000, 1000)
                while num2 == 0 and operation == "/":  # Prevent ZeroDivisionError
                    num2 = random.randint(-1000, 1000)

            if operation == "^":
                try:
                    answer = num1 ** num2

                except OverflowError:  # Too big?
                    try:
                        del answer
                    except NameError:
                        pass
                    continue
            elif operation == "+":
                answer = num1 + num2
            elif operation == "-":
                answer = num1 - num2
            elif operation == "*":
                answer = num1 * num2
            elif operation == "/":
                answer = round(num1 * 100 / num2) / 100

            while True:
                problem_id = generate_new_id()
                if problem_id not in [
                    problem.id for problem in await self.cache.get_global_problems()
                ]:  # All problem_ids
                    break
            question = (
                    f"What is {num1} "
                    + {
                        "*": "times",
                        "+": "times",
                        "-": "minus",
                        "/": "divided by",
                        "^": "to the power of",
                    }[operation]
                    + f" {str(num2)}?"
            )
            Problem = problems_module.BaseProblem(
                question=question,
                answer=str(answer),
                author=845751152901750824,
                guild_id=None,
                id=problem_id,
                cache=copy(self.cache),
            )
            await self.cache.add_problem(problem_id, Problem)
        await inter.send(
            embed=SuccessEmbed(
                f"Successfully created {str(num_new_problems_to_generate)} new problems!"
            ),
            ephemeral=True,
        )

    @commands.slash_command(
        name="add_trusted_user",
        description="Adds a trusted user",
        options=[
            Option(
                name="user",
                description="The user you want to give super special bot access to",
                type=OptionType.user,
                required=True,
            )
        ],
    )
    @checks.trusted_users_only()
    @checks.is_not_blacklisted()
    @commands.cooldown(1, 600, commands.BucketType.user)
    async def add_trusted_user(
            self,
            inter: disnake.ApplicationCommandInteraction,
            user: typing.Union[disnake.Member, disnake.User],
    ) -> None:
        """/add_trusted_user [user: User]
        This slash commands adds a trusted user!
        You must be a trusted user to add a trusted user, and the user you are trying to make a trusted user must not be a trusted user.
        You must also share a server with the new trusted user."""
        user_data = await self.bot.cache.get_user_data(
            user_id=user.id,
            default=problems_module.UserData(
                user_id=user.id, trusted=False, blacklisted=False
            ),
        )

        # if inter.author.id not in self.bot.trusted_users: # Should work
        #    await inter.send(
        #        embed=ErrorEmbed("You aren't a trusted user!"), ephemeral=True
        #    )
        #    return
        if user_data.trusted:
            await inter.send(
                embed=ErrorEmbed(f"{user.name} is already a trusted user!"),
                ephemeral=True,
            )
            return
        user_data.trusted = True
        try:
            await self.cache.set_user_data(user.id, new=user_data)
        except problems_module.UserDataNotExistsException:
            await self.cache.add_user_data(user=user.id, thing_to_add=user_data)

        await inter.send(
            embed=ErrorEmbed(f"Successfully made {user.nick} a trusted user!"),
            ephemeral=True,
        )
        return

    @commands.slash_command(
        name="remove_trusted_user",
        description="removes a trusted user",
        options=[
            Option(
                name="user",
                description="The user you want to take super special bot access from",
                type=OptionType.user,
                required=True,
            )
        ],
    )
    @commands.cooldown(1, 600, commands.BucketType.user)
    @checks.trusted_users_only()
    async def remove_trusted_user(
            self: "DeveloperCommands",
            inter: disnake.ApplicationCommandInteraction,
            user: disnake.User,
    ) -> typing.Optional[disnake.InteractionMessage]:
        """/remove_trusted_user [user: User]
        Remove a trusted user. You must be a trusted user to do this.
        There is also a 10-minute cooldown to prevent raids!"""
        my_user_data = await self.cache.get_user_data(inter.author.id, default=problems_module.UserData(
            user_id=inter.author.id,
            trusted=False,
            blacklisted=False
        ))
        if not my_user_data.trusted:
            await inter.send(
                embed=ErrorEmbed("You aren't a trusted user!"), ephemeral=True
            )
            return
        their_user_data = await self.cache.get_user_data(user.id, default=problems_module.UserData(
            trusted=False,
            user_id=user.id,
            blacklisted=False
        ))
        if not their_user_data.trusted:
            await inter.send(
                embed=ErrorEmbed(f"{user.name} isn't a trusted user!"), ephemeral=True
            )
            return
        their_user_data.trusted = False
        try:
            await self.cache.set_user_data(user_id=user.id, new=their_user_data)
        except problems_module.UserDataNotExistsException:
            await self.cache.add_user_data(user_id=user_id, thing_to_add=user_data)
        await inter.send(
            embed=ErrorEmbed(
                f"Successfully made {user.display_name} no longer a trusted user!"
            ),
            ephemeral=True,
        )


def setup(bot: TheDiscordMathProblemBot):
    bot.add_cog(DeveloperCommands(bot))


def teardown(bot):
    bot.remove_cog("DeveloperCommands")
