"""
You can distribute any version of the Software created and distributed *before* 23:17:55.00 July 28, 2024 GMT-4
under the GNU General Public License version 3 or at your option, any  later option.
But versions of the code created and/or distributed *on or after* that date must be distributed
under the GNU *Affero* General Public License, version 3, or, at your option, any later version.

TheDiscordMathProblemRepo - AppealModal


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
import time

import disnake

from helpful_modules import problems_module
from helpful_modules.custom_bot import TheDiscordMathProblemBot
from helpful_modules.custom_embeds import SuccessEmbed, ErrorEmbed
from helpful_modules.my_modals import MyModal
from helpful_modules.problems_module import Appeal, AppealViewInfo, AppealType, AppealQuestion, APPEAL_QUESTION_TYPE_NAMES
from .appeal_views import AppealView
from helpful_modules.threads_or_useful_funcs import generate_new_id

APPEAL_TYPE_REASONS = {
    AppealType.DENYLIST_APPEAL: "Denylist Appeal",
    AppealType.GUILD_DENYLIST_APPEAL: "Guild Denylist Appeal",
    AppealType.SUPPORT_SERVER_MISC_PUNISHMENT: "Support Server Miscellaneous Punishment Appeal",
    AppealType.SUPPORT_SERVER_BAN: "Support Server Ban Appeal",
    AppealType.OTHER: "Appeal",
    AppealType.NOT_SET: "NOT SET Appeal",
    AppealType.UNKNOWN: "Unknown Appeal"
}
async def get_highest_appeal_num_for(cache: problems_module.MathProblemCache | problems_module.RedisCache, author: int):
    highest_appeal_num = 0
    all_appeals = await cache.get_all_appeals()
    for appeal in all_appeals:
        if appeal.user_id != author:
            continue
        if appeal.appeal_num > highest_appeal_num:
            highest_appeal_num = appeal.appeal_num
    highest_appeal_num += 1
    return highest_appeal_num
async def handle_appeal(
        *,
        bot: TheDiscordMathProblemBot,
        modal_inter: disnake.ModalInteraction,
        reason: str,
        cache: problems_module.MathProblemCache | problems_module.RedisCache,
        custom_ids: dict[AppealQuestion, str],
        guild_id: int | None = None,
        appeal_type: AppealType = AppealType.NOT_SET
):
    try:
        await cache.update_cache()
    except NotImplementedError:
        pass

    highest_appeal_num = await get_highest_appeal_num_for(cache, modal_inter.author.id)
    appeal: Appeal = Appeal(
        timestamp=time.time(),
        appeal_msg=reason,
        special_id=generate_new_id(),
        appeal_num=highest_appeal_num,
        user_id=modal_inter.author.id,
        #guild_id=guild_id,
        type=appeal_type.value,
    )
    await cache.set_appeal_data(appeal)
    await modal_inter.send(embed=SuccessEmbed("Appeal should be sent?"))



    appeals_channel = bot.appeals_channel
    # reason = f"This appeal is from {modal_inter.author.mention} and appeals. The reason they appealed is below:. \n\n **Their reason:**\n" + reason

    our_view = AppealView(cache=bot.cache, user_id=modal_inter.author.id, pages=[], special_color=disnake.Color.red(),
                          guild_id=guild_id, appeal_type=AppealType.GUILD_DENYLIST_APPEAL)
    our_view.add_pages(AppealView.break_into_pages(
        f"This {APPEAL_TYPE_REASONS[appeal_type]} is from {modal_inter.author.mention} and appeals for the guild with guild id {guild_id}." +
        f"This is appeal#{highest_appeal_num}"

    ))
    for question in bot.appeal_questions[APPEAL_QUESTION_TYPE_NAMES[appeal_type]]:
        try:
            # Attempt to add pages
            our_view.add_pages(
                our_view.break_into_pages(
                    f"**{question.question}**: \n\n {modal_inter.text_values[custom_ids[question]]}"
                )
            )
        except KeyError as kerr:
            # Determine what went wrong
            if question not in custom_ids:
                # Handle missing question key
                raise KeyError(f"{question} doesn't have a key in `custom_ids`, which is {custom_ids}") from kerr
            elif custom_ids[question] not in modal_inter.text_values:
                # Handle missing text value key
                raise KeyError(
                    f"{custom_ids[question]} doesn't have a key in the text values, which are `{modal_inter.text_values}`"
                ) from kerr
            else:
                # Catch any other unexpected KeyError
                raise RuntimeError("Unexpected KeyError occurred") from kerr

    msg = await appeals_channel.send(view=our_view, embed=our_view.create_embed())
    our_view.message_id = msg.id
    await cache.set_appeal_view_info(AppealViewInfo(
        message_id=msg.id,
        user_id=modal_inter.author.id,
        guild_id=None,
        done=False,
        pages=our_view.pages,
        appeal_type=AppealType.DENYLIST_APPEAL
    ))


class AppealModal(MyModal):
    bot: TheDiscordMathProblemBot
    custom_ids: dict[AppealQuestion, str]
    def __init__(self, *args, **kwargs):
        self.custom_ids = kwargs.pop("custom_ids", {})

        super().__init__(*args, **kwargs)
    async def callback(self, modal_inter: disnake.ModalInteraction):
        if not isinstance(modal_inter.bot, TheDiscordMathProblemBot):
            raise TypeError("The bot is of the wrong type")
        self.bot = modal_inter.bot # type: ignore # (we did a type check earlier)
        assert isinstance(self.bot, TheDiscordMathProblemBot)
        assert hasattr(self.bot, 'cache')
class UserDenylistAppealModal(AppealModal):
    undenylist_custom_id: str
    def __init__(self, *args, **kwargs):
        self.undenylist_custom_id = kwargs.pop("undenylist_custom_id", None)
        super().__init__(*args, **kwargs)

    async def callback(self, modal_inter: disnake.ModalInteraction):
        await super().callback(modal_inter)
        cache = self.bot.cache
        # nonlocal reason
        reason = modal_inter.text_values[self.undenylist_custom_id]
        await modal_inter.send(embed=SuccessEmbed("Thanks! I'm now going to add this to the database :)"))

        # Create an appeal
        # find the appeal
        highest_appeal_num = 0
        try:
            await cache.update_cache()
        except NotImplementedError:
            pass
        await handle_appeal(
            bot=self.bot,
            modal_inter=modal_inter,
            reason=reason,
            cache=self.bot.cache,
            guild_id=None,
            appeal_type=AppealType.DENYLIST_APPEAL,
            custom_ids=self.custom_ids
        )
class GuildDenylistAppealModal(AppealModal):
    guild_id_custom_id: str
    custom_ids: dict[AppealQuestion, str]
    represent_custom_id: str
    reason_custom_id: str
    async def callback(self, modal_inter: disnake.ModalInteraction):
        await super().callback(modal_inter)
        bot = modal_inter.bot
        if not isinstance(bot, TheDiscordMathProblemBot):
            raise TypeError
        assert hasattr(bot, 'cache')
        cache = bot.cache
        # nonlocal reason

        try:
            guild_id = int(modal_inter.text_values[self.guild_id_custom_id])
        except ValueError:
            await modal_inter.send(embed=ErrorEmbed("Your guild ID is not an integer"))
            return

        data = await self.bot.cache.get_guild_data(guild_id=guild_id, default=None)

        if not self.bot.is_denylisted_by_guild_id(guild_id):
            await modal_inter.send(embed=ErrorEmbed("Your Guild is not actually denylisted"))
            return
        reason = modal_inter.text_values[self.reason_custom_id]
        await modal_inter.send(embed=SuccessEmbed("Thanks! I'm now going to add this to the database :)"))

        # Create an appeal
        # find the appeal

        await handle_appeal(
            bot=bot,
            modal_inter=modal_inter,
            reason = reason,
            cache= bot.cache,
            guild_id=guild_id,
            appeal_type=AppealType.GUILD_DENYLIST_APPEAL,
            custom_ids=self.custom_ids
        )


