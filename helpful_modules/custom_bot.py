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
import asyncio
import inspect
import logging
import random
import time
import typing
from functools import partial, wraps
from types import FunctionType
import math
import warnings

import disnake
from disnake.ext import commands, tasks

import helpful_modules
from helpful_modules import problems_module
from helpful_modules.problems_module import GuildData
from helpful_modules.constants_loader import BotConstants
from helpful_modules.problems_module.cache import MathProblemCache
from helpful_modules.restart_the_bot import RestartTheBot

from ._error_logging import log_error
from .FileDictionaryReader import AsyncFileDict
from .StatsTrack import CommandStats, CommandUsage, StreamWrapperStorer
from .threads_or_useful_funcs import modified_async_wrap
from .message_queue import MessageQueue
from .errors import AppealViewMessageNotFoundException, NotInSupportServerWarning, AppealViewChannelCantSeeException
WAIT = True
TIME_TO_WAIT = 25
ANNOUNCEMENTS_CHANNEL = 960725589260652588
TIMEOUT = 0.5
SUPPORT_SERVER_GUILD_ID = 873741593159540747
APPEALS_CHANNEL_ID = 944693665899630592

class TheDiscordMathProblemBot(disnake.ext.commands.Bot):
    def __init__(self, *args, **kwargs):
        self.is_closing = False

        self.tasks = kwargs.pop("tasks")
        self.config_json = AsyncFileDict("config.json")
        self.storer = kwargs.pop("storer")
        self.trusted_users = kwargs.pop("trusted_users")
        self._on_ready_func = kwargs.pop(
            "on_ready_func"
        )  # Will be called when the bot is ready (with an argument of itself
        cache = kwargs.pop("cache")
        self.cache = (
            cache
            if isinstance(cache, helpful_modules.problems_module.MathProblemCache) or isinstance(helpful_modules.problems_module.RedisCache)
            else False
        )
        if self.cache is False:
            raise TypeError("Not of type MathProblemCache")
        # print(self.cache)
        self.constants = (
            kwargs.pop("constants")
            if isinstance(kwargs.get("constants"), BotConstants)
            else False
        )
        if self.constants is False:
            raise TypeError("Constants is not a BotConstants object")
        super().__init__(*args, **kwargs)

        assert isinstance(self.tasks, dict)
        self.restart = RestartTheBot(self) # TODO: fix the restartTheBot class
        for task in self.tasks.values():
            assert isinstance(task, disnake.ext.tasks.Loop)
            task.start()  # TODO: add being able to change it
        self.timeStarted = float("inf")
        self.total_stats = None
        self.this_session = None
        self.queue = MessageQueue()
        self.initialize_stats()
        # self.trusted_users = kwargs.get("trusted_users", None)
        # if not self.trusted_users and self.trusted_users != []:
        #    raise TypeError("trusted_users was not found")
        # self.denylisted_users = kwargs.get("denylisted_users", [])
        self.closing_things = []

    @property
    def support_server(self):
        return self.get_guild(SUPPORT_SERVER_GUILD_ID)

    def get_task(self, task_name):
        return self.tasks[task_name]

    def start_tasks(self):
        for task in self.tasks.values():
            task.start()

    @property
    def log(self):
        return logging.getLogger(__name__)

    @property
    def uptime(self):
        return time.time() - self.timeStarted  # TODO: more accurate time + timestamp

    async def on_ready(self):
        self.timeStarted = time.time()
        await self._on_ready_func(self)

    def owns_and_is_trusted(self, user: disnake.User):
        if not hasattr(self, "owner_id") or not self.owner_id or self.owner_id is None:
            return False
        return user.id in self.trusted_users and user.id == self.owner_id

    def add_task(self, task):
        assert isinstance(task, disnake.ext.tasks.Loop)
        self.tasks.append(task)
        task.start()

    async def close(self):

        try:

            self.is_closing = True

            await self.queue.stop(msg="Bot is closing", empty=True, act=True, timeout=TIMEOUT, limit = int(math.floor(TIME_TO_WAIT/TIMEOUT)), delete_undone_tasks=True)
            await self.maybe_send_closing_message()
            if WAIT:
                await asyncio.sleep(TIME_TO_WAIT)
            await self.queue.empty(act=False)
            for cog_name in list(self.cogs):
                self.remove_cog(cog_name)
            for extension in list(self.extensions):
                self.unload_extension(extension)
            for task in self.tasks:
                task.stop()
            await asyncio.sleep(5)
            self.storer.close()
            await asyncio.gather(*self.closing_things)
        except Exception as e:
            print(f"An exception of {e} happened while the bot was trying to close.")
            self.log.exception(e)
            await log_error(e)
            await asyncio.sleep(3)
        finally:
            await super().close()
            self.is_closing=False


    async def maybe_send_closing_message(self):
        guild = self.support_server
        channel = guild.get_channel(ANNOUNCEMENTS_CHANNEL)
        await channel.send(
            f"This process will stop functioning in {TIME_TO_WAIT} seconds (if waiting is enabled)"
        )

    def add_closing_thing(self, thing: FunctionType) -> None:
        if asyncio.iscoroutinefunction(thing):
            self.closing_things.append(thing())

        elif inspect.isawaitable(thing):
            self.closing_things.append(thing)

        else:
            raise TypeError()

    async def is_trusted(
        self, user: typing.Union[disnake.User, disnake.Member]
    ) -> bool:
        return await self.is_trusted_by_user_id(user.id)

    async def is_trusted_by_user_id(self, user_id: int) -> bool:

        data = await self.cache.get_user_data(
            user_id=user_id,
            default=problems_module.UserData(
                user_id=user_id, trusted=False, denylisted=False
            ),
        )
        return data.trusted

    async def is_denylisted_by_user_id(self, user_id: int) -> bool:
        data = await self.cache.get_user_data(
            user_id=user_id,
            default=problems_module.UserData(
                user_id=user_id, trusted=False, denylisted=False
            ),
        )
        return data.denylisted

    async def mods_can_view(self, channel: disnake.abc.Messageable):
        guild_data: problems_module.GuildData = await self.cache.get_guild_data(
            guild_id=channel.guild.id
        )
        for role_id in guild_data.mod_check.roles_allowed:
            role: disnake.Role = channel.guild.get_role(role_id)
            if channel.permissions_for(role).view_channel:
                return True
        return False
    async def is_user_denylisted(
        self, user: typing.Union[disnake.User, disnake.Member]
    ) -> bool:
        return await self.is_denylisted_by_guild_id(user.id)

    async def is_guild_denylisted(self, guild: disnake.Guild) -> bool:
        return await self.is_denylisted_by_guild_id(guild.id)

    async def is_denylisted_by_guild_id(self, guild_id: int) -> bool:
        data: GuildData = await self.cache.get_guild_data(
            guild_id=guild_id,
            default=GuildData.default(guild_id=guild_id),
        )
        return data.denylisted

    async def notify_guild_on_guild_leave_because_guild_denylist(self, guild: disnake.Guild) -> None:
        """
        Notify the guild about the bot leaving due to being denylisted. If suitable channels are available,
        send a notification message and then leave the guild. If no suitable channels are available, directly
        leave the guild without sending a notification.

        Args:
            guild (disnake.Guild): The guild from which the bot is leaving due to being denylisted.

        Raises:
            RuntimeError: If the guild is not actually denylisted.
        """

        if not await self.is_guild_denylisted(guild):
            raise RuntimeError("The guild isn't denylisted!")

        me: disnake.Member = guild.me

        # Function to check if a channel can be used for sending messages
        def can_send_messages(channel):
            return isinstance(channel, disnake.abc.Messageable) and channel.permissions_for(me).send_messages

        # Get all channels where the bot can send messages
        channels_that_we_could_send_to = list(filter(can_send_messages, guild.channels))

        if not channels_that_we_could_send_to:
            await guild.leave()
            return

        everyone_role = guild.get_role(guild.id)

        # Function to check if everyone can view the channel
        def everyone_can_view(channel):
            return channel.permissions_for(everyone_role).view_channel

        # Get channels visible to everyone
        channels_that_everyone_can_see = list(filter(everyone_can_view, channels_that_we_could_send_to))

        if channels_that_everyone_can_see:
            channel_to_send_to = random.choice(channels_that_everyone_can_see)
        else:
            # Function to check if mods can view the channel


            # Get channels visible to moderators
            channels_that_mods_can_see = [channel for channel in channels_that_we_could_send_to if await self.mods_can_view(channel)]

            if channels_that_mods_can_see:
                channel_to_send_to = random.choice(channels_that_mods_can_see)
            else:
                # If no suitable channels found, choose randomly from all channels
                channel_to_send_to = random.choice(channels_that_we_could_send_to)

        await channel_to_send_to.send(
            f"""I have left the guild because the guild is denylisted, under my terms and conditions.
            However, I'm available under the GPL. My source code is at {self.constants.SOURCE_CODE_LINK}, so you could self-host the bot if you wish.
            """
        )
        await guild.leave()

    # async def on_application_command(self, inter: disnake.ApplicationCommandInteraction):
    #    await super().on_application_command(inter)
    #    if await self.is_guild_denylisted(inter.guild):
    #        await inter.send("This command has been executed in a b")
    #       await self.notify_guild_on_guild_leave_because_guild_denylist(inter.guild)

    def task(
        self,
    ) -> typing.Callable[
        [typing.Callable[[typing.Any], typing.Any], typing.Any],
        typing.Callable[[typing.Any], typing.Any],
    ]:
        """Add a task to my internal list of tasks + return it  (this is a decorator :-))"""

        def decorator(_self, func: FunctionType, *args, **kwargs):
            task: tasks.Loop(func=func, *args, **kwargs)
            _self.tasks.append(task)
            return func

        return decorator

    def closing_task(self):
        """Add a closing task to my internal list of closing tasks"""

        def decorator(_self, func: FunctionType):
            if isinstance(func, FunctionType):
                _self.closing_things.append(modified_async_wrap(func))
                return func
            elif inspect.isawaitable(func):
                _self.closing_things.append(func)
                return func
            raise TypeError("func is not awaitable!!")

        return decorator

    async def save_stats(self):
        await self.storer.writeStats(self.total_stats)

    def initialize_stats(self):
        self.total_stats = self.storer.return_stats()
        self.this_session = CommandStats(usages=[], unique_users=set(), total_cmds=0)

    async def _is_owner(self, user: disnake.User) -> bool:
        """Helper function to determine whether user qualifies as an owner"""
        if await self.is_owner(user):
            return True
        if self.owner_ids is None or self.owner_id in [None, [], set()]:
            return False
        if self.bot.owner_id == user.id:
            return True
        try:
            if (
                self.bot.owner_ids not in [None, [], set()]
                and user.id in self.owner_ids
            ):
                return True
            return False  # nope
        except AttributeError:
            # not an owner
            return False
    async def register_appeal_views(self):

        appeals_channel = self.support_server.get_channel(APPEALS_CHANNEL_ID)
        errors = []
        try:
            for appeal_view in await self.cache.get_all_appeal_view_infos():
                try:
                    msg: disnake.Message = await appeals_channel.fetch_message(appeal_view.message_id)
                except disnake.NotFound as nf:
                    err = AppealViewMessageNotFoundException(
                        f"Appeal message for the appeal {appeal_view} is not found; maybe it's not in the appeals channel"
                    )
                    err.__cause__ == nf
                    errors.append(err)
                except disnake.Forbidden as forb:
                    err = AppealViewChannelCantSeeException(f"I can't see #appeals; I can't see the appeal with message {appeal_view.message_id}")
                    err.__cause__ = forb
                    errors.append(forb)
                except BaseException as be:
                    errors.append(be)

                if msg is None:
                    errors.append(AppealViewMessageNotFoundException(f"Appeal message for the appeal {appeal_view} is not found; maybe it's not in the appeals channel"))
                self.add_view(disnake.ui.View.from_message(msg), msg.id)
        if errors:
            raise BaseExceptionGroup("Appeal fetching failed!!!!", errors)

