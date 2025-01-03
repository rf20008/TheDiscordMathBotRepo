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
import traceback
import typing

import disnake
from disnake import Option, OptionChoice, OptionType
from disnake.ext import commands, tasks

from helpful_modules import custom_bot, custom_embeds, the_documentation_file_loader
from helpful_modules.custom_embeds import ErrorEmbed, SuccessEmbed
from helpful_modules.paginator_view import PaginatorView

TYPES_TO_NAMES = {
    commands.InvokableUserCommand: "user",
    commands.InvokableSlashCommand: "slash",
    commands.InvokableMessageCommand: "msg",
}
try:
    import orjson as json
except (ImportError, ModuleNotFoundError):
    pass
from .helper_cog import HelperCog

FILENAME = "help.json"


class HelpCog(HelperCog):
    def __init__(self, bot):
        super().__init__(bot)
        self.bot = bot
        self.cache = bot.cache
        self.cached_command_dict = {}
        self.precomputed_command_list_msg = ""
        self.cached_command_dict_by_cog={}

    @tasks.loop(seconds=86400)
    async def task_update_cached_command_dict(self):
        self.update_cached_command_dict()

    def update_cached_command_dict(self):
        new_cached_command_dict_by_cog = {
            "slash": {},
            "user": {},
            "message": {},
        }
        new_cached_command_dict = {
            "slash": {},
            "user": {},
            "message": {},
        }
        commands_existing = self.bot.application_commands
        for command in commands_existing:
            if not isinstance(
                command,
                (
                    commands.InvokableSlashCommand,
                    commands.InvokableMessageCommand,
                    commands.InvokableUserCommand,
                ),
            ):
                raise TypeError(
                    f"I expected all of my commands to be instances of InvokableSlashCommand, InvokableMessageCommand, or InvokableUserCommand; "
                    "however, one my commands is {command} of type {command.__class__.__name__}."
                )
            if TYPES_TO_NAMES[type(command)] not in new_cached_command_dict:
                new_cached_command_dict[TYPES_TO_NAMES[type(command)]] = {}
            new_cached_command_dict[TYPES_TO_NAMES[type(command)]][
                command.qualified_name
            ] = command
            try:
                new_cached_command_dict_by_cog[TYPES_TO_NAMES[type(command)]][
                    command.cog_name
                ].append(command)
            except KeyError:
                new_cached_command_dict_by_cog[TYPES_TO_NAMES[type(command)]][
                    command.cog_name
                ] = [command]
        self.cached_command_dict = new_cached_command_dict
        self.cached_command_dict_by_cog=new_cached_command_dict_by_cog
        msg = "`Your command was not found. Here is a list of my commands!\n```"
        for cmd_type in ["slash", "user", "message"]:
            msg += f"{cmd_type.title()} commands:\n"
            for cogName, cogCommands in self.cached_command_dict_by_cog[cmd_type].items():
                msg += f"    Cog {cogName}\n"
                for command in cogCommands:
                    msg += (
                        (" " * 8)
                        + command.name
                        + "\n\t"
                        + (" " * 8)
                        + command.description
                        + "\n"
                    )
        self.precomputed_command_list_msg = msg + "```"

    @commands.slash_command(
        name="help",
        description="This is the beginnings of the help command. If you do not specify a command I will DM you.",
    )
    async def help(
        self, inter: disnake.ApplicationCommandInteraction, cmd: str, cmd_type: str
    ):
        """/help cmd:str cmd_type: str
        Get help!
        cmd_type should be "slash", "user", or "message".
        If you post a command that does not exist then I will attempt to give you a list of all my commands in a DM! Otherwise I will give you the docstring if it exists.
        #"""
        if cmd_type not in ("slash", "user", "msg"):
            return await inter.send(
                embed=custom_embeds.ErrorEmbed(
                    'The only supported cmd_types are "slash", "user", and "msg".'
                )
            )
        if str == "":
            return await inter.send(
                embed=custom_embeds.ErrorEmbed(
                    "Unfortunately, you need to provide a command so I can help you!"
                )
            )
        command = None
        try:
            self.update_cached_command_dict()
            print(self.cached_command_dict[cmd_type])
            command = self.cached_command_dict[cmd_type][cmd]
            print("Command:", command)
            return await inter.send(
                embed=custom_embeds.SuccessEmbed(command.callback.__doc__)
            )
        except KeyError as ke:
            print("".join(traceback.format_exception(ke)))
            try:
                await inter.user.send(
                    embed=custom_embeds.SuccessEmbed(self.precomputed_command_list_msg)
                )
                await inter.send("I have sent you a DM with all my commands!")
            except disnake.Forbidden as e:
                msg = (
                    "I could not DM you! Maybe your DMs are closed...\n"
                    + self.precomputed_command_list_msg
                )
                await inter.send(embed=ErrorEmbed(msg))
                raise e
            return

    @commands.cooldown(1, 1, commands.BucketType.user)
    @commands.slash_command(
        name="documentation",
        description="Returns help!",
        options=[
            Option(
                name="documentation_type",
                description="What kind of help you want",
                choices=[
                    OptionChoice(name="documentation_link", value="documentation_link"),
                    OptionChoice(name="command_help", value="command_help"),
                    OptionChoice(name="function_help", value="function_help"),
                    OptionChoice(name="privacy_policy", value="privacy_policy"),
                    OptionChoice(name="terms_of_service", value="terms_of_service"),
                ],
                required=True,
            ),
            Option(
                name="help_obj",
                description="What you want help on",
                required=False,
                type=OptionType.string,
            ),
        ],
    )
    async def documentation(
        self,
        inter: disnake.ApplicationCommandInteraction,
        documentation_type: typing.Literal[
            "documentation_link",  # type: ignore
            "command_help",
            "function_help",
            "privacy_policy",
            "terms_of_service",
            "I just want general help",
        ],
        help_obj: str = None,
    ) -> typing.Optional[disnake.Message]:
        """/documentation {documentation_type: str|documentation_link|command_help|function_help} {help_obj}

        Prints documentation :-). If the documentation is a command, it attempts to get its docstring.
        Otherwise, it gets the cached documentation.
        help_obj will be ignored if documentation_type is privacy_policy or documentation_link.
        Legend (for other documentation)
        /command_name: the command
        {argument_name: type |choice1|choice2|...} (for a required argument with choices of the given type, and the available choices are choice1, choice 2, etc.)
        {argument_name: type |choice1|choice2|... = default} (an optional argument that defaults to default if not specified. Arguments must be a choice specified(from choice 1 etc.) and must be of the type specified.)
        [argument_name: type = default] (an argument with choices of the given type, and defaults to default if not specified. Strings are represented without quotation marks.)
        (argument_name: type) A required argument of the given type"""
        if help_obj is None and documentation_type in ["command_help", "function_help"]:
            return await inter.send(
                embed=ErrorEmbed(
                    "I can't help you with a command or function unless you tell me what you want help on!"
                )
            )

        if documentation_type == "documentation_link":
            await inter.send(
                embed=SuccessEmbed(
                    f"""<@{inter.author.id}> [Click here](https://github.com/rf20008/TheDiscordMathProblemBotRepo/tree/master/docs) for my documentation.
        Warning: It is deprecated
        """
                ),
                ephemeral=True,
            )
            return None
        if documentation_type == "command_help":
            try:
                command = self.bot.get_slash_command(help_obj)  # Get the command
                if command is None:  # command not found
                    return await inter.send(
                        embed=ErrorEmbed(
                            custom_title="I couldn't find your command!",
                            description=":x: Could not find the command specified. ",
                        )
                    )
                command_docstring = command.callback.__doc__
                if command_docstring is None:
                    return await inter.send(
                        "Oh no! This command does not have documentation! Please report this bug."
                    )
                return await inter.send(
                    embed=SuccessEmbed(description=str(command_docstring))
                )
            except AttributeError as exc:
                # My experiment failed
                raise Exception("uh oh...") from exc  # My experiment failed!
        elif documentation_type == "function_help":
            documentation_loader = (
                the_documentation_file_loader.DocumentationFileLoader()
            )
            try:
                _documentation = documentation_loader.get_documentation(
                    {
                        "function_help": "docs/misc-non-commands-documentation.md",
                    }[documentation_type],
                    help_obj,
                )
            except the_documentation_file_loader.DocumentationNotFound as e:
                if isinstance(
                    e, the_documentation_file_loader.DocumentationFileNotFound
                ):
                    await inter.send(
                        embed=ErrorEmbed(
                            "Documentation file was not found. Please report this error!"
                        )
                    )
                    return None
                await inter.send(embed=ErrorEmbed(str(e)))
                return None
            await inter.send(_documentation)
        elif documentation_type == "privacy_policy":
            with open("PRIVACY_POLICY.md") as file:
                text = "".join(file.readlines())

            await inter.send(
                view=await PaginatorView.paginate(
                    text=text, user_id=inter.author.id, max_page_length=2300
                )
            )  # Concatenate the lines in the file and send them
            return
        elif documentation_type == "terms_of_service":
            with open("TERMS_AND_CONDITIONS.md") as file:
                text = "".join(file.readlines())

            await inter.send(
                view=await PaginatorView.paginate(
                    text=text, user_id=inter.author.id, max_page_length=2300
                )
            )  # Concatenate the lines in the file and send them
            return
        else:
            raise NotImplementedError(
                "This hasn't been implemented yet. Please contribute something!"
            )

    async def cog_load(self):
        await self.update_cached_command_dict()


def setup(bot: custom_bot.TheDiscordMathProblemBot):
    bot.add_cog(HelpCog(bot))


def teardown(bot: custom_bot.TheDiscordMathProblemBot):
    bot.remove_cog("HelpCog")
