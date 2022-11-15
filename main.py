# Written by @rf20008
# Licensed under GPLv3 (or later)
# Feel free to contribute! :-)
# Python 3.10+ is required.

# imports - standard library
import asyncio
import logging
import threading
import typing
import warnings
from asyncio import sleep as asyncio_sleep
from copy import copy
from logging import handlers
from sys import argv, exc_info, exit, stdout

# Imports - 3rd party
from disnake.ext import commands

from cogs import *
from helpful_modules import (checks, custom_embeds, problems_module,
                             return_intents, save_files,
                             the_documentation_file_loader)
from helpful_modules.constants_loader import *
from helpful_modules.cooldowns import check_for_cooldown
from helpful_modules.custom_bot import TheDiscordMathProblemBot
from helpful_modules.threads_or_useful_funcs import *

# Imports - My own files




if (
    not __debug__
):  # __debug__ must be true for the bot to run (because assert statements)
    exit("__debug__ must be True for the bot to run! (Don't run with -o or -OO)")
del exit
VERSION = "0.0.8a1"
try:
    import dotenv  # https://pypi.org/project/python-dotenv/

    assert hasattr(dotenv, "load_dotenv") and hasattr(dotenv, "find_dotenv")
except (ModuleNotFoundError, AssertionError):
    raise RuntimeError("Dotenv could not be found, therefore cannot load .env")
env_path = dotenv.find_dotenv()
dotenv.load_dotenv(env_path)
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN", None)
if DISCORD_TOKEN is None:
    raise RuntimeError("Cannot start bot; no discord_token environment variable")

# TODO: use logging + changelog.json + debugging :-)
# TODO: fix SQL errors
# TODO: store logs

should_we_connect = True
if len(argv) >= 3:
    if argv[2] == "DO_NOT_CONNECT":
        should_we_connect=False
 
TRFHB = handlers.TimedRotatingFileHandler(
    filename="logs/bot.log", when="midnight", encoding="utf-8", backupCount=300
)  # TimedRotatingFileHandler(for the)Bot
TRFHD = handlers.TimedRotatingFileHandler(
    filename="logs/disnake.log", when="midnight", encoding="utf-8", backupCount=300
)  # TimedRotatingFileHandler(for) Disnake
assert TRFHD != TRFHB
if __name__ == "__main__":
    log = logging.getLogger()
else:
    log = logging.getLogger(__name__)
disnake_log = logging.getLogger("disnake")
log.addHandler(TRFHB)
disnake_log.addHandler(TRFHD)
log.setLevel(-1)
disnake_log.setLevel(logging.INFO)


def the_daemon_file_saver():
    """Auto-save files!"""
    global bot, guildMathProblems, trusted_users, vote_threshold
    print("Initializing the File Saver")
    FileSaverObj = save_files.FileSaver(
        name="The Daemon File Saver", enabled=True, printSuccessMessagesByDefault=True
    )
    print("Loading files...")
    FileSaverDict = FileSaverObj.load_files(bot.cache, True)
    (guildMathProblems, bot.trusted_users, bot.vote_threshold) = (
        FileSaverDict["guildMathProblems"],
        FileSaverDict["trusted_users"],
        int(FileSaverDict["vote_threshold"]),
    )
    while True:
        sleep(45)
        print("Saving files")
        FileSaverObj.save_files(
            bot.cache,
            False,
            guildMathProblems,
            bot.vote_threshold,
            bot.trusted_users,
        )


loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
warnings.simplefilter("default")  # unnecessary, probably will be removed
# constants

trusted_users = []
try:
    DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
    assert DISCORD_TOKEN is not None
except (KeyError, AssertionError):
    raise RuntimeError(
        "You haven't setup the .env file correctly! You need DISCORD_TOKEN=<your token>"
    )
bot_constants = BotConstants(dotenv.find_dotenv())
main_cache = problems_module.MathProblemCache(
    max_answer_length=2000,
    max_question_limit=2000,
    max_guild_problems=125,
    warnings_or_errors="errors",
    db_name="MathProblemCache1.db",
    update_cache_by_default_when_requesting=True,
    use_cached_problems=False,
    mysql_username=bot_constants.MYSQL_USERNAME,
    mysql_password=bot_constants.MYSQL_PASSWORD,
    mysql_db_ip=bot_constants.MYSQL_DB_IP,
    mysql_db_name=bot_constants.MYSQL_DB_NAME,
    use_sqlite=bot_constants.USE_SQLITE,
)  # Generate a new cache for the bot!
assert main_cache.db is main_cache.db_name
vote_threshold = -1  # default
mathProblems = {}
guildMathProblems = {}
guild_maximum_problem_limit = 125


def loading_documentation_thread():
    """This thread reloads the documentation."""
    d = DocumentationFileLoader()
    d.load_documentation_into_readable_files()
    del d


loader = threading.Thread(target=loading_documentation_thread)
loader.start()


def get_git_revision_hash() -> str:
    """A method that gets the git revision hash. Credit to https://stackoverflow.com/a/21901260 for the code :-)"""
    return (
        subprocess.check_output(["git", "rev-parse", "HEAD"])
        .decode("ascii")
        .strip()[:7]
    )  # [7:] is here because of the commit hash, the rest of this function is from stack overflow


