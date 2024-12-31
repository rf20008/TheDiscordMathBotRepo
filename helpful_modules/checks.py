"""You can distribute any version of the Software created and distributed *before* 23:17:55.00 July 28, 2024 GMT-4
under the GNU General Public License version 3 or at your option, any  later option.
But versions of the code created and/or distributed *on or after* that date must be distributed
under the GNU *Affero* General Public License, version 3, or, at your option, any later version.

The Discord Math Problem Bot Repo - Checks

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License
as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License along with this program.
If not, see <https://www.gnu.org/licenses/>.

Author: Samuel Guo (64931063+rf20008@users.noreply.github.com)"""
import time

import traceback
import disnake
from disnake.ext import commands

from .custom_bot import TheDiscordMathProblemBot
from .problems_module.user_data import UserData
from .StatsTrack import CommandStats, CommandUsage, StreamWrapperStorer
from .file_log import AuditLog

bot = None
MAX_LIMIT = 120_000  # Nothing longer than 120,000 characters
MAX_NUM = 10**30


# MAX_NUM should equal 10^30
def setup(_bot):
    global bot
    bot = _bot
    return "Success!"


class CustomCheckFailure(commands.CheckFailure):
    """Raised when a custom check fails. Some checks raise exceptions inherited from this."""

    pass


class NotTrustedUser(CustomCheckFailure):
    """Raised when trying to run a command that requires trusted user permissions but the user isn't trusted"""

    pass


class DenylistedException(CustomCheckFailure):
    """Raised when trying to run a command, but something you are trying to use is denylisted"""

    pass


class BotClosingException(commands.CheckFailure):
    """Raised when the bot is closing and someone tries to use a command"""

    pass


def custom_check(
    function=lambda inter: True, args: list = [], exceptionToRaiseIfFailed=None
):
    """A check template :-)"""

    def predicate(inter):
        f = function(inter)
        if not f:
            raise exceptionToRaiseIfFailed
        return True

    return commands.check(predicate)


def trusted_users_only():
    async def predicate(inter):
        if inter.bot is None:
            raise CustomCheckFailure("Bot is None")
        if not isinstance(inter.bot, TheDiscordMathProblemBot):
            raise TypeError("Uh oh; inter.bot isn't TheDiscordMathProblemBot")
        try:
            if await inter.bot.is_trusted(inter.author):
                return True
        except Exception as e:
            print("An error occurred while trying to find whether someone was trusted:",
                  "".join(traceback.format_exception(e)))
            inter.bot.log.exception(e)

            raise
        raise NotTrustedUser(
            f"You aren't a trusted user, {inter.author.mention}. Therefore, you do not have permission to run this command!"
        )

    return commands.check(predicate)


def administrator_or_trusted_users_only():
    """Checks if the user has administrator permission or is a bot trusted user."""

    async def predicate(inter):
        if inter.author.guild_permissions.adminstrator:
            return True
        else:
            if not isinstance(inter.bot, TheDiscordMathProblemBot):
                raise TypeError("Uh oh")
            if await inter.bot.is_trusted(inter.author):
                return True

        raise CustomCheckFailure(
            "Insufficient permissions (administrator permission or bot trusted user required. If this happens again and you have the administrator permission, report this)"
        )

    return commands.check(predicate)


def always_failing_check():
    """This check will never pass"""

    def predicate(_):
        raise CustomCheckFailure("This check (test) will never pass")

    return commands.check(predicate)


def is_not_denylisted():
    """Check to make sure the user is not denylisted"""

    async def predicate(inter):
        if not isinstance(inter.bot, TheDiscordMathProblemBot):
            raise TypeError(
                "Uh oh! We can't check whether people are denylisted if the bot is just an instance of disnake.ext.commands.Bot"
            )

        user_data: UserData = await inter.bot.cache.get_user_data(
            user_id=inter.author.id,
            default=UserData(user_id=inter.author.id, trusted=False, denylisted=False),
        )
        if user_data.is_denylisted():
            until_str = ""
            if user_data.denylist_reason == float('inf'):
                until_str='never'
            else:
                if user_data.denylist_expiry < time.time():
                    until_str = f"{disnake.utils.format_dt(user_data.denylist_expiry, 'R')} ago"
                else:
                    until_str = f'in {disnake.utils.format_dt(user_data.denylist_expiry, "R")}'
            msg = f"""You are denylisted from the bot! To appeal, you must use /appeal. Note that appeals are seen very rarely..., The reason you've been denylisted is {user_data.denylist_reason}. This ban expires {until_str}"""
            raise DenylistedException(
                msg
            )
        return True

    return commands.check(predicate)

user_not_denylisted = is_not_denylisted

def guild_not_denylisted():
    """Check to make sure a command isn't being executed in a denylisted guild -- instead, we will say the guild has been denylisted & leave the guild"""

    async def predicate(inter: disnake.ApplicationCommandInteraction):
        """The actual check"""
        if not isinstance(inter.bot, TheDiscordMathProblemBot):
            raise TypeError("Uh oh! inter.bot isn't TheDiscordMathProblemBot")
        if inter.guild is None:
            return True
        if await inter.bot.is_guild_denylisted(inter.guild):
            await inter.send(
                "This guild has just been denylisted -- therefore I'm leaving."
                f"However, my source code is available at {inter.bot.constants.SOURCE_CODE_LINK}",
                ephemeral=True,
            )
            await inter.bot.notify_guild_on_guild_leave_because_guild_denylist(
                inter.guild
            )
            return False
        return True

    return commands.check(predicate)


