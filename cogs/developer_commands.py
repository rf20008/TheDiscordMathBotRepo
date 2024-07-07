"""Admin-related commands. Licensed under GPLv3"""

import random
import typing
import warnings
from copy import copy

import disnake
from disnake import *
from disnake.ext import commands

from helpful_modules import (
    checks,
    cooldowns,
    problems_module,
    the_documentation_file_loader,
)
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
        warnings.warn(
            "Since I have been migrated from using files to a SQL database, this command is deprecated!"
        )
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
        You must be the owner of this bot and be a trusted user to have permission to run this command (although I suppose anybody could run it).
        The purpose of this command is to test the bot's on_slash_command_error event!
        """
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
            "Server Guild ID": inter.guild.id,
            "Invoker's user ID": inter.author.id,
            "Maximum number of guild-only problems allowed.": self.bot.cache.max_guild_problems,
            "Has this guild reached the maximum number of problems?": (
                "✅"
                if len(await self.bot.cache.get_guild_problems(inter.guild))
                >= self.bot.cache.max_guild_problems
                else "❌"
            ),
            "Number of guild-only problems": len(
                await self.bot.cache.get_guild_problems(inter.guild)
            ),
        }
        correct_permissions = {  # todo: don't hardcode
            "Read Message History": "✅" if my_permissions.read_messages else "❌",
            "Read Messages": (
                "✅" if my_permissions.read_messages else "❌"
            ),  # can I read messages?
            "Send Messages": (
                "✅" if my_permissions.send_messages else "❌"
            ),  # can I send messages?
            "Embed Links": (
                "✅" if my_permissions.embed_links else "❌"
            ),  # can I embed links?
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
    @checks.is_not_denylisted()
    @commands.cooldown(2, 600, commands.BucketType.user)
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
                user_id=user.id, trusted=False, denylisted=False
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
            embed=SuccessEmbed(f"Successfully made {user.name} a trusted user!"),
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
    @checks.is_not_denylisted()
    @checks.trusted_users_only()
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
                user_id=inter.author.id, trusted=False, denylisted=False
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
                trusted=False, user_id=user.id, denylisted=False
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
            embed=SuccessEmbed(
                f"Successfully made {user.global_name} no longer a trusted user!"
            ),
            ephemeral=True,
        )


def setup(bot: TheDiscordMathProblemBot):
    bot.add_cog(DeveloperCommands(bot))


def teardown(bot):
    bot.remove_cog("DeveloperCommands")
