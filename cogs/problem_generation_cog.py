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

import random
import typing

import disnake
from disnake import Option, OptionType
from disnake.ext import commands

from helpful_modules import checks, problems_module
from helpful_modules.custom_bot import TheDiscordMathProblemBot
from helpful_modules.custom_embeds import ErrorEmbed, SuccessEmbed
from helpful_modules.problem_generator import (
    generate_arithmetic_problem,
    generate_linear_algebra_problem,
)
from helpful_modules.threads_or_useful_funcs import generate_new_id

from .helper_cog import HelperCog

PROBLEM_GENERATORS = [generate_arithmetic_problem, generate_linear_algebra_problem]


class ProblemGenerationCog(HelperCog):
    def __init__(self, bot: TheDiscordMathProblemBot):
        super().__init__(bot)
        self.bot: TheDiscordMathProblemBot = bot
        # checks = self.checks
        checks.setup(bot)

    @commands.slash_command(
        name="generate_new_problems",
        description="Generates new problems",
        options=[
            Option(
                name="num_new_problems_to_generate",
                description="the number of problems that should be generated",
                type=OptionType.integer,
                required=True,
            )
        ],
    )
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def generate_new_problems(
        self,
        inter: disnake.ApplicationCommandInteraction,
        num_new_problems_to_generate: int,
    ) -> typing.Optional[disnake.Message]:
        """/generate_new_problems [num_new_problems_to_generate: int]
        Generate new Problems."""
        # TODO: problem_generator class (and use formulas :-))

        if not self.bot.is_trusted(inter.author):
            await inter.send(embed=ErrorEmbed("You aren't trusted!"), ephemeral=True)
            return
        if num_new_problems_to_generate > 200:
            return await inter.send(
                embed=ErrorEmbed(
                    "You are trying to create too many problems. Try something smaller than or equal to 200."
                ),
                ephemeral=True,
            )
        if num_new_problems_to_generate < 0:
            return await inter.send(
                embed=ErrorEmbed("You can only create a positive number of problems")
            )
        for i in range(num_new_problems_to_generate):  # basic problems for now.... :(
            print(i)
            # TODO: linear equations, etc

            while True:
                problem_id = generate_new_id()
                try:
                    already_existing_problem = await self.cache.get_problem(
                        None, problem_id
                    )
                    print(already_existing_problem)
                except problems_module.ProblemNotFound:
                    break

            problem_generator = random.choice(PROBLEM_GENERATORS)
            problem = problem_generator()
            print(problem)
            await self.cache.add_problem(problem_id, problem)

        try:
            await self.cache.bgsave(schedule=True)
        except problems_module.errors.BGSaveNotSupportedOnSQLException:
            pass
        await inter.send(
            embed=SuccessEmbed(
                f"Successfully created {str(num_new_problems_to_generate)} new problems!"
            ),
            ephemeral=True,
        )


def setup(bot: TheDiscordMathProblemBot):
    bot.add_cog(ProblemGenerationCog(bot))


def teardown(bot):
    bot.remove_cog("ProblemGenerationCog")
