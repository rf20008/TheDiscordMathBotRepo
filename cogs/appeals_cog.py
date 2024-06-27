import time
from os import urandom

import disnake
from disnake.ext import commands

from helpful_modules import problems_module
from helpful_modules.checks import has_privileges
from helpful_modules.custom_bot import TheDiscordMathProblemBot
from helpful_modules.custom_embeds import ErrorEmbed, SuccessEmbed
from helpful_modules.my_modals import MyModal
from helpful_modules.threads_or_useful_funcs import _generate_special_id
from helpful_modules.problems_module import Appeal
from .helper_cog import HelperCog

class AppealModal(MyModal):
    async def callback(s, modal_inter: disnake.ModalInteraction):
        s.view.stop()
        nonlocal reason
        reason = modal_inter.text_values[undenylist_custom_id]
        await modal_inter.send(
            "Thanks! I'm now going to add this to the database :)"
        )
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
                label="Why should I undenylist you? You have 20 minutes to answer",
                style=disnake.TextInputStyle.long,
                required=True,
                custom_id=undenylist_custom_id,
            )
        ]
        reason: str = ""



        modal = MyModal(
            callback=callback,
            title="Why should I un-denylist you?",
            components=[text_inputs],
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
        try:
            await self.bot.cache.update_cache()
        except NotImplementedError:
            pass
        appeal: problems_module.Appeal = problems_module.Appeal(
            timestamp=time.time(),
            appeal_str=reason,
            special_id=_generate_appeal_id(inter.author.id, highest_appeal_num),
            appeal_num=highest_appeal_num,
            user_id=inter.author.id,
            type=problems_module.AppealType.DENYKLIST_APPEAL.value,
        )
        await self.cache.set_appeal_data(appeal)
        raise NotImplementedError("The program that finds the highest appeal number is not yet implemented. However, your appeal should have been sent")
        for appeal in self.cache.cached_appeals:
            if appeal.user_id != inter.author.id:
                continue
            if appeal.appeal_num > highest_appeal_num:
                highest_appeal_num = appeal.appeal_num
        highest_appeal_num += 1



def setup(bot):
    bot.add_cog(AppealsCog(bot))


def teardown(bot):
    bot.remove_cog("AppealsCog")
