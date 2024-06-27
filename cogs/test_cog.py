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
"""A cog made to test TheDiscordMathProblemBot's connection to Discord. This doesn't provide the bot extra functionality.
This cog, like everything else in this repository, is licensed under GPLv3 (or later)"""
import typing

import disnake

from .helper_cog import HelperCog


class TestCog(HelperCog):
    """A cog made to test the bot's connection to Discord. This cog does not provide extra functionality"""

    def __init__(self, bot: disnake.ext.commands.Bot):
        super().__init__(bot)

    @disnake.ext.commands.slash_command(
        name="_test",
        description="A command that when executed, returns the string 'test' & takes no arguments",
    )
    async def _test(
        self, inter: disnake.ApplicationCommandInteraction
    ) -> typing.Optional[disnake.InteractionMessage]:
        """/_test
        This makes the bot say Test. This doesn't take any arguments. The purpose of this command is to test the bot!
        """
        return await inter.send("Test")

    @disnake.ext.commands.command(name="_test")
    async def test(self, ctx):
        """Returns test & takes no arguments. Useful only for debugging purposes"""
        return await ctx.send("test")
