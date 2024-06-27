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


import disnake
from disnake.ext import commands, tasks

from helpful_modules._error_logging import log_error
from helpful_modules.custom_bot import TheDiscordMathProblemBot
from helpful_modules.problems_module.errors import BGSaveNotSupportedOnSQLException
from .helper_cog import HelperCog

# TODO: make this an extension :-)
SUPPORT_SERVER_ID = 873741593159540747


class TaskCog(HelperCog):
    def __init__(self, bot: TheDiscordMathProblemBot):
        self.bot = bot
        super().__init__(bot)
        self.cache = bot.cache

    # Listener to handle slash commands
    @commands.Cog.listener()
    async def on_slash_command(self, inter: disnake.ApplicationCommandInteraction):
        """Leave guilds because the guild is blacklisted"""
        if not inter.guild:
            return
        # Check if the bot instance is of the correct type
        if not isinstance(inter.bot, TheDiscordMathProblemBot):
            raise TypeError("The bot instance must be an instance of TheDiscordMathProblemBot")
        # Check if the guild is blacklisted and notify before leaving
        if await inter.bot.is_guild_blacklisted(inter.guild):
            await inter.send("Your guild is blacklisted - so I am leaving this guild")
            await inter.bot.notify_guild_on_guild_leave_because_guild_blacklist()

    # Task to report any failed tasks
    @tasks.loop(seconds=15)
    async def report_tasks_task(self):
        """Report any failed tasks"""
        for task in self.bot._tasks:
            if task.failed():
                # Log the exception
                _int_task = task.get_task()
                if _int_task.done():
                    try:
                        await log_error(_int_task.exception())
                    except asyncio.InvalidStateError as ISE:
                        await log_error(ISE)

    # Task to leave blacklisted guilds
    @tasks.loop(minutes=15)
    async def leaving_blacklisted_guilds_task(self):
        """Leave guilds that are blacklisted"""
        for guild in self.bot.guilds:
            if await self.bot.is_guild_blacklisted(guild):
                await self.bot.notify_guild_on_guild_leave_because_guild_blacklist(guild)

    # Task to update cache
    @tasks.loop(seconds=15)
    async def update_cache_task(self):
        """Update cache"""
        await self.cache.update_cache()

    def cog_unload(self):
        """Stop all tasks when cog is unloaded"""
        super().cog_unload()
        self.leaving_blacklisted_guilds_task.stop()
        self.update_cache_task.stop()
        self.report_tasks_task.stop()

    # Task to update support server information
    @tasks.loop(minutes=4)
    async def update_support_server(self):
        """Update support server information"""
        self.bot.support_server = await self.bot.fetch_guild(self.bot.constants.SUPPORT_SERVER_ID)

    # Task to ensure config JSON is correct
    @tasks.loop(seconds=5)
    async def make_sure_config_json_is_correct(self):
        """Ensure config JSON is correct"""
        await self.bot.config_json.update_my_file()

    # Task to ensure stats are saved
    @tasks.loop(seconds=45)
    async def make_sure_stats_are_saved(self):
        """Ensure stats are saved"""
        await self.bot.save_stats()

    # Task to perform background save every so often
    @tasks.loop(seconds=60)
    async def bgsave_every_so_often(self):
        """Perform a background save every so often"""
        try:
            await self.bot.cache.bgsave()
        except BGSaveNotSupportedOnSQLException:
            pass

def setup(bot: TheDiscordMathProblemBot):
    bot.add_cog(TaskCog(bot))
