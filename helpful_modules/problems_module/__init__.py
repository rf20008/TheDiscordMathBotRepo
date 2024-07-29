# This module is the 'core' of my bot!
# It's quite important.

# This module is licensed under AGPLv3 (This includes everything in this file.)

# You can distribute any version of the Software created and distributed *before* 23:17:55.00 July 28, 2024 GMT-4
# under the GNU General Public License version 3 or at your option, any  later option.
# But versions of the code created and/or distributed *on or after* that date must be distributed
# under the GNU *Affero* General Public License, version 3, or, at your option, any later version.
#
# This file and this module are part of The Discord Math Problem Bot Repo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# Author: Samuel Guo (64931063+rf20008@users.noreply.github.com)

from . import *
from .appeal import Appeal, AppealViewInfo, AppealType
from .appeal_question import AppealQuestion, APPEAL_QUESTION_TYPE_NAME
from .base_problem import BaseProblem
from .cache import *
from .cache_rewrite_with_redis import RedisCache
from .computational_problem import ComputationalProblem
from .denylistable import Denylistable
from .dict_convertible import DictConvertible
from .errors import *
from .GuildData import CheckForUserPassage, GuildData
from .linear_algebra_problem import LinearAlgebraProblem
from .parse_problem import convert_dict_to_problem, convert_row_to_problem
from .quizzes import *
from .user_data import UserData
from .verification_code_info import VerificationCodeInfo

__version__ = "0.1.0"