# @bot.event
async def on_ready(bot: TheDiscordMathProblemBot):
    """Ran when the disnake library detects that the bot is ready"""
    app_info = await bot.application_info()

    print("The bot is now ready!")
    print(f"I connected as {bot.user.name}#{bot.user.discriminator}.")
    print(
        f"My owner id is {bot.owner_id if bot.owner_id is not None else app_info.owner.id}!"
    )
    if bot.owner_id is None and app_info.owner.id is not None:
        bot.owner_id = app_info.owner.id

    print(f"My owner ids are {bot.owner_ids}")


# Bot creation

asyncio.set_event_loop(asyncio.new_event_loop())  # Otherwise, weird errors will happen
bot = TheDiscordMathProblemBot(
    intents=return_intents.return_intents(),
    application_id=845751152901750824,
    status=disnake.Status.idle,
    cache=main_cache,
    constants=bot_constants,
    trusted_users=copy(trusted_users),
    tasks={},
    on_ready_func=on_ready,
    loop=loop
    # activity = nextcord.CustomActivity(name="Making sure that the bot works!", emoji = "🙂") # This didn't work anyway, will set the activity in on_connect
)
# TODO: move bot events + initializing to custom_bot.py
bot._sync_commands_debug = True
# setup(bot)
# bot._transport_modules = {
#    "problems_module": problems_module,
#    "save_files": save_files,
#    "the_documentation_file_loader": the_documentation_file_loader,
#    "check_for_cooldown": check_for_cooldown,
#    "custom_embeds": custom_embeds,
#    "checks": checks,
# }
bot.add_check(
    disnake.ext.commands.bot_has_permissions(
        send_messages=True,
        read_messages=True,
        embed_links=True,
    )
)
_the_daemon_file_saver = threading.Thread(
    target=the_daemon_file_saver,
    name="The File Saver",
    daemon=True,
    # Make sure that the bot object passed to the_daemon_file_saver is the same one used by the rest of the program
)
_the_daemon_file_saver.start()
# bot.load_extension("jishaku")

# slash = InteractionClient(client=bot, sync_commands=True)
# bot.slash = slash
# Add the commands
bot.add_cog(DebugCog(bot))
bot.add_cog(DeveloperCommands(bot))
bot.add_cog(ProblemsCog(bot))
bot.add_cog(QuizCog(bot))
bot.add_cog(MiscCommandsCog(bot))
bot.CONSTANTS = bot_constants
bot.add_check(checks.is_not_blacklisted())
bot.add_cog(InterestingComputationCog(bot))

# Events

# TODO: (general) add changelog.json
@bot.event
async def on_connect():
    """Run when the bot connects"""
    print("The bot has connected to Discord successfully.")
    await asyncio_sleep(0.5)
    await bot.change_presence(
        status=disnake.Status.idle,
    )
    bot.log.debug(
        "Deleting data from guilds the bot was kicked from while it was offline"
    )
    bot_guild_ids = [
        guild.id for guild in bot.guilds
    ]  # The guild_ids of the guilds that the bot is in
    for (
        guild_id
    ) in (
        await bot.cache.get_guilds()
    ):  # Obtain all guilds the cache stores data (will need to be upgraded.)
        if guild_id not in bot_guild_ids:  # It's not in!
            if guild_id is None:  # Don't delete global problems
                continue
            bot.log.debug("The bot is deleting data from a guild it has left.")
            await bot.cache.delete_all_by_guild_id(guild_id)  # Delete the data


@bot.event
async def on_error(event, *args, **kwargs):
    print(f"Error in {event}... uh oh", file=stderr)
    error = exc_info()
    # print the traceback to the file
    print(
        "\n".join(traceback.format_exception(*error)),
        file=stderr,
    )

    error_traceback_as_obj = "\n".join(traceback.format_exception(*error))
    # Log the error?
    log_error(error[1])
    # We don't have an interaction/context, so I can't tell the user that an error happened
    print("Oh no! An exception occurred!", flush=True, file=stdout)

    print(error_traceback_as_obj, flush=True, file=stdout)


@bot.event
async def on_slash_command_error(inter, error):
    """Function called when a slash command errors, which will inevitably happen. All the functionality was moved to base_on_error :-)"""
    # print the traceback to the file
    dict_args = await base_on_error(inter, error)
    try:
        return await inter.send(**dict_args)
    except AttributeError:
        log_error(error, f"error_logs/{str(datetime.datetime.now())}")
        await inter.send(
            "An error occured, and the error message couldn't be sent. However, it has been saved!"
        )
        raise error


# @bot.command(help = """Adds a trusted user!
# math_problems.add_trusted_user <user_id>
# adds the user's id to the trusted users list
# (can only be used by trusted users)""",
# brief = "Adds a trusted user")


@bot.event
async def on_guild_join(guild):
    """Ran when the bot joins a guild!"""
    if guild.id is None:  # Should never happen
        raise Exception("Uh oh!")  # This is probably causing the bot to do stuff
        # await guild.leave()  # This will mess up stuff
        # print("Oh no")
        # raise RuntimeError(
        #     "Oh no..... there is a guild with id None... this will mess up the bot!")
        #  # Make sure that a guild with id _global doesn't mess up stuff


@bot.event
async def on_guild_remove(guild):
    await bot.cache.remove_all_by_guild_id(guild.id)  # Remove all guild-related stuff
    # uh oh?


if __name__ == "__main__":
    print("The bot has finished setting up and will now run.")
    for command in bot.global_slash_commands:
        # raise
        if len(command.name) > 100:
            raise Exception(f"This command: {command.name} is too long!")
    if should_we_connect:
        bot.run(DISCORD_TOKEN)
