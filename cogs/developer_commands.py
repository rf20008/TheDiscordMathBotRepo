"""Admin-related commands. Licensed under GPLv3"""
import random
import typing
from copy import copy

import disnake
from disnake.ext import commands

from helpful_modules import checks, problems_module
from helpful_modules.custom_bot import TheDiscordMathProblemBot
from helpful_modules.custom_embeds import ErrorEmbed, SimpleEmbed, SuccessEmbed
from helpful_modules.save_files import FileSaver
from helpful_modules.threads_or_useful_funcs import generate_new_id

from .helper_cog import HelperCog

slash = None


class DeveloperCommands(HelperCog):
    def __init__(self, bot: TheDiscordMathProblemBot):

        super().__init__(bot)
        self.bot: TheDiscordMathProblemBot = bot
        # checks = self.checks
        try:
            checks.setup(bot)
        except AttributeError:
            pass

    async def cog_check(self, inter: disnake.ApplicationCommandInteraction | commands.Context) -> bool:
        """Return whether the user can use the command"""
        if await self.bot.is_owner(inter.author):
            return True

        if await self.bot.is_trusted(inter.author):
            return True
        if await self.bot.is_blacklisted(inter.author):
            await inter.send("You cannot use this command because you are blacklisted.")
            return False
        await inter.send("These commands are only for my developers!")
        return False

    # TODO: make these commands guild-only commands or get rid of the commands entirely

    @checks.has_privileges(blacklisted=False)
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
                embed=ErrorEmbed(
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

    @checks.has_privileges(blacklisted=False)
    @commands.cooldown(1, 5)
    @checks.trusted_users_only()
    @commands.slash_command(
        name="force_save_files",
        description="Forcefully saves files (can only be used by trusted users).",
    )
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
    @checks.has_privileges(blacklisted=False)
    @commands.cooldown(1, 5, type=disnake.ext.commands.BucketType.user)
    @commands.slash_command(
        name="raise_error",
        description="⚠ This command will raise an error. Useful for testing on_slash_command_error",
        options=[
            disnake.Option(
                name="error_type",
                description="The type of error",
                choices=[disnake.OptionChoice(name="Exception", value="Exception")],
                required=True,
            ),
            disnake.Option(
                name="error_description",
                description="The description of the error",
                type=disnake.OptionType.string,
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
        This command raises an error (of type error_type) that has the description provided.
        You must be a trusted user and the bot owner to run this command!
        The purpose of this command is to test the bot's on_slash_command_error event!"""
        # if (
        #        inter.author.id not in self.bot.trusted_users
        # ):  # Check that the user is a trusted user
        #    await inter.send(
        #        embed=ErrorEmbed(
        #            f"⚠ {inter.author.mention}, you do not have permission to intentionally raise errors for debugging purposes.",
        #            custom_title="Insufficient permission to raise errors.",
        #        ),
        #        allowed_mentions=disnake.AllowedMentions(
        #            everyone=False, users=[], roles=[], replied_user=False
        #        ),
        #    )
        #    return
        if not await self.bot.is_trusted(inter.author):
            return await inter.send("You don't have permission!")
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

    async def humanify_check(check: problems_module.CheckForUserPassage, guild: disnake.Guild):
        roles_needed =" ".join([guild.get_role(role_id).name for role in check.roles_allowed])
        permissions_needed = check.permissions_needed
        whitelisted_user_ids = " ".join(check.whitelisted_users) # We can't show the names because no members intent
        blacklisted_users_ids = " ".join(check.blacklisted_users)
        return f"The roles needed are {roles_needed} and the permissions needed are {permissions_needed} and the whitelisted user ids are {whitelisted_user_ids} and the blacklisted user ids are {blacklisted_user_ids}"
        

    
    @checks.has_privileges(blacklisted=False)
    @commands.slash_command(
        name="debug",
        description="Helpful for debugging :-)",
        options=[
            disnake.Option(
                name="raw",
                description="raw debug data?",
                type=disnake.OptionType.boolean,
                required=False,
            ),
            disnake.Option(
                name="send_ephemerally",
                description="Send the debug message ephemerally?",
                type=disnake.OptionType.boolean,
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
        guild_data = await self.bot.cache.get_guild_data(guild_id)
        
        debug_dict = {
            "Server Guild ID": inter.guild.id,
            "Invoker's user ID": inter.author.id,
            "Maximum number of guild-only problems allowed.": self.bot.cache.max_guild_problems,
            "Has this guild reached the maximum number of problems?": "✅"
            if len(await self.bot.cache.get_guild_problems(inter.guild))
            >= self.bot.cache.max_guild_problems
            else "❌",
            "Number of guild-only problems": len(
                await self.bot.cache.get_guild_problems(inter.guild)
            ),
            "Guild info": {
                "Checks": {
                    "Mod check": self.humanify_check(guild_data.mod_check),
                    "Can create problems check": self.humanify_check(guild_data.can_create_problems_check)
                }
            }
        }
        correct_permissions = {
            "Read Message History": "✅" if my_permissions.read_messages else "❌",
            "Read Messages": "✅"
            if my_permissions.read_messages
            else "❌",  # can I read messages?
            "Send Messages": "✅"
            if my_permissions.send_messages
            else "❌",  # can I send messages?
            "Embed Links": "✅"
            if my_permissions.embed_links
            else "❌",  # can I embed links?
            "Use Slash Commands": "✅" if my_permissions.use_slash_commands else "❌",
        }

        debug_dict["Do I have the correct permissions?"] = correct_permissions
        if raw:
            await inter.send(str(debug_dict), ephemeral=send_ephermally)
            return
        else:
            text = ""
            for key in debug_dict.keys():
                val = debug_dict[key]
                if not isinstance(val, dict):
                    text += f"{key}: {val}\n"
                else:
                    text += key + "\n"
                    if isinstance(val, dict):
                        for k in val.keys():
                            v = val[k]
                            text += f"\t{k}: {v}\n"

        await inter.send(text, ephemeral=send_ephermally)

    @commands.cooldown(1, 30, commands.BucketType.user)
    @commands.slash_command(
        name="generate_new_problems",
        description="Generates new problems",
        options=[
            disnake.Option(
                name="num_new_problems_to_generate",
                description="the number of problems that should be generated",
                type=disnake.OptionType.integer,
                required=True,
            )
        ],
    )
    async def generate_new_problems(
        self,
        inter: disnake.ApplicationCommandInteraction,
        num_new_problems_to_generate: int,
    ) -> typing.Optional[disnake.Message]:
        """/generate_new_problems [num_new_problems_to_generate: int]
        Generate new Problems."""
        # TODO: problem_generator class (and use formulas :-))
        await inter.response.defer()
        if not await self.bot.is_trusted(inter.author):
            await inter.send(embed=ErrorEmbed("You aren't trusted!"), ephemeral=True)
            return
        if num_new_problems_to_generate > 200:
            return await inter.send(
                embed=ErrorEmbed(
                    "You are trying to create too many problems."
                    "Try something smaller than or equal to 200."
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
                    answer = num1**num2

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

    @checks.trusted_users_only()
    @checks.is_not_blacklisted()
    @commands.cooldown(1, 600, commands.BucketType.user)
    @checks.has_privileges(blacklisted=False)
    @commands.slash_command(
        name="add_trusted_user",
        description="Adds a trusted user",
        options=[
            disnake.Option(
                name="user",
                description="The user you want to give super special bot access to",
                type=disnake.OptionType.user,
                required=True,
            )
        ],
    )
    async def add_trusted_user(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: typing.Union[disnake.Member, disnake.User],
    ) -> None:
        """/add_trusted_user [user: User]
        This slash commands adds a trusted user!
        You must be a trusted user to add a trusted user.
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

    @commands.cooldown(1, 600, commands.BucketType.user)
    @checks.trusted_users_only()
    @checks.has_privileges(blacklisted=False)
    @commands.slash_command(
        name="remove_trusted_user",
        description="removes a trusted user",
        options=[
            disnake.Option(
                name="user",
                description="The user you want to take super special bot access from",
                type=disnake.OptionType.user,
                required=True,
            )
        ],
    )
    async def remove_trusted_user(
        self: "DeveloperCommands",
        inter: disnake.ApplicationCommandInteraction,
        user: disnake.User,
    ) -> typing.Optional[disnake.InteractionMessage]:
        """/remove_trusted_user [user: User]
        Remove a trusted user. You must be a trusted user to do this.
        There is also a 10-minute cooldown to prevent raids!"""
        my_user_data = await self.cache.get_user_data(
            inter.author.id,
            default=problems_module.UserData(
                user_id=inter.author.id, trusted=False, blacklisted=False
            ),
        )
        if not my_user_data.trusted:
            await inter.send(
                embed=ErrorEmbed("You aren't a trusted user!"), ephemeral=True
            )
            return
        their_user_data = await self.cache.get_user_data(
            user.id,
            default=problems_module.UserData(
                trusted=False, user_id=user.id, blacklisted=False
            ),
        )
        if not their_user_data.trusted:
            await inter.send(
                embed=ErrorEmbed(f"{user.name} isn't a trusted user!"), ephemeral=True
            )
            return
        their_user_data.trusted = False
        try:
            await self.cache.set_user_data(user_id=user.id, new=their_user_data)
        except problems_module.UserDataNotExistsException:
            await self.cache.add_user_data(
                user_id=user.id, thing_to_add=their_user_data
            )
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