def has_privileges(**privileges_required):
    """Make sure the user running this has the privileges required to run this command (not permissions, but bot privileges).
    Right now, the only privileges that can be checked are:
        -`trusted`,
        -`denylisted`
    As this is the internal API of my bot, this may change at any time; don't rely on it :-)
    """

    async def predicate(inter: disnake.ApplicationCommandInteraction):
        """The actual check"""
        if not isinstance(inter.bot, TheDiscordMathProblemBot):
            raise TypeError("Uh oh - inter.bot isn't TheDiscordMathProblemBot")
        if privileges_required == {}:
            if await inter.bot.cache.user_meets_permissions_required_to_use_command(
                inter.author.id
            ):  # This uses the values defined in config.json
                return True
            raise CustomCheckFailure("You don't have the permissions required!")
        if await inter.bot.cache.user_meets_permissions_required_to_use_command(
            inter.author.id, privileges_required
        ):
            return True
        raise CustomCheckFailure("You don't have the required privileges!")

    return commands.check(predicate)


def guild_owners_or_trusted_users_only():
    """A check to make sure that only trusted users or users who own the guild that the command is running in can run the command"""

    async def predicate(inter: disnake.ApplicationCommandInteraction):
        if not isinstance(inter.bot, TheDiscordMathProblemBot):
            raise RuntimeError("Uh oh - inter.bot isn't TheDiscordMathProblemBot")
        if await inter.bot.is_trusted(inter.author):
            return True  # Trusted users can run this
        if inter.guild is None:
            raise commands.CheckFailure(
                "You can't run this command because it's in a DM and you must be the guild owner to run the command!"
            )
        if inter.guild.owner_id is None:
            raise Exception("The owner id is not defined!")

        if inter.guild.owner_id == inter.author.id:
            return True
        else:
            raise commands.CheckFailure("You don't own this guild!")

    return commands.check(predicate)


def nothing_too_long():
    async def predicate(inter: disnake.ApplicationCommandInteraction):
        for item, l in inter.filled_options:
            try:
                if len(l) > MAX_LIMIT:
                    raise commands.CheckFailure(
                        f"You're not allowed to send things longer than {MAX_LIMIT} characters."
                    )
                else:
                    continue
            except commands.CheckFailure:
                raise  # Don't catch this error
            except TypeError:
                # Not something we can find the length of
                pass  # Don't do anything

        return True

    return commands.check(predicate)


def no_insanely_huge_numbers_check(max_num=MAX_NUM):
    async def predicate(inter: disnake.ApplicationCommandInteraction):
        for _, it in inter.filled_options.items():
            if not isinstance(it, (float, str, int)):
                continue
            if isinstance(it, float):
                continue
            if isinstance(it, str):
                try:
                    if int(it) >= max_num:
                        return False
                except:
                    pass
                for i in it.split():
                    try:
                        if int(i) >= max_num:
                            return False
                    except:
                        pass
        return True

    return commands.check(predicate)


def cmds_cnt():
    """Count the number of commands used and store it in storer. Storer must support storer.writeStats(CommandStats) and storer.appendStats(CommandStats"""

    async def predicate(inter):
        # increment both total_stats
        # and this_session
        # and then set these objects to
        inter.bot.total_stats.update(
            CommandUsage(inter.user.id, inter.data.name, time.time())
        )  # warning
        inter.bot.this_session.update(
            CommandUsage(inter.user.id, inter.data.name, time.time())
        )  # warning
        return True

    return commands.check(predicate)

def audit_command_usage_check():
    async def predicate(inter: disnake.ApplicationCommandInteraction):
        print("HEHE!")
        try:
            if not isinstance(inter.bot, TheDiscordMathProblemBot):
                raise TypeError
            if not hasattr(inter.bot, 'audit_log'):
                raise AttributeError
            if not isinstance(inter.bot.audit_log, AuditLog):
                raise TypeError
            inter.bot.audit_log.add_to_log(
                log_entry = f"Command {inter.application_command.qualified_name} has been run in a guild with ID {inter.guild_id} by a user with ID {inter.author.id}",
                priority=0,
                extra_info={}
            )
            return True
        except:
            exit()
    return commands.check(predicate)
async def always_succeeding_check_unwrapped(inter, *args, **kwargs):
    if callable(inter):
        raise ValueError(
            "You cannot use this to wrap a function, because it is not a check"
        )
    return True


def not_is_closing():
    async def predicate(inter):
        if not isinstance(inter.bot, TheDiscordMathProblemBot):
            raise TypeError("inter.bot is not a TheDiscordMathProblemBot")
        if inter.bot.is_closing:
            raise BotClosingException(
                "This bot is currently closing. Try again when the bot is not closing."
            )
        return True

    return commands.check(predicate)
