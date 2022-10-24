import asyncio
import inspect
import logging
import random
import time
import typing
from functools import partial, wraps
from types import FunctionType

import disnake
from disnake.ext import commands, tasks

import helpful_modules
from helpful_modules import problems_module
from helpful_modules.constants_loader import BotConstants
from helpful_modules.problems_module.cache import MathProblemCache
from helpful_modules.restart_the_bot import RestartTheBot

from .FileDictionaryReader import AsyncFileDict
from .threads_or_useful_funcs import modified_async_wrap


class TheDiscordMathProblemBot(disnake.ext.commands.Bot):
    def __init__(self, *args, **kwargs):
        self.is_closing = False

        self.tasks = kwargs.pop("tasks")
        self.config_json = AsyncFileDict("config.json")
        self.trusted_users = kwargs.pop("trusted_users")
        self._on_ready_func = kwargs.pop(
            "on_ready_func"
        )  # Will be called when the bot is ready (with an argument of itself
        cache = kwargs.pop("cache")
        self.cache = (
            cache
            if isinstance(
                cache,
                helpful_modules.problems_module.MathProblemCache
            )
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
        self.restart = RestartTheBot(self)
        for task in self.tasks.values():
            assert isinstance(task, disnake.ext.tasks.Loop)
            task.start()  # TODO: add being able to change it
        self.timeStarted = float("inf")

        # self.trusted_users = kwargs.get("trusted_users", None)
        # if not self.trusted_users and self.trusted_users != []:
        #    raise TypeError("trusted_users was not found")
        # self.blacklisted_users = kwargs.get("blacklisted_users", [])
        self.closing_things = []
        self.support_server = None

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
        assert isinstance(task, disnake.tasks.Loop)
        self.tasks.append(task)
        task.start()

    async def close(self):
        self.is_closing = True
        for cog_name in list(self.cogs):
            self.remove_cog(cog_name)
        for extension in list(self.extensions):
            self.unload_extension(extension)
        for task in self.tasks:
            task.stop()
        await asyncio.sleep(5)
        await asyncio.gather(*self.closing_things)
        self.is_closing = False
        await super().close()

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
        return await self.is_trusted_by_id(user.id)

    async def is_trusted_by_id(self, user_id: int) -> bool:
        data = await self.cache.get_user_data(
            user_id=user_id,
            default=problems_module.UserData(
                user_id=user_id, trusted=False, blacklisted=False
            ),
        )
        return data.trusted

    async def is_blacklisted_by_user_id(self, user_id: int) -> bool:
        data = await self.cache.get_user_data(
            user_id=user_id,
            default=problems_module.UserData(
                user_id=user_id, trusted=False, blacklisted=False
            ),
        )
        return data.blacklisted

    async def is_user_blacklisted(
            self, user: typing.Union[disnake.User, disnake.Member]
    ) -> bool:
        return await self.is_blacklisted_by_user_id(user.id)

    async def is_guild_blacklisted(self, guild: disnake.Guild) -> bool:
        return await self.is_blacklisted_by_guild_id(guild.id)

    async def is_blacklisted_by_guild_id(self, guild_id: int) -> bool:
        data: GuildData = await self.cache.get_guild_data(
            guild_id=guild_id, default=problems_module.GuildData.default(guild_id=guild_id)
        )
        return data.blacklisted

    async def notify_guild_on_guild_leave_because_guild_blacklist(
            self, guild: disnake.Guild
    ) -> None:
        """Notify the guild about the bot leaving the guild because the guild is blacklisted.
        Throws RuntimeError if the guild is not actually blacklisted.
        Throws HTTPException if sending the message failed, or leaving the guild failed."""
        if not await self.is_guild_blacklisted(guild):
            raise RuntimeError("The guild isn't blacklisted!")
        _me: disnake.Member = guild.me
        channels_that_we_could_send_to = [
            channel
            for channel in guild.channels
            if channel.permissions_for(me).send_messages
        ]
        if len(channels_that_we_could_send_to) == 0:
            # Bypass trying to send the message - We don't have any channels we could send this message to anyway

            await guild.leave()
            return

        # Let's try to send the message to a channel that everyone can see
        everyone_role = guild.get_role(guild.id)
        channels_that_we_can_send_to_and_everyone_can_see = [
            channel
            for channel in channels_that_we_could_send_to
            if channel.permissions_for(everyone_role).view_channel
        ]
        if len(channels_that_we_can_send_to_and_everyone_can_see) != 0:
            channel_to_send_to = random.choice(
                channels_that_we_can_send_to_and_everyone_can_see
            )
            await channel_to_send_to.send(
                f"""I have left the guild because the guild is blacklisted, under my terms and conditions.
            However, I'm available under the GPL. My source code is at {self.constants.SOURCE_CODE_LINK}, so you could self-host the bot if you wish.
            """
            )
            await guild.leave()
            return

        else:
            # There is no channel that we can send to and everyone can see
            # So we try to send it to a channel that mods can see
            guild_data: problems_module.GuildData = await self.cache.get_guild_data(
                guild_id=guild.id, default=problems_module.GuildData.default()
            )
            channels_that_mods_can_see = channels_that_we_could_send_to
            for role_id in guild_data.mod_check.roles_allowed:
                role: disnake.Role = guild.get_role(role_id)
                channels_that_mods_can_see = [
                    channel
                    for channel in channels_that_mods_can_see
                    if channel.permissions_for(role).view_channel
                ]
            if (
                    len(channels_that_mods_can_see) == 0
                    and len(channels_that_we_could_send_to) != 0
            ):
                # No channels that mods can see, but we could send to some channels
                channel_to_send_to = random.choice(channels_that_we_could_send_to)
                await channel_to_send_to.send(
                    f"""I have left this guild because the guild is blacklisted, under my terms and conditions.
                            However, I'm available under the GPL. My source code is at {self.constants.SOURCE_CODE_LINK}, so you could self-host the bot if you wish.
                            """
                )
                await guild.leave()
                return

            channel_to_send_to = random.choice(channels_that_mods_can_see)
            await channel_to_send_to.send(
                f"""I have left this guild because the guild is blacklisted, under my terms and conditions.
                        However, I'm available under the GPL. My source code is at {self.constants.SOURCE_CODE_LINK}, so you could self-host the bot if you wish.
                        """
            )
            await guild.leave()
            return
        # Fallback

        await guild.leave()  # noqa
        return

    # async def on_application_command(self, inter: disnake.ApplicationCommandInteraction):
    #    await super().on_application_command(inter)
    #    if await self.is_guild_blacklisted(inter.guild):
    #        await inter.send("This command has been executed in a b")
    #       await self.notify_guild_on_guild_leave_because_guild_blacklist(inter.guild)

    def task(
            self,
    ) -> typing.Callable[
        [typing.Callable[[typing.Any], typing.Any], typing.Any],
        typing.Callable[[typing.Any], typing.Any],
    ]:
        """Add a task to my internal list of tasks + return it  (this is a decorator :-))"""

        def decorator(_self, func: types.FunctionType, *args, **kwargs):
            task: tasks.Loop(func=func, *args, **kwargs)
            _self.tasks.append(task)
            return func

        return decorator

    def closing_task(self):
        """Add a closing task to my internal list of closing tasks"""

        def decorator(_self, func: types.FunctionType):
            if isinstance(func, types.FunctionType):
                _self.closing_things.append(modified_async_wrap(func))
                return func
            elif inspect.isawaitable(func):
                _self.closing_things.append(func)
                return func
            raise TypeError("func is not awaitable!!")

        return decorator