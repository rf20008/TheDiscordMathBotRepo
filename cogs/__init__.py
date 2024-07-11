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

# The test_cogs folder! This contains all my test_cogs
"""A folder containing all the test_cogs!"""
from . import *
from .appeals_ext import *
from .appeals_ext.appeals_cog import AppealsCog
from .config_cog import GuildConfigCog
from .data_modification_cog import DataModificationCog
from .debug_cog import DebugCog
from .developer_commands import DeveloperCommands
from .documentation_cog import HelpCog
from .handle_errors import ErrorHandlerCog
from .helper_cog import HelperCog
from .interesting_computation_ import InterestingComputationCog
from .misc_commands_cog import MiscCommandsCog
from .problem_generation_cog import ProblemGenerationCog
from .problems_cog import ProblemsCog
from .quiz_cog import QuizCog
from .quiz_ext import *
from .suggestion_ext import *
from .test_cog import TestCog
from .verification_cog import VerificationCog
