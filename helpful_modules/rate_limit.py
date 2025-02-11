import disnake
import time
import disnake.ext.commands
from .circular_deque import CircularDeque
from .problems_module import UserData, DenylistType
from .custom_bot import TheDiscordMathProblemBot
from .threads_or_useful_funcs import first_true, last_true
ONE_MINUTE = 60
ONE_HOUR = 60 * ONE_MINUTE
ONE_DAY = 24 * ONE_HOUR
ONE_WEEK = 7 * ONE_DAY
LIMITS = {
    "day": 1440,
    "minute": 15,
    "hour": 250,
    "second": 5,
}
GLOBAL_LIMIT_PER_MIN = 1000

usage_deque: CircularDeque = CircularDeque([])
DEQUES: dict[int, CircularDeque] = {}
async def autoban(user: disnake.User, bot: TheDiscordMathProblemBot, duration: float = 30.0, reason: str = "You've been temporarily denylisted for using the bot too much recently. "):
    user_info: UserData = await bot.cache.get_user_data(user.id, default = None)
    if user_info.is_denylisted():
        return
    user_info.denylist(
        reason=reason,
        duration=duration,
        denylist_type=DenylistType.GENERAL_USER_DENYLIST,
        denylisting_moderator=bot.user.id,
    )
    await bot.cache.set_user_data(user.id, user_info)

class RateLimitedException(disnake.ext.commands.CheckFailure):
    """Raised when someone tries to run a command but they're rate limit"""
    pass
def rate_limit_check():
    async def predicate(inter: disnake.ApplicationCommandInteraction):
        if not isinstance(inter, TheDiscordMathProblemBot):
            raise TypeError
        cur_time = time.time()
        BEFORE = time.time() - ONE_DAY
        usage_deque.append_right(cur_time)

        if inter.author.id not in DEQUES.keys():
            DEQUES[inter.author.id] = CircularDeque([time.time()])
        else:
            DEQUES[inter.author.id].append_right(cur_time)
        while not DEQUES[inter.author.id].empty() and DEQUES[inter.author.id].left() < BEFORE:
            DEQUES[inter.author.id].pop_left()
        while not usage_deque.empty() and usage_deque.left() < cur_time - ONE_MINUTE:
            usage_deque.pop_left()
        if len(usage_deque) > GLOBAL_LIMIT_PER_MIN:
            raise RateLimitedException("The bot is currently experiencing a high volume of commands. Please try again later.")
        if len(DEQUES[inter.author.id]) > LIMITS["day"]:
            await autoban(
                user=inter.author,
                bot=inter.bot,
                duration = ONE_DAY,
                reason = (
                    f"You have been automatically denylisted for using the bot {LIMITS['day']} times in a day. "
                    "This denylist is appealable, and we hope that your appeal will be reviewed, but beware: \n\n"
                    "Warning 1: It is **NOT** guaranteed that your appeal will be even read. We hope that we can read your appeal,"
                    "but I am a busy high school student and I do not have the time to read every appeal. \n"
                    "Warning 2: I do not check my appeal box often. It may be faster to informally appeal in my DMs.\n"
                    "Warning 3: If you exceed 1440 requests within a 24-hour period, you will be autobanned. \n\n"
                    "Your past usage (before the appeal) will still be counted when re-evaluating your rate limit status. "
                    "Even if your appeal is approved, the autoban will be automatically reimposed if you continue to exceed the limit."
                )
            )

            raise RateLimitedException("You have been denylisted for using the bot too many times today. Please try again later. "
                                       "This denylist is appealable, but you will be automatically denylisted again if you appeal.")
        for unit, duration in (("second", 1), ("minute", ONE_MINUTE), ("hour", ONE_HOUR), ("day", ONE_DAY)):
            times_last_unit = len(DEQUES[inter.author.id]) - last_true(0, len(DEQUES[inter.author.id]), lambda t: t < cur_time - duration)
            if times_last_unit > LIMITS[unit]:
                raise RateLimitedException(f"You've used the bot too many times in the last {unit}. Please try again later.")

        return True
    return predicate