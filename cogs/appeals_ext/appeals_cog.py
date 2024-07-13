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

import time
from os import urandom

import disnake
from disnake.ext import commands

from helpful_modules import problems_module
from helpful_modules.checks import has_privileges
from helpful_modules.custom_bot import TheDiscordMathProblemBot
from helpful_modules.custom_embeds import ErrorEmbed, SuccessEmbed
from helpful_modules.my_modals import MyModal
from helpful_modules.problems_module import Appeal, AppealViewInfo, AppealType
from .appeal_views import AppealView
from helpful_modules.threads_or_useful_funcs import generate_new_id

from cogs.helper_cog import HelperCog


class AppealModal(MyModal):
    async def callback(self, modal_inter: disnake.ModalInteraction):
        bot = modal_inter.bot
        assert isinstance(bot, TheDiscordMathProblemBot)
        assert hasattr(bot, 'cache')
        cache = bot.cache
        # nonlocal reason
        reason = modal_inter.text_values[self.undenylist_custom_id]
        await modal_inter.send("Thanks! I'm now going to add this to the database :)")

        # Create an appeal
        # find the appeal
        highest_appeal_num = 0
        try:
            await cache.update_cache()
        except NotImplementedError:
            pass
        appeal: Appeal = Appeal(
            timestamp=time.time(),
            appeal_msg=reason,
            special_id=generate_new_id(),
            appeal_num=highest_appeal_num,
            user_id=modal_inter.author.id,
            type=problems_module.AppealType.DENYLIST_APPEAL.value,
        )
        await cache.set_appeal_data(appeal)
        await modal_inter.send(embed=SuccessEmbed("Appeal should be sent?"))

        # raise NotImplementedError("The program that finds the highest appeal number is not yet implemented. However, your appeal should have been sent")
        all_appeals = await cache.get_all_appeals()
        for appeal in all_appeals:
            if appeal.user_id != modal_inter.author.id:
                continue
            if appeal.appeal_num > highest_appeal_num:
                highest_appeal_num = appeal.appeal_num
        highest_appeal_num += 1

        appeals_channel = bot.appeals_channel
        reason = f"This appeal is from {modal_inter.author.mention} and is appeal#{appeal.appeal_num}. The reason they appealed is below:. \n\n **Their reason:**\n" + reason
        pages = AppealView.break_into_pages(reason)

        our_view = AppealView(cache=bot.cache, user_id=modal_inter.author.id,
                              pages=pages, guild_id = None, appeal_type = AppealType.DENYLIST_APPEAL)
        msg = await appeals_channel.send(view=our_view, embed=our_view.create_embed())
        our_view.message_id = msg.id
        await cache.set_appeal_view_info(AppealViewInfo(
            message_id=msg.id,
            user_id=modal_inter.author.id,
            guild_id = None,
            done = False,
            pages = pages,
            appeal_type= AppealType.DENYLIST_APPEAL
        ))

class AppealsCog(HelperCog):
    def __init__(self, bot: TheDiscordMathProblemBot):
        super().__init__(bot)
        self.bot = bot
        self.cache = bot.cache

    @commands.cooldown(1, 30, commands.BucketType.user)
    @commands.slash_command(name="appeal", description="Appeal your punishments")
    async def appeal(self, inter: disnake.ApplicationCommandInteraction):
        """/appeal

        Appeal your punishments! It uses a modal.
        There are subcommands!"""
        pass

    @has_privileges(denylisted=True)
    @commands.cooldown(2, 86400, commands.BucketType.user)
    @appeal.sub_command(name="denylist", description="Appeal your denylists")
    async def denylist(self, inter: disnake.ApplicationCommandInteraction):
        """
        /appeal
        Appeal your denylists!

        You should write out your reasoning beforehand. However, you have 20 minutes to type.
        The sole appeal question is "Why should I undenylist you?". You can respond in at most 4k chars.
        If you close the modal without saving your work somewhere else, YOUR WORK WILL BE LOST!!!!
        """

        async def callback(s, modal_inter: disnake.ModalInteraction):
            s.view.stop()
            nonlocal reason
            reason = modal_inter.text_values[undenylist_custom_id]
            await modal_inter.send(
                "Thanks! I'm now going to add this to the database :)"
            )

        # Make sure they are denylisted because if they're not denylisted, they can't appeal
        # Get the info from the user
        modal_custom_id = str(inter.id) + urandom(10).hex()
        undenylist_custom_id = str(inter.id) + urandom(10).hex()
        text_inputs = [
            disnake.ui.TextInput(
                label="Why should I undenylist you? ",
                style=disnake.TextInputStyle.long,
                required=True,
                custom_id=undenylist_custom_id,
            )
        ]
        reason: str = ""

        modal = AppealModal(
            callback=callback,
            title="Why should I un-denylist you? (20m limit)",
            components=[text_inputs],
            timeout=1200,
            custom_id=modal_custom_id,
        )
        modal.undenylist_custom_id = undenylist_custom_id
        # modal.append_component(text_inputs)
        await inter.response.send_modal(modal)
        modal_inter = None

        def check(modal_i):
            if modal_i.author.id == inter.author.id:
                modal_inter = modal_i
                return True
            return False

        _ = await self.bot.wait_for("modal_submit", check=check)


def setup(bot):
    bot.add_cog(AppealsCog(bot))


def teardown(bot):
    bot.remove_cog("AppealsCog")
