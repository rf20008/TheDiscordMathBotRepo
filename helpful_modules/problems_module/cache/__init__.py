from . import *
from .misc_related_cache import MiscRelatedCache

from .problems_related_cache import ProblemsRelatedCache
from .quiz_related_cache import QuizRelatedCache
from .user_data_related_cache import UserDataRelatedCache
from .permissions_required_related_cache import PermissionsRequiredRelatedCache
from .guild_data_related_cache import GuildDataRelatedCache
from .appeals_related_cache import AppealsRelatedCache
from .final_cache import MathProblemCache

# problems_related_cache -> quiz_related_cache -> user_data_related_cache
# user_data_related_cache -> permissions_related_cache -> guild_data_related_cache
# guild_data_related_cache -> appeals_related_cache -> misc_related_cache
# misc_related_cache -> finalcache