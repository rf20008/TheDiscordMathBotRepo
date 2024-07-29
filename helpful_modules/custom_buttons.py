"""You can distribute any version of the Software created and distributed *before* 23:17:55.00 July 28, 2024 GMT-4
under the GNU General Public License version 3 or at your option, any  later option.
But versions of the code created and/or distributed *on or after* that date must be distributed
under the GNU *Affero* General Public License, version 3, or, at your option, any later version.

The Discord Math Problem Bot Repo - Custom Buttons

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License
as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License along with this program.
If not, see <https://www.gnu.org/licenses/>.

Author: Samuel Guo (64931063+rf20008@users.noreply.github.com)"""
from copy import deepcopy
from typing import Any, List

import disnake

from .base_on_error import base_on_error
from .custom_embeds import ErrorEmbed, SuccessEmbed

"""These are buttons that inherit from disnake's UI kit items"""


class MyView(disnake.ui.View):
    """A better? view for my bot (which is easier for my bot to work with)"""

    def __init__(
        self,
        message: disnake.Message = None,
        *,
        timeout: int = 180.0,
        items: List[disnake.ui.Item]
    ):
        super().__init__()
        self.message = message
        assert len(items) <= 25  # Discord limitation
        for item in items:
            assert isinstance(item, disnake.ui.Item)
            self.add_item(item)

    async def on_error(
        self, error: Exception, item: disnake.ui.Item, inter: disnake.Interaction
    ):
        return await inter.response.send_message(**(await base_on_error(inter, error)))

    #    async def reply(self, Interaction: disnake.Interaction, *args, **kwargs):
    #        """Reply to an interaction"""
    #        return await Interaction.response.send_message(*args, **kwargs)

    async def stop_all_items(self):
        """Stop all items. However, this does not work, because the bot will not know the message before it's sent"""
        newView = self.__class__(
            self.message, items=[]
        )  # Create a new view that has the same message
        for item in self.children:
            if item.__class__ == disnake.ui.Item:
                # It's a base item
                raise RuntimeError("Cannot stop base item")
            new_item_dict = item.__dict__
            new_item_dict["disabled"] = True  # Disable the button by editing __dict__
            newItem = item.__class__(**new_item_dict)  # Create a new item
            newView.add_item(newItem)  # Add it to the new view

        await self.message.edit(
            content=self.message.content,
            embeds=self.message.embeds,
            attachments=self.message.attachments,
            view=newView,
        )


class BasicButton(disnake.ui.Button):
    def __init__(self, check, callback, **kwargs):
        super().__init__(**kwargs)
        self.check = check
        self._callback = callback
        self.disabled = False
        try:
            self.user_for = kwargs.pop("user_for").id
        except KeyError:
            self.user_for = 2**222

    async def callback(self, interaction: disnake.Interaction) -> Any:
        if self.check(interaction=interaction):
            return await self._callback(self, interaction)

    def disable(self):
        """Disable myself. If this does not work, this is probably a Discord limitation. However, I don't know."""
        self.disabled = True

    def enable(self):
        """Enable myself. If this does not work, this is probably a Discord limitation. However, I don't know."""
        self.disabled = False


class ConfirmationButton(BasicButton):
    """A confirmation button"""

    def __init__(
        self,
        custom_id="1",
        *args,
        callback,
        check,
        _extra_data,
        message_kwargs={},
        author_for={},
        **kwargs
    ):
        """Create a new ConfirmationButton."""
        super().__init__(*args, callback=callback, custom_id=custom_id, check=check, **kwargs)  # type: ignore
        self.custom_id = custom_id
        self.author_for = author_for
        self.message_kwargs = message_kwargs
        self._func = callback

        self._extra_data = _extra_data

    async def callback(
        self: "ConfirmationButton", interaction: disnake.Interaction
    ) -> Any:
        if not self.check(interaction):
            embed = ErrorEmbed(
                description="You are not allowed to use this menu!",
                custom_title="Wrong menu :(",
            )
            await inter.send(embed=embed, ephemeral=True)
            return None
        # TBD!
        return await self._func(self, interaction, self._extra_data)
        # return await responder.send_message(**self.message_kwargs)
