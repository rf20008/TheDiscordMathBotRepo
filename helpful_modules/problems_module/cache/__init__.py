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
from .appeals_related_cache import AppealsRelatedCache
from .final_cache import MathProblemCache
from .guild_data_related_cache import GuildDataRelatedCache
from .misc_related_cache import MiscRelatedCache
from .permissions_required_related_cache import PermissionsRequiredRelatedCache
from .problems_related_cache import ProblemsRelatedCache
from .quiz_related_cache import QuizRelatedCache
from .user_data_related_cache import UserDataRelatedCache

# problems_related_cache -> quiz_related_cache -> user_data_related_cache
# user_data_related_cache -> permissions_related_cache -> guild_data_related_cache
# guild_data_related_cache -> appeals_related_cache -> misc_related_cache
# misc_related_cache -> finalcache
