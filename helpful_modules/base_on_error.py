import asyncio
import datetime
import logging
import traceback
from copy import deepcopy
from sys import exc_info, stderr
from time import asctime

import disnake
from disnake.ext import commands
import subprocess
from ._error_logging import log_error
from .cooldowns import OnCooldown
from .custom_embeds import *
from .problems_module.errors import LockedCacheException

from .the_documentation_file_loader import DocumentationFileLoader


def get_git_revision_hash() -> str:
    """A method that gets the git revision hash. Credit to https://stackoverflow.com/a/21901260 for the code :-)"""
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], encoding="ascii", errors="ignore"
    ).strip()[
        :7
    ]  # [7:] is here because of the commit hash, the rest of this function is from stack overflow


async def base_on_error(
    inter: disnake.ApplicationCommandInteraction, error: BaseException | Exception
):
    """The base on_error event. Call this and use the dictionary as keyword arguments to print to the user"""

    if isinstance(error, BaseException) and not isinstance(error, Exception):
        # Errors that do not inherit from Exception are not meant to be caught
        await inter.bot.close()
        if exc_info()[0] is not None:
            raise
        raise error
    if isinstance(error, LockedCacheException):
        return {
            "content": "The bot's cache's lock is currently being held. Please try again later."
        }

    if isinstance(error, (OnCooldown, disnake.ext.commands.CommandOnCooldown)):
        # This is a cooldown exception
        content = f"This command is on cooldown; please retry **{disnake.utils.format_dt(disnake.utils.utcnow() + datetime.timedelta(seconds=error.retry_after), style='R')}**."
        return {"content": content, "delete_after": error.retry_after}
    if isinstance(error, (disnake.Forbidden,)):
        extra_content = """There was a 403 error. This means either
        1) You didn't give me enough permissions to function correctly, or
        2) There's a bug! If so, please report it!

        The error traceback is below."""
        error_traceback = "\n".join(traceback.format_exception(error))
        return {"content": extra_content + error_traceback}

    if isinstance(error, commands.NotOwner):
        return {"embed": ErrorEmbed("You are not the owner of this bot.")}
    if isinstance(error, disnake.ext.commands.errors.CheckFailure):
        return {"embed": ErrorEmbed(str(error))}
    # Embed = ErrorEmbed(custom_title="⚠ Oh no! Error: " + str(type(error)), description=("Command raised an exception:" + str(error)))
    logging.error("Uh oh - an error occurred ", exc_info=exc_info())
    error_traceback = "\n".join(traceback.format_exception(error))
    print(
        "\n".join(traceback.format_exception(error)),  # python 3.10 only!
        file=stderr,
    )

    error_msg = """An error occurred!

    Steps you should do:
    1) Please report this bug to me! (Either create a github issue, or report it in the support server)
    2) If you are a programmer, please suggest a fix by creating a Pull Request.
    3) Please don't use this command until it gets fixed in a later update!

    The error traceback is shown below; this may be removed/DMed to the user in the future.

    """ + disnake.utils.escape_markdown(
        error_traceback
    )  # TODO: update when my support server becomes public & think about providing the traceback to the user
    try:
        await log_error(error)  # Log the error
    except Exception as log_error_exc:
        error_msg += (
            """Additionally, while trying to log this error, the following exception occurred: \n"""
            + disnake.utils.escape_markdown(
                "\n".join(traceback.format_exception(log_error_exc))
            )
        )

    try:
        embed = disnake.Embed(
            colour=disnake.Colour.red(),
            description=error_msg,
            title="Oh, no! An error occurred!",
        )
    except (TypeError, NameError) as e:
        # send as plain text
        plain_text = (
            """Oh no! An Exception occurred! And it couldn't be sent as an embed!```"""
        )
        plain_text += error_traceback
        plain_text += f"```Time: {str(asctime())} Commit hash: {get_git_revision_hash()} The stack trace is shown for debugging purposes. The stack trace is also logged (and pushed), but should not contain identifying information (only code which is on github)"

        plain_text += f"Error that occurred while attempting to send it as an embed:"
        plain_text += disnake.utils.escape_markdown(
            "".join(traceback.format_exception(e))
        )[: -(1650 - len(plain_text))]
        the_new_exception = deepcopy(e)
        the_new_exception.__cause__ = error
        if len(plain_text) > 2000:
            # uh oh
            raise RuntimeError(
                "An error occurred; could not send it as an embed nor as plain text!"
            ) from the_new_exception

        return {"content": plain_text}
    footer = f"Time: {str(asctime())} Commit hash: {get_git_revision_hash()} The stack trace is shown for debugging purposes. The stack trace is also logged (and pushed), but should not contain identifying information (only code which is on github)"
    embed.set_footer(text=footer)
    return {"embed": embed}
