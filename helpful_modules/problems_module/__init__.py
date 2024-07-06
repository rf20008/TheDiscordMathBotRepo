# This module is the 'core' of my bot!
# It's quite important.

# This module is licensed under GPLv3 (This includes everything in this file.)

#     This file is part of The Discord Math Problem Bot.
#
#     The Discord Math Problem Bot is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     The Discord Math Problem Bot is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with the Discord Math Problem Bot.  If not, see <https://www.gnu.org/licenses/>.

from . import *
from .base_problem import BaseProblem
from .computational_problem import ComputationalProblem
from .linear_algebra_problem import LinearAlgebraProblem
from .cache import *
from .GuildData import GuildData, CheckForUserPassage
from .cache_rewrite_with_redis import RedisCache
from .errors import *
from .quizzes import *
from .appeal import Appeal
from .user_data import UserData
__version__ = "0.1.0"
