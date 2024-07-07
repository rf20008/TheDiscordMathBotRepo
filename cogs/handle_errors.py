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

import sys
import traceback
from time import asctime

from disnake.ext.commands import CommandOnCooldown, NotOwner

from helpful_modules._error_logging import log_error
from helpful_modules.base_on_error import get_git_revision_hash
from helpful_modules.cooldowns import OnCooldown
from helpful_modules.custom_embeds import ErrorEmbed

from .helper_cog import *


class ErrorHandlerCog(HelperCog):
    def __init__(self, bot):
        super().__init__(bot)
        self.bot = bot

    @staticmethod
    async def handle_errors(
        ctx, error, print_stack_traceback: tuple = (True, sys.stderr)
    ):
        """Function called when a slash command errors"""

        if print_stack_traceback[0]:
            # print the traceback to the file
            print(
                "\n".join(
                    traceback.format_exception(
                        etype=type(error), value=error, tb=error.__traceback__
                    )
                ),
                file=print_stack_traceback[1],
            )

        if isinstance(error, OnCooldown):
            await ctx.reply(str(error))
            return
        error_traceback_as_obj = traceback.format_exception(
            etype=type(error), value=error, tb=error.__traceback__
        )
        await log_error(error)  # Log the error
        if isinstance(error, NotOwner):
            await ctx.reply(embed=ErrorEmbed("You are not the owner of this bot."))
            return

        error_traceback = "\n".join(error_traceback_as_obj)

        await ctx.reply(
            embed=ErrorEmbed(
                disnake.utils.escape_markdown(error_traceback),
                custom_title="Oh, no! An exception occurred",
                footer=f"Time: {str(asctime())} Commit hash: {get_git_revision_hash()} ",
            )
        )
