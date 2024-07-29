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
from math import gcd

import disnake
import more_itertools
from disnake.ext import commands, tasks
from mpmath import *

from helpful_modules import checks, custom_bot, problems_module, threads_or_useful_funcs
from helpful_modules.custom_embeds import ErrorEmbed, SimpleEmbed, SuccessEmbed
from helpful_modules.problems_module import *

from .helper_cog import HelperCog

MAX_NUM = 1_000_000_000_000_000_000_000_000_000_000


class InterestingComputationCog(HelperCog):
    def __init__(self, bot):
        self.bot = bot
        self.cache = bot.cache
        super().__init__(bot)

    class ChineseRemainderTheoremComputer:
        def __init__(self, remainders, moduli):
            if len(remainders) != len(moduli):
                raise ValueError(
                    "The length of the remainders does not equal the length of the moduli!"
                )
            for a, b in more_itertools.distinct_combinations(moduli, 2):
                if gcd(a, b) != 1:
                    raise ValueError(
                        "Not all the moduli are relatively pairwise coprime!!!!!!"
                    )
            for i in range(len(moduli)):
                if not (
                    isinstance(remainders[i], int)
                    and isinstance(moduli[i], int)
                    and moduli[i] > remainders[i] > 0
                ):
                    raise ValueError("The CRT prerequsites are not satisifed!")
            self.remainders = remainders
            self.moduli = moduli

        def compute(self):
            """Compute the CRT
            Algorithm credits to my brother"""
            product = 1
            for i in range(len(self.moduli)):
                product *= self.moduli[i]
            su = 0
            for i in range(len(self.moduli)):
                num = product // self.moduli[i]
                # compute the multiplicative number of product/b_i mod b_i
                return_val = threads_or_useful_funcs.extended_gcd(
                    product, self.moduli[i]
                )  # replace with pow(product, -1, self.moduli[i]) since pow can compute modular inverses
                try:
                    return_val = pow(product, -1, self.moduli[i])
                except ValueError:
                    raise ValueError("They aren't relatively prime")
                mult_inv = return_val[0][1]
                su += num * mult_inv * self.remainders[i]
            return su

    @checks.no_insanely_huge_numbers_check()
    @commands.slash_command(name="crt_problem", description="crt_problem")
    async def crt_problem(
        self, inter: disnake.ApplicationCommandInteraction, moduli: str, nums: str
    ):
        """/crt_problem (moduli: str (should be a space-seperated list of numbers)) (nums: str (should be a space-seperated list of numbers)
        Solve the CRT problem for when the moduli are `moduli` and the nums are `nums`

        """
        moduliA = moduli
        numsA = nums

        if len(moduliA) >= 300 or len(numsA) >= 300:
            return await inter.send(embed=ErrorEmbed("Too many moduli or nums!"))
        try:
            moduli = [int(item) for item in moduliA.split()]
        except ValueError:
            await inter.send(
                embed=ErrorEmbed("Could not convert moduli to a list of numbers!")
            )
            raise
        if len(moduli) >= 100:
            return await inter.send(embed=ErrorEmbed("Too many moduli!"))
        if len(moduli) >= 100:
            return inter.send(embed=ErrorEmbed("Too many moduli!"))
        for i in moduli:
            if i <= 0 or i > 10**30:
                return inter.send("All the remainders must be positive")

        # linear time solution to check for relatively prime:
        # compute a_1a_2a_3...a_n=C
        # then for each n from 1 to n:
        # compute C/a_i mod a_i (call it D)
        # if gcd(a_i, D) != 1 then they are not pairwise relatively prime
        # proof: if a_1 is relatively prime to a_2, a_3, a_4, ..., a_n then it is relatively prime to a_2a_3a_4...a_n

        for num1, num2 in more_itertools.distinct_combinations(moduli, 2):
            if gcd(moduli[i], moduli[j]) != 1:
                return await inter.send(
                    embed=ErrorEmbed(
                        "The chinese remainder theorem doesn't hold unless the numbers are relatively prime"
                    )
                )
            if moduli[i] >= MAX_NUM:
                raise MathProblemsModuleException("Remainder too big")
            for j in range(i, len(moduli)):
                if gcd(moduli[i], moduli[j]) != 1:
                    return await inter.send(
                        embed=ErrorEmbed(
                            f"The chinese remainder theorem doesn't hold unless the numbers are relatively prime. The numbers that aren't relatively prime are {moduli[i]} and {moduli[j]} (which have a gcd of {gcd(moduli[i], moduli[j])})."
                        )
                    )

        try:
            nums = [int(item) for item in numsA.split()]
        except ValueError:
            await inter.send(
                embed=ErrorEmbed("Could not convert nums to a list of numbers!")
            )
            raise
        if len(nums) >= 100:
            return await inter.send(embed=ErrorEmbed("Too many nums!"))
        if len(moduli) != len(nums):
            return await inter.send(
                embed=ErrorEmbed("#moduli != # nums : therefore we can't use CRT.")
            )

        for i in range(len(nums)):
            if nums[i] <= 0:
                return await inter.send("All the remainders must be positive!")
            if nums[i] >= MAX_NUM:
                raise MathProblemsModuleException("Number too big")
            if nums[i] >= moduli[i]:
                raise MathProblemsModuleException("nums[i] > moduli[i]")
        CRTC = InterestingComputationCog.ChineseRemainderTheoremComputer(
            remainders=nums, moduli=moduli
        )
        inter.send(embed=SuccessEmbed(f"The result is f{CRTC.compute()}."))
        return


def setup(bot):
    bot.add_cog(InterestingComputationCog(bot))


def teardown(bot):
    bot.remove_cog("InterestingComputationCog")
