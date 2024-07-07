from copy import deepcopy
from typing import Any, List

import disnake

from .base_on_error import base_on_error
from .custom_embeds import ErrorEmbed, SuccessEmbed

"""These are buttons that inherit from disnake's UI kit items"""


# Licensed under the GNU GPLv3 (or later)


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
