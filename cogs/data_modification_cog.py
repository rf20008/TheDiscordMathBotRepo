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

import asyncio
import copy
import io
import json
import typing
from typing import *

import disnake
from disnake.ext import commands

from helpful_modules import checks, custom_bot, problems_module
from helpful_modules.custom_buttons import BasicButton, ConfirmationButton, MyView
from helpful_modules.custom_embeds import ErrorEmbed, SimpleEmbed, SuccessEmbed
from helpful_modules.threads_or_useful_funcs import file_version_of_item

from .helper_cog import HelperCog

PAGE_SIZE = 3000


class DataModificationCog(HelperCog):
    def __init__(self, bot):
        super().__init__(bot)

    @commands.slash_command(description="Interact with your user data")
    async def user_data(self, inter: disnake.ApplicationCommandInteraction):
        """The base command to interact with your user data.
        This doesn't do anything (you need to call a subcommand)"""
        pass

    @checks.is_not_denylisted()
    @disnake.ext.commands.cooldown(1, 500, commands.BucketType.user)  # To prevent abuse
    @user_data.sub_command(
        name="delete_all",
        description="Delete all problems, quizzes, and quiz submissions you created!",
        options=[
            disnake.Option(
                name="save_data_before_deletion",
                description=(
                    "Whether to give you your problems or submissions in JSON format!"
                    "Defaults to True"
                ),
                type=disnake.OptionType.boolean,
                required=False,
            ),
            disnake.Option(
                name="delete_votes",
                description="Whether to delete your votes. ",
                type=disnake.OptionType.boolean,
                required=False,
            ),
            disnake.Option(
                name="delete_solves",
                description="Whether to erase whether you have solved a problem or not",
                type=disnake.OptionType.boolean,
                required=False,
            ),
        ],
    )
    async def delete_all(
        self: "DataModificationCog",
        inter: disnake.ApplicationCommandInteraction,
        save_data_before_deletion: bool = True,
        delete_votes=False,
        delete_solves=False,
    ):
        """/user_data delete_all [save_data_before_deletion: bool = True] [delete_votes: bool = False] [delete_solves: bool = False]
        Delete all your data. YOU MUST CONFIRM THIS!
        If save_data_before_deletion, the data about you will be sent as a json file
        This has a 500-second cooldown.

        You cannot use this command if you are denylisted.

        This command will delete your permissions --

        By using this command, you agree to being DMed!"""
        if save_data_before_deletion:
            json_data: dict = await self._get_json_data_by_user(
                inter.author
            )  # Get the data
            file_version = file_version_of_item(
                str(json_data), file_name="your_data.json"
            )  # Turn it into a dictionary

        async def confirm_callback(
            Self: ConfirmationButton,
            interaction: disnake.Interaction,
            _extra_data: dict,
        ) -> None:
            """The function that runs when the button gets pressed. This actually deletes the data.
            Time complexity: O(V*N+P+S*M)
            V: number of problems user voted for
            N: number of votes for each problem the user voted for
            S: number of problems user solved
            M: number of solvers for each problem the user solved
            P: number of problems user created
            """
            assert Self.check(interaction)
            # attempt to delete all command stats (but not aggregate data such as the total # of commands)
            # and we try 2 times because race conditions
            for i in range(2):
                new_usages = []
                numberUsages = 0
                for usage in self.bot.total_stats.usages:
                    numberUsages += 1
                    if numberUsages % PAGE_SIZE == 0:
                        await asyncio.sleep(0.5)  # give other processes a chance to run
                    if usage.user_id != interaction.user.id:
                        new_usages.append(usage)
                self.bot.total_stats.usages = new_usages
                # repeat the same thing for this session
                new_usages = []
                numberUsages = 0
                for usage in self.bot.this_session.usages:
                    raise NotImplementedError("I don't know")
            kwargs = {
                "content": "Successfully deleted your data! Your data should now be cleared now."
            }
            if "file" in _extra_data.keys():
                # Return the file
                kwargs["file"] = _extra_data["file"]

            await _extra_data["cache"].delete_all_by_user_id(interaction.user.id)
            if _extra_data["delete_votes"]:
                problems_to_remove_votes_for = await _extra_data[
                    "cache"
                ].get_problems_by_func(
                    func=lambda prob, user_id: user_id in prob.voters,  # prob: problem
                    args=[interaction.user.id],
                )
                for problem in problems_to_remove_votes_for:
                    problem.voters.remove(interaction.user.id)
                    await problem.update_self()
            if _extra_data["delete_solves"]:
                problems_to_remove_solves_for = await _extra_data[
                    "cache"
                ].get_problems_by_func(
                    func=lambda problem, user_id: user_id in problem.solvers,
                    args=[interaction.user.id],
                )  # Get all the problems the user voted for
                for problem in problems_to_remove_solves_for:
                    problem.solvers.remove(interaction.user.id)
                    await problem.update_self()

            await interaction.send(**kwargs)
            Self.disable()
            Self.view.stop()
            return

        async def deny_callback(
            button: BasicButton, interaction: disnake.MessageInteraction
        ):
            """A function that runs when the deny button is pressed"""
            await interaction.response.send_message(
                "Your data is safe! It has not been deleted."
            )
            button.disable()
            button.view.stop()
            return

        _extra_data = {
            "cache": copy.copy(self.bot.cache),
            "delete_votes": delete_votes,
            "delete_solves": delete_solves,
        }
        if save_data_before_deletion:
            _extra_data["file"] = file_version

        def check(interaction: disnake.MessageInteraction):
            return interaction.author.id == inter.author.id

        confirmation_button = ConfirmationButton(
            check=check,
            callback=confirm_callback,
            style=disnake.ButtonStyle.danger,
            label="I'm 100% sure I want to delete my data!",
            disabled=False,
            _extra_data=_extra_data,
        )
        deny_button = BasicButton(
            check=check,
            callback=deny_callback,
            style=disnake.ButtonStyle.green,
            disabled=False,
            label="Never mind....",
        )
        view = MyView(timeout=30, items=[confirmation_button, deny_button])
        await inter.send(
            embed=SimpleEmbed(
                title="Are you sure?", description="This will delete all your data!"
            ),
            view=view,
        )
        return view

    async def _get_json_data_by_user(
        self, author: Union[disnake.User, disnake.Member]
    ) -> typing.Dict[str, typing.Any]:
        """
        Return a user's stored data as a dictionary.
        """
        raw_data = await self.cache.get_all_by_author_id(author.id)
        problems_user_voted_for = await self.cache.get_problems_by_func(
            func=lambda problem, user_id: user_id in problem.voters, args=(author,)
        )
        # self.bot.log.trace("Getting problems user voted & solved.")
        problems_user_solved = await self.cache.get_problems_by_func(
            func=lambda problem, user_id: user_id in problem.solvers, args=(author,)
        )
        user_data: problems_module.UserData = await self.bot.cache.get_user_data(
            user_id=author.id,
            default=problems_module.UserData(
                user_id=author.id, trusted=False, denylisted=False
            ),
        )
        is_trusted_user = user_data.trusted
        is_denylisted = user_data.denylisted

        new_data = {
            "Problems": [
                problem.to_dict(show_answer=True) for problem in raw_data["problems"]
            ],
            "Quiz Problems": [
                quiz_problem.to_dict() for quiz_problem in raw_data["quiz_problems"]
            ],
            "Quiz Submissions": [
                submission.to_dict() for submission in raw_data["quiz_submissions"]
            ],
            "Quiz Sessions Created": [
                session.to_dict() for session in raw_data["sessions"]
            ],
            "Descriptions created": [
                description.to_dict()
                for description in raw_data["descriptions_created"]
            ],
            "Problems the user voted for": [
                problem.to_dict(show_answer=False)
                for problem in problems_user_voted_for
            ],
            "Problems the user solved": [
                problem.to_dict() for problem in problems_user_solved
            ],
            "User status": {
                "trusted_user": is_trusted_user,
                "denylisted": is_denylisted,
            },
            "Appeals": [appeal.to_dict() for appeal in raw_data["appeals"]],
            "total_session_command_stats": [
                usage.to_dict()
                for usage in self.bot.total_stats.usages
                if usage.user_id == author.id
            ],
        }
        return new_data

    @disnake.ext.commands.cooldown(1, 100, disnake.ext.commands.BucketType.user)
    @user_data.sub_command(
        name="get_data",
        description="Get a json-ified version of the data stored with this application!",
    )
    async def get_data(self, inter):
        """/user_data get_data
        Get (almost) all the data the bot stores about you automatically.
        To prevent spam and getting rate limited, there is a 100-second cooldown.
        You can use this command even if you are denylisted."""
        await inter.response.defer()
        file = disnake.File(
            io.BytesIO(
                bytes(
                    json.dumps(
                        await self._get_json_data_by_user(inter.author), indent=2
                    ),
                    "utf-8",
                )
            ),
            filename="your_data.json",
        )
        # await inter.send(
        #  embed=SuccessEmbed(
        #    "Your json data will be attached in the next message due to API #limitations!"
        #  ),
        #  ephemeral = True
        # )
        try:
            await inter.send(
                embed=SuccessEmbed("Your data has been attached in this message!"),
                file=file,
            )
            # TODO: when discord api allows sending files in interaction replies, send them the file
        except BaseException as e:  # We can't send it for some reason
            raise e


def setup(bot: custom_bot.TheDiscordMathProblemBot):
    bot.add_cog(DataModificationCog(bot))
