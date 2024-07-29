"""
You can distribute any version of the Software created and distributed *before* 23:17:55.00 July 28, 2024 GMT-4
under the GNU General Public License version 3 or at your option, any  later option.
But versions of the code created and/or distributed *on or after* that date must be distributed
under the GNU *Affero* General Public License, version 3, or, at your option, any later version.

This file is part of The Discord Math Problem Bot Repo

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
import asyncio
import os
import subprocess
import sys
import warnings
from sys import executable
from typing import NoReturn, Optional

import disnake
import psutil

# from .custom_bot import TheDiscordMathProblemBot


## This code is licensed under GPLv3, like all the other Python code in this repo
## TODO: fix this
RESTART_MESSAGE_WARNING = (
    "The bot will automatically restart to apply an update after 20 seconds. "
    "It should be back in a few seconds!"
)
RESTART_MESSAGE_FINAL_WARNING = (
    "The bot is automatically restarting! It should be back in a few seconds!"
)


class RestartTheBot:
    def __init__(self, bot: Optional["TheDiscordMathProblemBot"]):
        self.bot = bot

    async def notify_before_restarting(self) -> None:
        if self.bot is None:
            warnings.warn(category=RuntimeWarning, message="no bot supplied")
            return
        warnings.warn(
            category=RuntimeWarning, message="This may not do what it actually does"
        )
        channel = await self.bot.fetch_channel(self.bot.constants.BOT_RESTART_CHANNEL)
        await channel.send(RESTART_MESSAGE_WARNING)
        await asyncio.sleep(20)
        await channel.send(RESTART_MESSAGE_FINAL_WARNING)

    async def restart_the_bot(self) -> NoReturn:
        print("The bot is now restarting!")
        await self.notify_before_restarting()
        await self.actual_restart()

    async def actual_restart(self) -> NoReturn:
        if self.bot is not None:
            await asyncio.sleep(3)
            await self.bot.close()
            await asyncio.sleep(5)
        ## I learned that starting a new process that starts a new copy of the bot is better than starting the bot directly
        # the hard way

        command = executable + " actual_restarter.py"  #
        print(f"We are going to run {command.split()}")

        try:
            restarter = subprocess.Popen(
                "helpful_modules/actual_restarter.py",
                executable=executable,
                shell=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
            )
            print(restarter.pid)
            restarter.wait(timeout=10)
        except subprocess.TimeoutExpired as te:
            print(te)
            pass
        finally:
            os._exit(0)


if __name__ == "__main__":

    async def main():
        restarter = RestartTheBot(bot=None)
        await restarter.restart_the_bot()

    asyncio.run(main())
