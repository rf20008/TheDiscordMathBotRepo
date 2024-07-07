from typing import Optional, Union

import disnake
from disnake import abc, ui
from disnake.ext import commands

from helpful_modules import custom_bot, problems_module
from helpful_modules.base_on_error import base_on_error
from helpful_modules.custom_bot import TheDiscordMathProblemBot


class GuildDataDeletionView(ui.View):
    def __init__(
        self,
        bot: TheDiscordMathProblemBot,
        inter: Union[disnake.ApplicationCommandInteraction, commands.Context],
        timeout: int = 180.0,
    ):
        self.timeout = timeout
        self.inter = inter
        self.bot = bot
        if self.inter.guild is None:
            raise RuntimeError("The guild must be set in order to delete data")

        if not self.inter.author.id == self.inter.guild.owner_id:
            raise RuntimeError(
                "The user does not have enough permission to request deletion of the data "
                "because the user is not the owner of the guild "
                "that the interaction/context was sent in."
            )

    @ui.button(label="Cancel Deletion", style=disnake.ButtonStyle.green)
    async def cancel_deletion(
        self, button: disnake.Button, inter: disnake.MessageInteraction
    ):
        self.stop()
        button.disabled = True
        await inter.response.edit_message(view=self)
        await inter.channel.send("You have successfully prevented the data deletion!")

    async def interaction_check(self, inter: disnake.MessageInteraction):  #
        """Check that only guild owners can run this command in guilds that they own
        This cannot be static."""
        if inter.guild_id is None or inter.guild is None:
            raise commands.CheckFailure(
                "This is not in a guild. You can only get GuildDataDeletionViews in a guild."
            )

        return (
            inter.guild.owner_id == inter.author.id
        )  # return whether they own the guild

    @ui.button(label="Delete the data! This is irreversible")
    async def delete_data(self, _: disnake.Button, inter: disnake.MessageInteraction):
        """Actually delete data"""
        if not await self.interaction_check(inter):
            return await inter.send(
                "You don't have permission to delete all the guild's data"
            )
        if inter.guild_id is None:
            raise RuntimeError("This should not be running globally")
        await self.bot.cache.delete_all_by_guild_id(inter.guild_id)
        return await inter.send("Almost all the guild's data has been deleted!")

    async def on_timeout(self):
        for item in self.children:
            if not isinstance(item, disnake.ui.Item):
                raise RuntimeError()
            if hasattr(item, "disabled"):
                if not getattr(item, "disabled", False):
                    item.disabled = True

    async def on_error(
        self, err: Exception, _: disnake.ui.Item, inter: disnake.MessageInteraction
    ):
        for item in self.children:
            if not isinstance(item, disnake.ui.Item):
                raise RuntimeError()
            if hasattr(item, "disabled"):
                if not getattr(item, "disabled", False):
                    item.disabled = True
        await inter.message.edit(view=self)
        await inter.send(**base_on_error(inter, err))


def setup(*args):
    pass
