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
import typing
from warnings import warn

import disnake
from disnake import ext

from helpful_modules import problems_module
from helpful_modules.custom_bot import TheDiscordMathProblemBot


class HelperCog(ext.commands.Cog):
    """A helper cog :-) However, by itself, it does not implement any commands."""

    def __init__(self, bot: TheDiscordMathProblemBot):
        """Helpful __init__, the entire reason I decided to make this, so I could transfer modules"""
        # self.b = bot._transport_modules
        # checks.setup(bot)
        # (
        #    self.problems_module,
        #    self.SuccessEmbed,
        #    self.ErrorEmbed,
        #    self.the_documentation_file_loader,
        # ) = (
        #    self.b["problems_module"],
        #    self.b["custom_embeds"].SuccessEmbed,
        #    self.b["custom_embeds"].ErrorEmbed,
        #    self.b["the_documentation_file_loader"],
        # )
        self.cache: problems_module.MathProblemCache = bot.cache
        self.bot: disnake.ext.commands.Bot = bot

    @property
    def trusted_users(self):
        """Syntactic sugar? A shorthand for self.bot.trusted_users"""
        return self.bot.trusted_users

    @property
    def vote_threshold(self):
        """A shorthand for self.bot.vote_threshold"""
        return self.bot.vote_threshold

    def _change_vote_threshold(
        self,
        new_vote_threshold,
        ctx=None,
        *,
        bypass_ctx_check=False,
        bypass_argument_checks=False,
    ):
        """A helper method that will change the vote_threshold to the one specified"""
        if not bypass_ctx_check:
            assert isinstance(
                ctx,
                (disnake.ext.commands.Context, disnake.ApplicationCommandInteraction),
            )
            if not self.cache.get_user_data(
                ctx.author.id,
            ).trusted:
                raise RuntimeError(
                    f"Sadly, you're not allowed to do this, {ctx.author.mention} ☹️"
                )
        if not bypass_argument_checks:
            if not isinstance(new_vote_threshold, int):
                raise TypeError(
                    f"new_vote_threshold is of type {type(new_vote_threshold)}, not int"
                )
            if new_vote_threshold <= 0:
                raise ValueError("new_vote_threshold must be bigger than 0")
        self.bot.vote_threshold = new_vote_threshold

    def _change_trusted_users(
        self,
        new_trusted_users: typing.List[int],
        ctx=None,
        *,
        bypass_ctx_check=False,
        bypass_argument_checks=False,
    ):
        """A helper method that will change the trusted_users.
        This will replace the trusted users with the one given!"""
        if not bypass_ctx_check:
            assert isinstance(
                ctx,
                (disnake.ext.commands.Context, disnake.ApplicationCommandInteraction),
            )
            if not self.bot.is_trusted(ctx.author):
                raise RuntimeError(
                    f"Sadly, you're not allowed to do this, {ctx.author.mention} ☹️"
                )
        if not bypass_argument_checks:
            if not isinstance(new_trusted_users, (list, tuple)):
                raise TypeError(
                    f"new_trusted_users is of type {type(new_trusted_users)}, not list"
                )
            if len(new_trusted_users) == 0:
                warn("You are removing all trusted users", Warning)
        self.bot.trusted_users = new_trusted_users
