"""
You can distribute any version of the Software created and distributed *before* 23:17:55.00 July 28, 2024 GMT-4
under the GNU General Public License version 3 or at your option, any  later option.
But versions of the code created and/or distributed *on or after* that date must be distributed
under the GNU *Affero* General Public License, version 3, or, at your option, any later version.

TheDiscordMathProblemRepo - AppealCog

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
import asyncio
from os import urandom

import disnake
from disnake.ext import commands

from helpful_modules.checks import has_privileges
from helpful_modules.custom_bot import TheDiscordMathProblemBot
from helpful_modules.custom_embeds import SuccessEmbed, ErrorEmbed

from cogs.helper_cog import HelperCog
from .appeal_modals import UserDenylistAppealModal, GuildDenylistAppealModal
from .errors import NoAppealQuestionsException
from helpful_modules.problems_module import AppealType, APPEAL_QUESTION_TYPE_NAMES


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
    def load_questions(self):
        if not self.bot.appeal_questions:
            self.bot.appeal_questions = self.bot.file_saver.load_appeal_questions()
            # are there questions?
            if not self.bot.appeal_questions:
                raise NoAppealQuestionsException("There are no appeal questions")

    @has_privileges(denylisted=True)
    @commands.cooldown(2, 86400, commands.BucketType.user)
    @appeal.sub_command(name="denylist", description="Appeal your denylists")
    async def denylist(self, inter: disnake.ApplicationCommandInteraction):
        """
        /appeal
        Appeal your denylists!

        You should write out your reasoning beforehand. However, you have 14m30s to type.
        The sole appeal question is "Why should I undenylist you?". You can respond in at most 4k chars.
        If you close the modal without saving your work somewhere else, YOUR WORK WILL BE LOST!!!!
        """
        # make sure appeal questions are loaded
        self.load_questions()

        # Make sure they are denylisted because if they're not denylisted, they can't appeal
        # Get the info from the user
        modal_custom_id = str(inter.id) + urandom(10).hex()
        undenylist_custom_id = urandom(1).hex()
        text_inputs = [
            disnake.ui.TextInput(
                label="Why should I undenylist you? ",
                style=disnake.TextInputStyle.long,
                required=True,
                custom_id=undenylist_custom_id,
            )
        ]
        reason: str = ""

        modal = UserDenylistAppealModal(
            #callback=callback,
            title="Why should I un-denylist you? (14m limit)",
            components=[question.to_textinput() for question in self.bot.appeal_questions["user_denylist"]],
            timeout=870,
            custom_id=modal_custom_id,
        )
        modal.undenylist_custom_id = modal.components[0].children[0].custom_id
        # modal.append_component(text_inputs)
        await inter.response.send_modal(modal)
        modal_inter = None

        def check(modal_i):
            if modal_i.author.id == inter.author.id:
                modal_inter = modal_i
                return True
            return False

        try:
            _ = await self.bot.wait_for("modal_submit", check=check, timeout = 870.0)
        except asyncio.TimeoutError:
            await inter.send(embed=ErrorEmbed("You did not submit the modal in time"))
            return
    @commands.cooldown(2,15,commands.BucketType.user)
    @appeal.sub_command(
        name="guild_denylist",
        description="Appeal your guild denylists"
    )
    async def guild_denylist(self, inter: disnake.ApplicationCommandInteraction):
        """/appeal guild_denylist
        Appeal Guild Denylists
        Like /appeal denylist, this gives you a questionnaire. We'll provide you the 3 questions, and you still have 20m to answer the questions.
        You can still take as much time as you need to prepare, and you should take as much time as you need to prepare.
        Here are the questions:
        1) What is your Guild ID (short answer, 100 chars)
            Enter *only* your GUILD ID, which is also your server ID, so I can know what guild you're appealing for.
            You must enter an integer or it won't be accepted by my bot
        2) "Why can *YOU* appeal for your guild/server?"
            Explain in as much or as little detail as you want why you have the authority to submit this appeal on behalf of your guild/server.
            The character limit is 4000, but that does not mean you need to write a whole essay.
            Be concise if all other things are equal.

        3) Why should I undenylist your guild?
            Explain why I should undenylist your guild.
            Things you can include is how you've improved or changes in my rules, etc.
            The character limit is 4000, but you don't need to write a whole essay. Be concise (sometimes a single sentence is enough!)
        """
        self.load_questions()
        modal_custom_id = str(inter.id) + urandom(10).hex()
        questions = self.bot.appeal_questions[APPEAL_QUESTION_TYPE_NAMES[AppealType.GUILD_DENYLIST_APPEAL]]
        textinputs = [q.to_textinput() for q in questions]
        question_custom_ids = {question: textinput.custom_id for question, textinput in zip(questions, textinputs)}
        modal = GuildDenylistAppealModal(
            timeout=870.0,
            title="Guild Denylist Appeal Questionnaire (14m max)",
            components=textinputs,
            custom_id=modal_custom_id
        )
        modal.guild_id_custom_id = textinputs[0].custom_id
        modal.reason_custom_id = textinputs[-1].custom_id
        modal.custom_ids = question_custom_ids
        print("question custom ids: ", question_custom_ids)
        await inter.response.send_modal(modal)
        try:
            _ = await self.bot.wait_for("modal_submit", check=lambda minter: minter.author.id == inter.author.id, timeout=870.0)
            return
        except asyncio.TimeoutError:
            await inter.send(embed=ErrorEmbed("You did not fill out the form in time"))
            return



    # TODO: more appeals

def setup(bot):
    bot.add_cog(AppealsCog(bot))


def teardown(bot):
    bot.remove_cog("AppealsCog")
