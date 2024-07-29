"""You can distribute any version of the Software created and distributed *before* 23:17:55.00 July 28, 2024 GMT-4
under the GNU General Public License version 3 or at your option, any  later option.
But versions of the code created and/or distributed *on or after* that date must be distributed
under the GNU *Affero* General Public License, version 3, or, at your option, any later version.

The Discord Math Problem Bot Repo - Cooldowns

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License
as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License along with this program.
If not, see <https://www.gnu.org/licenses/>.

Author: Samuel Guo (64931063+rf20008@users.noreply.github.com)"""
# NOT NEEDED - I forgot about decorators
import typing as t


class OnCooldown(Exception):
    # This is no longer needed
    pass


async def check_for_cooldown(
    ctx, command_name: str, cooldown_time: float = 0.1, is_global_cooldown: bool = False
) -> t.NoReturn:
    raise NotImplementedError("THIS FUNCTION NOT SUPPOSED TO BE USED")


# import time
#
# cooldowns = {}


# class OnCooldown(Exception):
#    "This command is on cooldown"
#    pass


# async def check_for_cooldown(
#    ctx, command_name, cooldown_time=0.1, is_global_cooldown=False, global_cooldown=0
# ):
#    "A function that checks for cooldowns. Raises nextcord.ext.commands.errors.CommandOnCooldown if you are on cooldown Otherwise, returns False and sets the user on cooldown. cooldown_time is in seconds."
#    global cooldowns
#    if command_name not in cooldowns.keys():
#        cooldowns[command_name] = {}
#    if is_global_cooldown and "_global" not in cooldowns.keys():
#        cooldowns["_global"] = {}
#    if is_global_cooldown:
#        command_name = "_global"
#    try:
#        if cooldowns["_global"][ctx.author.id] - time.time() > 0:
#            raise OnCooldown(
#                f"You are on cooldown (this applies to all commands. Try again in {round(cooldowns['_global'][ctx.author.id] - time.time(),ndigits = 3)} seconds.)"
#            )
#    except:
#        if is_global_cooldown:
#            cooldowns["_global"][ctx.author.id] = time.time() + global_cooldown
#       raise
#    try:
#        t = cooldowns[command_name][ctx.author.id] - time.time()
#        if t > 0:
#            raise OnCooldown(f"You are on cooldown! Try again in {t} seconds.")
#        else:
#            cooldowns[command_name][ctx.author.id] = time.time() + cooldown_time
#            return False
#    except KeyError:
#        cooldowns[command_name][ctx.author.id] = time.time() + cooldown_time
#        return False
