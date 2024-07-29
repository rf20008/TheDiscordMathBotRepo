"""
You can distribute any version of the Software created and distributed *before* 23:17:55.00 July 28, 2024 GMT-4
under the GNU General Public License version 3 or at your option, any  later option.
But versions of the code created and/or distributed *on or after* that date must be distributed
under the GNU *Affero* General Public License, version 3, or, at your option, any later version.

This file is part of TheDiscordMathProblemBotRepo

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
from typing import List, Optional, Union

import disnake
from disnake import ui
from disnake.ext import commands

from helpful_modules import problems_module as pm
from helpful_modules.custom_bot import TheDiscordMathProblemBot
from helpful_modules.my_modals import MyModal
from helpful_modules.base_on_error import base_on_error


class GradingQuizView(ui.View):
    def __init__(
        self,
        *,
        quiz_id: int,
        user_id: int,
        bot: TheDiscordMathProblemBot,
        attempt_num: int,
        problem_num: int,
        grader_user_id: int,
        timeout: int = 600
    ):
        super().__init__(
            title=title, components=components, custom_id=custom_id, timeout=timeout
        )
        self._buttons = (self.exit_and_stop, self.continue_grading)
        self.quiz_id = quiz_id
        self.user_id = user_id
        self._bot = bot
        self._attempt_num = attempt_num
        self.target = grader_user_id
        self.problem_num = problem_num

    async def interaction_check(self, inter: disnake.Interaction):
        """Make sure this view is only used by who it's intended to be used!"""
        return inter.author.id == self.target

    def stop(self):
        super().__stop__()
        for button in self._buttons:
            button.disabled = True

    @ui.button(
        label="Exit and stop grading (Your changes will be saved)",
        style=disnake.ButtonStyle.danger,
    )
    async def exit_and_stop(
        self,
        button: disnake.Button,
        inter: disnake.MessageInteraction,
    ):
        button.disabled = True
        content = inter.message.content
        content = "Thank you for grading Your changes have been saved!" + content
        self.stop()
        await inter.response.edit_message(content=content, view=self)
        return

    @ui.button(label="Continue Grading", style=disnake.ButtonStyle.green)
    async def continue_grading(
        self, button: disnake.ui.Button, inter: disnake.MessageInteraction
    ):
        assert button == self.continue_grading
        assert isinstance(inter.bot, TheDiscordMathProblemBot)
        reasoning_input_custom_id = os.urandom(13).hex() + inter.id
        grade_input_custom_id = os.urandom(14).hex() + inter.id
        the_modal_custom_id = os.urandom(15).hex() + inter.id
        modal_to_send = MyModal(
            target_user_id=self.user_id,
            bot=inter.bot,
            quiz_id=self.quiz_id,
            grader_user_id=inter.author.id,
            attempt_num=self.attempt_num,
            problem_num=self.problem_num,
            channel=inter.channel,
            reasoning_input_custom_id=reasoning_input_custom_id,
            grade_input_custom_id=grade_input_custom_id,
            title="Grade this quiz's submission problem number #",
            components=[],
            custom_id=the_modal_custom_id,
            timeout=60 * 60,
        )
        # raise NotImplementedError("Oh No! This isn't fully implemented yet!!!")
        modal_to_send.add_text_input(
            label="What will you choose?",
        )
        await inter.response.send_modal(modal_to_send)

    async def on_error(self, _: ui.Item, exc: Exception):
        await base_on_error(exc)
        raise NotImplementedError

    async def interaction_check(self, inter: disnake.MessageInteraction):
        return inter.author.id == self.grader_user_id and inter.component.custom_id in [
            self.continue_grading.custom_id,
            self.exit_and_stop.custom_id,
        ]


async def on_grade_modal_callback(
    modal_inter: disnake.ModalInteraction,
    quiz_id: int,
    reasoning_input_custom_id: str,
    grade_input_custom_id: str,
    cache: pm.MathProblemCache,
    problem_num: int,
    user_id: int,
    attempt_num: int,
):
    quiz: Quiz = await cache.get_quiz(quiz_id)
    try:
        grade = float(modal_inter.text_values[grade_input_custom_id])
    except ValueError:
        await modal_inter.send("Invalid input....")
        return

    submissions = list(
        filter(
            lambda session: session.user_id == user_id
            and session.attempt_num == attempt_num,
            quiz.existing_sessions,
        )
    )
    session: pm.QuizSolvingSession = copy.copy(submissions[0])
    submission = session.answers[problem_num]
    submission.set_grade(grade)
    submission.reasoning = modal_inter.text_values[reasoning_input_custom_id]
    await quiz.update_self()
    await modal_inter.send(
        view=GradingQuizView(
            timeout=200,
            user_id=user_id,
            quiz_id=quiz_id,
            grader_user_id=inter.author.id,
            bot=inter.bot,
            attempt_num=attempt_num,
            channel=modal_inter.channel,
        )
    )


class GradingModal(ui.Modal):
    def __init__(
        self,
        *,
        target_user_id: int,
        bot: TheDiscordMathProblemBot,
        quiz_id: int,
        grader_user_id: int,
        attempt_num: int,
        problem_num: int,
        channel: Union[disnake.TextChannel, disnake.PartialMessageable],
        reasoning_input_custom_id: str,
        grade_input_custom_id: str,
        title: str,
        components: Union[
            disnake.ui.ActionRow,
            disnake.ui.WrappedComponent,
            List[
                Union[
                    disnake.ui.ActionRow,
                    disnake.ui.WrappedComponent,
                    List[disnake.ui.WrappedComponent],
                ]
            ],
        ],
        custom_id=...,
        timeout=60 * 60
    ):
        super().__init__(
            title=title, components=components, custom_id=custom_id, timeout=timeout
        )
        self._bot = bot
        self.quiz_id = quiz_id
        self.grader_quiz_id = (grader_user_id,)
        self.target_user_id = target_user_id
        self._attempt_num = attempt_num
        self._channel = channel
        self.reasoning_input_custom_id = reasoning_input_custom_id
        self.grade_input_custom_id = grade_input_custom_id
        self.problem_num = problem_num

    async def on_timeout(self):
        try:
            await self._channel.send("You didn't submit the modal in time!")
        except disnake.Forbidden:
            raise RuntimeError(
                "I don't have permission to send to the channel and tell them that they ran out of time"
            )

    async def callback(self, inter: disnake.ModalInteraction):
        if inter.author.id is not self.grader_quiz_id:
            raise RuntimeError("Uh oh!")
        assert isinstance(inter.bot, TheDiscordMathProblemBot)

        # raise NotImplementedError("I haven't fully implemented this yet!")
        return await on_grade_modal_callback(
            modal_inter=inter,
            quiz_id=self.quiz_id,
            grade_input_custom_id=self.grade_input_custom_id,
            reasoning_input_custom_id=self.reasoning_input_custom_id,
            problem_num=self.problem_num,
            attempt_num=self._attempt_num,
            cache=inter.bot.cache,
        )

    async def on_error(self, error: Exception, inter: disnake.ModalInteraction):
        return await inter.send(**base_on_error(inter, error))


def setup(*args):
    pass
