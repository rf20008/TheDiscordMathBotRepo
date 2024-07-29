"""You can distribute any version of the Software created and distributed *before* 23:17:55.00 July 28, 2024 GMT-4
under the GNU General Public License version 3 or at your option, any  later option.
But versions of the code created and/or distributed *on or after* that date must be distributed
under the GNU *Affero* General Public License, version 3, or, at your option, any later version.

The Discord Math Problem Bot Repo - Custom Embeds

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License
as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License along with this program.
If not, see <https://www.gnu.org/licenses/>.

Author: Samuel Guo (64931063+rf20008@users.noreply.github.com)"""
from random import randint

from disnake import Color, Embed


def generate_random_color():
    return Color.from_rgb(r=randint(0, 255), g=randint(0, 255), b=randint(0, 255))


class SimpleEmbed(Embed):
    def __init__(
        self,
        title="",
        description="",
        color: Color | None = None,
        footer=None,
    ):
        if color is None:
            color = generate_random_color()
        super().__init__(title=title, description=description, color=color)
        self.set_footer(text=footer)


class ErrorEmbed(SimpleEmbed):
    def __init__(
        self,
        description="",
        color=Color.red(),
        custom_title=None,
        title=None,
        footer=None,
    ):
        if title is None and custom_title is None:
            custom_title = "Error!"
        if title != custom_title and (title is not None and custom_title is not None):
            raise ValueError("Titles don't match")
        if custom_title is None:
            custom_title = title
        elif title is None:
            pass
        super().__init__(title=custom_title, description=description, color=color)
        self.set_footer(text=footer)


class SuccessEmbed(SimpleEmbed):
    def __init__(
        self,
        description="",
        color=Color.green(),
        successTitle=None,
        title=None,
        footer=None,
    ):
        if title is None and successTitle is None:
            successTitle = "Success!"
        if title != successTitle and (title is not None and successTitle is not None):
            raise ValueError("Titles don't match")
        if successTitle is None:
            successTitle = title
        elif title is None:
            pass
        super().__init__(title=successTitle, description=description, color=color)
        self.set_footer(text=footer)
