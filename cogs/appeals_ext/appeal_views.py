"""
You can distribute any version of the Software created and distributed *before* 23:17:55.00 July 28, 2024 GMT-4
under the GNU General Public License version 3 or at your option, any  later option.
But versions of the code created and/or distributed *on or after* that date must be distributed
under the GNU *Affero* General Public License, version 3, or, at your option, any later version.

TheDiscordMathProblemRepo - AppealView


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

import warnings

import disnake
from helpful_modules.base_on_error import base_on_error
from helpful_modules.paginator_view import PaginatorView
from helpful_modules.custom_embeds import SuccessEmbed, ErrorEmbed
from helpful_modules.custom_bot import TheDiscordMathProblemBot
from helpful_modules.problems_module import RedisCache, MathProblemCache, Appeal, AppealViewInfo, AppealType, GuildData, UserData, PastWarning

class AppealView(PaginatorView):
    def __init__(
            self,
            cache: MathProblemCache | RedisCache,
            user_id: int,
            pages: list[str],
            special_color: disnake.Color = None,
            guild_id: int | None = None,
            appeal_type: AppealType = None,



    ):
        self.cache = cache
        super().__init__(user_id, pages, special_color)
        self.guild_id = guild_id
        self.message_id = None
        self.message = None
        self.appeal_type = appeal_type if appeal_type is not None else AppealType.NOT_SET
    async def register(
        self,
        *,
        message_id: int,
        cache: MathProblemCache | RedisCache,

    ):
        self.message_id = message_id
        await cache.set_appeal_view_info(AppealViewInfo(message_id=message_id, user_id=self.user_id, guild_id=self.guild_id, done=False, pages=self.pages))
    async def interaction_check(self, interaction: disnake.Interaction) -> bool:
        warnings.warn("The interaction check does not check whether they are the appealant, but checks whether they are trusted", category=UserWarning)
        if not isinstance(interaction.bot, TheDiscordMathProblemBot):
            raise TypeError("interaction.bot is not an instance of `TheDiscordMathProblemBot`")

        return await interaction.bot.is_trusted(interaction.author)
    async def on_error(self, error, item, inter):
        await inter.send(**(await base_on_error(inter, error)))
    @disnake.ui.button(label="Accept", style=disnake.ButtonStyle.green, row=2)
    async def accept(self, accept_button: disnake.ui.Button, inter: disnake.MessageInteraction):
        # TODO: reasons
        # TODO: deal with the fact that from_message returns only a View
        if not isinstance(inter.bot, TheDiscordMathProblemBot):
            raise TypeError("inter.bot is not an instance of `TheDiscordMathProblemBot`")
        if not await self.interaction_check(inter):
            await inter.send("You don't have permission to click this button.")
            return

        # what is the type?
        if self.appeal_type != AppealType.GUILD_DENYLIST_APPEAL and self.appeal_type != AppealType.DENYLIST_APPEAL:
            raise NotImplementedError("Accepting appeals that aren't guild denylist appeals and that aren't denylist appeals is not implemented yet")
        self.stop()
        await inter.message.edit(view=self)
        # handle guild appeal
        if self.appeal_type == AppealType.GUILD_DENYLIST_APPEAL:
            # undenylist
            old_guild_info: GuildData = await self.cache.get_guild_data(guild_id=self.guild_id)
            if not old_guild_info.is_denylisted():
                raise RuntimeError("The guild is already not on the denylist!")
            old_guild_info.undenylist()
            await self.cache.set_guild_data(data=old_guild_info)
            await inter.send(embed=SuccessEmbed(f"I successfully removed the denylist for the guild with id {self.guild_id}!"))
        elif self.appeal_type == AppealType.DENYLIST_APPEAL:
            old_user_info: UserData = await self.cache.get_user_data(user_id=self.user_id, default=UserData.default(user_id=self.user_id))
            if not old_user_info.is_denylisted():
                raise RuntimeError("This user is already not on the denylist!")
            # undenylist them
            old_user_info.undenylist()
            await self.cache.set_user_data(user_id=self.user_id, new=old_user_info)
            await inter.send(f"I successfully removed the denylist for the user with id {self.user_id}!")
        else:
            raise NotImplementedError("Other types of appeals are not supported")

        # remove them from cache
        await self.cache.del_appeal_view_info(self.message_id)






    @disnake.ui.button(label="Reject", style=disnake.ButtonStyle.red, row=2)
    async def deny(self, deny_button: disnake.ui.Button, inter: disnake.MessageInteraction):
        if inter.message.id != self.message_id:
            raise ValueError("Message ID not initialized correctly")
        if not isinstance(inter.bot, TheDiscordMathProblemBot):
            raise TypeError("inter.bot is not an instance of `TheDiscordMathProblemBot`")
        if not await self.interaction_check(inter):
            await inter.send("You don't have permission to click this button.")
            return
        if self.appeal_type != AppealType.GUILD_DENYLIST_APPEAL and self.appeal_type != AppealType.DENYLIST_APPEAL:
            raise NotImplementedError("Denylist appeals that aren't guild denylist appeals and that aren't denylist appeals are not implemented yet")
        self.stop()
        try:
            await inter.message.edit(view=self)
        except (disnake.NotFound, disnake.errors.InteractionNotResponded):
            print("oh no")
            raise
        if self.appeal_type == AppealType.GUILD_DENYLIST_APPEAL:
            # TODO: reasons
            await inter.send("This appeal of a guild denylist has been denied for an unspecified reason. You should personally notify the user that the appeal was denied and tell them why")
        elif self.appeal_type == AppealType.DENYLIST_APPEAL:
            # TODO: reasons
            await inter.send("This appeal of a user denylist has been denied for an unspecified reason. You should personally notify the user that the appeal was denied and tell them why")
        else:
            raise NotImplementedError("Other types of appeals are not supported")

        await self.cache.del_appeal_view_info(message_id=self.message_id)
    def stop(self):
        for thing in self.children:
            if isinstance(thing, disnake.ui.Button):
                thing.disabled = True
        super().stop()