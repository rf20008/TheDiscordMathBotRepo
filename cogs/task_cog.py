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

import disnake
from disnake.ext import commands, tasks

from helpful_modules._error_logging import log_error
from helpful_modules.custom_bot import TheDiscordMathProblemBot
from helpful_modules.problems_module.cache_rewrite_with_redis.rediscache import (
    RedisCache,
)
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
        """Leave guilds because the guild is denylisted"""
        if not inter.guild:
            return
        # Check if the bot instance is of the correct type
        if not isinstance(inter.bot, TheDiscordMathProblemBot):
            raise TypeError(
                "The bot instance must be an instance of TheDiscordMathProblemBot"
            )
        # Check if the guild is denylisted and notify before leaving
        if await inter.bot.is_guild_denylisted(inter.guild):
            await inter.send("Your guild is denylisted - so I am leaving this guild")
            await inter.bot.notify_guild_on_guild_leave_because_guild_denylist()

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

    # Task to leave denylisted guilds
    @tasks.loop(minutes=15)
    async def leaving_denylisted_guilds_task(self):
        """Leave guilds that are denylisted"""
        for guild in self.bot.guilds:
            if await self.bot.is_guild_denylisted(guild):
                await self.bot.notify_guild_on_guild_leave_because_guild_denylist(guild)

    # Task to update cache
    @tasks.loop(seconds=15)
    async def update_cache_task(self):
        """Update cache"""
        await self.cache.update_cache()

    def cog_unload(self):
        """Stop all tasks when cog is unloaded"""
        super().cog_unload()
        self.leaving_denylisted_guilds_task.stop()
        self.update_cache_task.stop()
        self.report_tasks_task.stop()
        self.update_support_server.stop()
        self.make_sure_config_json_is_correct.stop()
        self.make_sure_stats_are_saved.stop()
        self.bgsave_every_so_often.stop()

    # Task to update support server information
    @tasks.loop(minutes=4)
    async def update_support_server(self):
        """Update support server information"""
        self.bot.support_server = await self.bot.fetch_guild(
            self.bot.constants.SUPPORT_SERVER_ID
        )

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

    @tasks.loop(seconds=60)
    async def manage_redis_memory(self):
        if not isinstance(self.bot.cache, RedisCache):
            return
        memory_info = await self.bot.cache.redis.info("memory")


def setup(bot: TheDiscordMathProblemBot):
    bot.add_cog(TaskCog(bot))
