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
import disnake
from disnake.ext import commands

from helpful_modules.custom_bot import TheDiscordMathProblemBot

from .creating_quizzes_commands import CreatingQuizzesCommandsCog
from .modifying_quizzes_cog import ModifyingQuizzesCog
from .solving_commands import QuizSolveCog
from .viewing_quizzes_cog import ViewingQuizzesCog


def setup(bot: TheDiscordMathProblemBot) -> None:
    bot.add_cog(QuizSolveCog(bot))
    bot.add_cog(CreatingQuizzesCommandsCog(bot))
    bot.add_cog(ViewingQuizzesCog(bot))
    bot.add_cog(ModifyingQuizzesCog(bot))


def teardown(bot: TheDiscordMathProblemBot) -> None:
    bot.remove_cog("QuizSolveCog")
    bot.remove_cog("CreatingQuizzesCommandsCog")
    bot.remove_cog("ViewingQuizzesCog")
    bot.remove_cog("ModifyingQuizzesCog")
