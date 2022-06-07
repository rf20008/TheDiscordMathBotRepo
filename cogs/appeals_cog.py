import time
from os import urandom

import disnake
from disnake.ext import commands

from helpful_modules import problems_module
from helpful_modules.checks import has_privileges
from helpful_modules.custom_bot import TheDiscordMathProblemBot
from helpful_modules.custom_embeds import ErrorEmbed, SuccessEmbed
from helpful_modules.my_modals import MyModal
from helpful_modules.threads_or_useful_funcs import _generate_appeal_id

from .helper_cog import HelperCog


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

    @has_privileges(blacklisted=True)
    @commands.cooldown(1, 86400, commands.BucketType.user)
    @appeal.sub_command(name="blacklist", description="Appeal your blacklists")
    async def blacklist(self, inter: disnake.ApplicationCommandInteraction):
        """Appeal your blacklists!

        You should write out your reasoning beforehand. However, you have 20 minutes to type."""

        # Make sure they are blacklisted because if they're not blacklisted, they can't appeal
        # Get the info from the user
        modal_custom_id = str(inter.id) + urandom(10).hex()
        unblacklist_custom_id = str(inter.id) + urandom(10).hex()
        text_inputs = [
            disnake.ui.TextInput(
                label="Why should I unblacklist you? You have 20 minutes to answer",
                style=disnake.TextInputStyle.long,
                required=True,
                custom_id=unblacklist_custom_id,
            )
        ]
        reason: str = ""

        async def callback(s, modal_inter: disnake.ModalInteraction):
            s.view.stop()
            nonlocal reason
            reason = modal_inter.text_values[unblacklist_custom_id]
            await modal_inter.send(
                "Thanks! I'm now going to add this to the database :)"
            )

        modal = MyModal(
            callback=callback,
            title="Why should I un-blacklist you?",
            components=[],
            timeout=1200,
            custom_id=modal_custom_id,
        )
        modal.add_text_input(text_inputs)
        await inter.response.send_modal(modal)
        _ = await self.bot.wait_for(
            "modal_submit",
            check=lambda modal_inter: modal_inter.author.id == inter.author.id,
        )

        # Create an appeal
        # find the appeal
        highest_appeal_num = 0
        await self.bot.cache.update_cache()
        for appeal in self.cache.cached_appeals:
            if appeal.user_id != inter.author.id:
                continue
            if appeal.appeal_num > highest_appeal_num:
                highest_appeal_num = appeal.appeal_num
        highest_appeal_num += 1
        appeal: problems_module.Appeal = problems_module.Appeal(
            timestamp=time.time(),
            appeal_str=reason,
            special_id=_generate_appeal_id(inter.author.id, highest_appeal_num),
            appeal_num=highest_appeal_num,
            user_id=inter.author.id,
            type=problems_module.AppealType.BLACKLIST_APPEAL.value,
        )
        await self.cache.set_appeal_data(appeal)


def setup(bot):
    bot.add_cog(AppealsCog(bot))


def teardown(bot):
    bot.remove_cog("AppealsCog")
