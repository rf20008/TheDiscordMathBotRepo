import disnake
from disnake.ext import commands, tasks
from disnake import OptionChoice, Option, OptionType
import typing
from typing import Optional
import aiofiles
from helpful_modules import (
    custom_bot,
    custom_embeds,
    _error_logging,
    checks,
    dict_factory,
    FileDictionaryReader,
)
import json
from collections import defaultdict

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
        self.bot = bot
        self.cache = bot.cache
        self.cached_command_dict = {}
        self.precomputed_command_list_msg = ""

    @tasks.loop(seconds=86400)
    async def task_update_cached_command_dict(self):
        self.update_cached_command_dict()

    def update_cached_command_dict(self):
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

            try:
                new_cached_command_dict[TYPES_TO_NAMES[type(command)]][
                    command.cog.qualified_name
                ].append(command)
            except KeyError:
                new_cached_command_dict[TYPES_TO_NAMES[type(command)]][
                    command.cog.qualified_name
                ] = [command]
        self.cached_command_dict = new_cached_command_dict
        msg = "`Your command was not found. Here is a list of my commands!\n```"
        for cmd_type in ["slash", "user", "message"]:
            msg += f"{cmd_type.title()} commands:\n"
            for cogName, cogCommands in self.cached_command_dict[cmd_type].items():
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
            command = self.cached_command_dict[cmd_type][cmd]
            return await inter.send(
                embed=custom_embeds.SuccessEmbed(command.callback.__doc__)
            )
        except KeyError:
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
                await inter.send(
                    embed=SuccessEmbed("".join([str(line) for line in file]))
                )  # Concatenate the lines in the file and send them
            return
        elif documentation_type == "terms_of_service":
            with open("TERMS_AND_CONDITIONS.md") as file:
                await inter.send(
                    embed=SuccessEmbed("".join([line for line in file]))
                )  # Concatenate the lines in the file + send them
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
