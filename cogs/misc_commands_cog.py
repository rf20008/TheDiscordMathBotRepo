import json
import typing
from asyncio import sleep as asyncio_sleep
from copy import copy
from io import BytesIO  # For file submitting!
from os import cpu_count
from sys import version, version_info
from time import asctime
from typing import Union

import psutil
from disnake import *
from disnake.ext import commands

from helpful_modules import checks, cooldowns, problems_module
from helpful_modules.custom_bot import TheDiscordMathProblemBot
from helpful_modules.custom_buttons import *
from helpful_modules.custom_embeds import SimpleEmbed
from helpful_modules.save_files import FileSaver
from helpful_modules.base_on_error import get_git_revision_hash

from .helper_cog import HelperCog

mb = lambda us: round(us / (1000000), ndigits=3)


class MiscCommandsCog(HelperCog):
    def __init__(self, bot: TheDiscordMathProblemBot):
        super().__init__(bot)
        checks.setup(bot)  # Sadly, Interactions do not have a bot parameter
        self.bot: TheDiscordMathProblemBot = bot
        self.cache: problems_module.MathProblemCache = bot.cache

    @commands.slash_command(
        name="info",
        description="Bot info!",
        options=[
            Option(
                name="include_extra_info",
                description="Whether to include extra, technical info",
                required=False,
                type=OptionType.boolean,
            )
        ],
    )
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def info(
        self,
        inter: disnake.ApplicationCommandInteraction,
        include_extra_info: bool = False,
    ):
        """/info [include_extra_info: bool = False]
        Show bot info. include_extra_info shows technical information!"""
        mem_usage = psutil.virtual_memory()
        used = mb(mem_usage.used / (1024 * 1024))
        total = mb(mem_usage.total)
        perc = mem_usage.percent
        avail = mb(mem_usage.available)
        embed = SimpleEmbed(title="Bot info", description="")
        embed = embed.add_field(
            name="Original Bot Developer", value="ay136416#2707", inline=False
        )  # Could be sufficient for attribution (except for stating changes).
        embed = embed.add_field(
            name="Github Repository Link", value=self.bot.constants.SOURCE_CODE_LINK
        )
        embed = embed.add_field(
            name="Latest Git Commit Hash",
            value=str(get_git_revision_hash()),
            inline=False,
        )
        embed = embed.add_field(
            name="Memory Usage",
            value=f"""Used/Available+Used Memory: {used}MB/{used+avail}MB 
            (percentage: {round(100*used/(used+avail), ndigits=3)}%) (perc reported: {perc}) Total memory available: {total}MB""",
            inline=False,
        )
        embed = embed.add_field(
            name="Current Latency to Discord",
            value=f"{round(self.bot.latency * 10000) / 10}ms",
            inline=False,
        )
        current_version_info = version_info
        print(current_version_info)
        python_version_as_str = f"Python {current_version_info.major}.{current_version_info.minor}.{current_version_info.micro}{current_version_info.releaselevel}"

        embed = embed.add_field(
            name="Python version", value=python_version_as_str, inline=False
        )  # uh oh
        if include_extra_info:
            embed = embed.add_field(
                name="Python version given by sys.version", value=str(version)
            )
            # embed = embed.add_field(
            #    name="Nextcord version", value=str(disnake.__version__)
            # )
            embed = embed.add_field(
                name="Disnake version", value=str(disnake.__version__)
            )

            embed = embed.add_field(
                name="CPU count (which may not necessarily be the amount of CPU available to the bot due to a Python limitation)",
                value=str(cpu_count()),
            )
            embed = embed.add_field(
                name="License",
                value="""This bot is licensed under GPLv3. 
                Please see [the official GPLv3 website that explains the GPLv3](https://www.gnu.org/licenses/gpl-3.0.en.html) for more details.
                Note that there are previous licenses, including the CC-BY-SA 4.0 and the MIT license; I believe these are superseded by the GPL license but I'm not sure.""",
            )
            embed = embed.add_field(
                name="Uptime",
                value=f"The bot started at {disnake.utils.format_dt(self.bot.timeStarted)} and has been up for {round(self.bot.uptime)} seconds.",
            )

        await inter.send(embed=embed)

    @commands.slash_command(
        name="list_trusted_users", description="list all trusted users"
    )
    @commands.cooldown(1, 5, commands.BucketType.user)  # 5 second user cooldown
    @commands.cooldown(
        20, 50, commands.BucketType.default
    )  # 20 times before a global cooldown of 50 seconds is established
    @commands.guild_only()  # Due to bugs, it doesn't work in DM's
    async def list_trusted_users(self, inter):
        """/list_trusted_users
        List all trusted users in username#discriminator format (takes no arguments)"""
        # await inter.send(type=5)  # Defer
        # Deferring might be unnecessary & and cause errors
        # We might not be able to respond in time because of the 100ms delay between user fetching
        # This is to respect the API rate limit.

        # We don't need a try/except
        result = await self.cache.run_sql("SELECT * FROM user_data")
        trusted_users = []
        for item in result:
            if item["trusted"]:
                trusted_users.append(item["user_id"])
        if len(trusted_users) == 0:
            await inter.send("There are no trusted users.")
            return
            # raise Exception("There are no trusted users!")

        __trusted_users = ""

        for user_id in trusted_users:
            try:
                user = await self.bot.fetch_user(user_id)
                __trusted_users += f"""{user.name}
            """
            except (disnake.NotFound, disnake.NotFound):
                # A user with this ID does not exist
                self.bot.trusted_users.remove(user_id)  # delete the user!
                try:
                    f = FileSaver(name=4, enabled=True)
                    f.save_files(
                        self.bot.cache,
                        vote_threshold=self.bot.vote_threshold,
                        trusted_users_list=self.bot.trusted_users,
                    )
                    try:
                        del f
                    except NameError:
                        pass
                except BaseException as e:
                    raise RuntimeError(
                        "Could not save the files after removing the trusted user with ID that does not exist!"
                    ) from e
            except (
                disnake.Forbidden,
                disnake.Forbidden,
            ) as exc:  # Cannot fetch this user!
                raise RuntimeError("Cannot fetch users") from exc
            else:
                await asyncio_sleep(
                    0.1
                )  # 100 ms between fetching to respect the rate limit (and to prevent spam)

        await inter.send(__trusted_users, ephemeral=True)

    @commands.cooldown(1, 30, commands.BucketType.user)
    @commands.slash_command(
        name="ping", description="Prints latency and takes no arguments"
    )
    async def ping(self, inter: disnake.ApplicationCommandInteraction):
        """Ping the bot which returns its latency! This command does not take any arguments."""
        # TODO: round-trip latency, etc
        await inter.send(
            embed=SuccessEmbed(
                f"Pong! My latency is {round(self.bot.latency * 1000)}ms."
            ),
            ephemeral=True,
        )

    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.slash_command(
        name="what_is_vote_threshold",
        description="Prints the vote threshold and takes no arguments",
    )
    async def what_is_vote_threshold(
        self, inter: disnake.ApplicationCommandInteraction
    ):
        """/what_is_vote_threshold
        Returns the vote threshold. Takes no arguments. There is a 5-second cooldown on this command.
        """
        await inter.send(
            embed=SuccessEmbed(f"The vote threshold is {self.bot.vote_threshold}."),
            ephemeral=True,
        )

    @commands.slash_command(
        name="generate_invite_link",
        description="Generates a invite link for this bot! Takes no arguments",
    )
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def generate_invite_link(self, inter: disnake.ApplicationCommandInteraction):
        """/generate_invite_link
        Generate an invite link for the bot. Takes no arguments"""
        await inter.send(
            embed=SuccessEmbed(
                disnake.utils.oauth_url(
                    client_id=self.bot.application_id,
                    permissions=disnake.Permissions(
                        send_messages=True,
                        read_messages=True,
                        embed_links=True,
                        use_slash_commands=True,
                        attach_files=True,
                    ),
                    scopes=["bot", "applications.commands"],
                )
            ),
            ephemeral=True,
        )

    @commands.slash_command(
        name="github_repo", description="Returns the link to the github repo"
    )
    @commands.cooldown(2, 120, commands.BucketType.user)
    async def github_repo(self, inter: disnake.ApplicationCommandInteraction):
        """/github_repo
        Gives you the link to the bot's GitHub repo.
        If you are modifying this, because of the GPLv3 license, you must change this to reflect the new location of the bot's source code.
        There is a 2-minute cooldown on this command (after it has been executed 2 times)
        """
        await inter.send(
            embed=SuccessEmbed(
                f"[Repo Link:]({self.bot.constants.SOURCE_CODE_LINK})",
                successTitle="Here is the Github Repository Link.",
            )
        )

    @commands.slash_command(
        name="set_vote_threshold",
        description="Sets the vote threshold",
        options=[
            Option(
                name="threshold",
                description="the threshold you want to change it to",
                type=OptionType.integer,
                required=True,
            )
        ],
    )
    @checks.trusted_users_only()
    @commands.cooldown(
        1, 50, commands.BucketType.user
    )  # Don't overload the bot (although trusted users will probably not)
    @commands.cooldown(
        15, 500, commands.BucketType.default
    )  # To prevent wars! If you want your own version, self host it :-)
    async def set_vote_threshold(
        self, inter: disnake.ApplicationCommandInteraction, threshold: int
    ):
        """/set_vote_threshold [threshold: int]
        Set the vote threshold. Only trusted users may do this.
        There is a 50-second cooldown.
        This might cause a race condition"""
        # try:
        #    threshold = int(threshold)
        # except TypeError:  # Conversion failed!
        #    await inter.send(
        #        embed=ErrorEmbed(
        #            "Invalid threshold argument! (threshold must be an integer)"
        #        ),
        #        ephemeral=True,
        #    )
        #    return
        # Unnecessary because the type is an integer
        if threshold < 1:  # Threshold must be greater than 1!
            await inter.send(
                embed=ErrorEmbed("You can't set the threshold to smaller than 1."),
                ephemeral=True,
            )
            return
        vote_threshold = int(threshold)  # Probably unnecessary
        for problem in await self.bot.cache.get_global_problems():
            if (
                problem.get_num_voters() >= vote_threshold
            ):  # Delete the problem if the number of votes the problem has is above the new threshold.
                await self.cache.remove_problem(problem.id)
        await inter.send(
            embed=SuccessEmbed(
                f"The vote threshold has successfully been changed to {threshold}!"
            ),
            ephemeral=True,
        )
        return



    @commands.slash_command(
        name="submit_a_request",
        description="Submit a request. I will know!",
        options=[
            Option(
                name="offending_problem_guild_id",
                description="The guild id of the problem you are trying to remove. The guild id of a global problem is null",
                type=OptionType.integer,
                required=False,
            ),
            Option(
                name="offending_problem_id",
                description="The problem id of the problem. Very important (so I know which problem to check)",
                type=OptionType.integer,
                required=False,
            ),
            Option(
                name="extra_info",
                description="A up to 5000 character description (about 2 pages) Use this wisely!",
                type=OptionType.string,
                required=False,
            ),
            Option(
                name="copyrighted_thing",
                description="The copyrighted thing that this problem is violating",
                type=OptionType.string,
                required=False,
            ),
            Option(
                name="type",
                description="Request type",
                required=False,
                type=OptionType.string,
            ),
        ],
    )
    async def submit_a_request(
        self,
        inter: disnake.ApplicationCommandInteraction,
        offending_problem_guild_id: int = None,
        offending_problem_id: int = None,
        extra_info: str = None,
        copyrighted_thing: str = Exception,
        type: str = "",
    ):
        """/submit_a_request [offending_problem_guild_id: int = None] [offending_problem_id: int = None]

        Submit a request! I will know! It uses a channel in my discord server and posts an embed.
        I will probably deprecate this and replace it with emailing me.
        Therefore, this command has been deprecated and will be removed in a future version of the bot!
        """
        if (
            extra_info is None
            and type == ""
            and copyrighted_thing is not Exception
            and offending_problem_guild_id is None
            and offending_problem_id is None
        ):
            await inter.send(embed=ErrorEmbed("You must specify some field."))
        if extra_info is None:
            await inter.send(embed=ErrorEmbed("Please provide extra information!"))
        assert len(extra_info) <= 5000
        try:
            channel = await self.bot.fetch_channel(
                901464948604039209
            )  # CHANGE THIS IF YOU HAVE A DIFFERENT REQUESTS CHANNEL! (the part after id)\
            # TODO: make this an env var
        except (disnake.ext.commands.ChannelNotReadable, disnake.Forbidden):
            raise RuntimeError("The bot cannot send messages to the channel!")
        try:
            Problem = await self.bot.cache.get_problem(
                offending_problem_guild_id, offending_problem_id
            )
            problem_found = True
        except (TypeError, KeyError, problems_module.ProblemNotFound):
            # Problem not found
            problem_found = False
        embed = disnake.Embed(
            title=f"A new {type} request has been received from {inter.author.name}#{inter.author.discriminator}!",
            description="",
        )

        if problem_found:
            embed.description = f"Problem_info:{str(Problem)}"  # type: ignore
        embed.description += f"""Copyrighted thing: (if legal): {copyrighted_thing}
        Extra info: {extra_info}"""
        if problem_found:
            embed.set_footer(text=str(Problem) + asctime())
        else:
            embed.set_footer(text=str(asctime()))

        content = "A request has been submitted."
        for (
            owner_id
        ) in (
            self.bot.owner_ids
        ):  # Mentioning owners: may be removed (you can also remove it as well)
            content += f"<@{owner_id}>"
        content += f"<@{self.bot.owner_id}>"
        await channel.send(embed=embed, content=content)
        await inter.send("Your request has been submitted!")

    @commands.slash_command(
        name="blacklist",
        description="Blacklist someone from the bot!",
        options=[
            Option(
                name="user",
                description="The user to blacklist",
                type=OptionType.user,
                required=True,
            )
        ],
    )
    @checks.trusted_users_only()
    @checks.is_not_blacklisted()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def blacklist(
        self: "MiscCommandsCog",
        inter: disnake.ApplicationCommandInteraction,
        user: typing.Union[disnake.User, disnake.Member],
    ):
        """/blacklist [user: user]
        Blacklist someone from the bot. You must be a trusted user to do this!
        There is a 1-second cooldown."""
        user_data = await self.cache.get_user_data(
            user_id=user.id,
            default=problems_module.UserData(
                user_id=user.id, trusted=False, blacklisted=False
            ),
        )
        if user_data.blacklisted:
            self.bot.log.debug("Can't blacklist user; user already blacklisted")
            return await inter.send("Can't blacklist user; user already blacklisted")
        else:
            user_data.blacklisted = True
            await self.cache.set_user_data(user_id=user.id, new=user_data)

            self.bot.log.info(f"Successfully blacklisted the user with id {user.id}")
            await inter.send("Successfully blacklisted the user!")

            # TODO: what do I do after a user gets blacklisted? Do I delete their data?

    @commands.slash_command(
        name="unblacklist",
        description="Remove someone's blacklist",
        options=[
            Option(
                name="user",
                description="The user to un-blacklist",
                type=OptionType.user,
                required=True,
            )
        ],
    )
    @checks.trusted_users_only()
    @checks.is_not_blacklisted()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def unblacklist(
        self: "MiscCommandsCog",
        inter: disnake.ApplicationCommandInteraction,
        user: typing.Union[disnake.User, disnake.Member],
    ):
        """/unblacklist [user: user]
        Remove a user's bot blacklist. You must be a trusted user to do this!
        There is a 1-second cooldown."""
        user_data = await self.cache.get_user_data(
            user_id=user.id,
            default=problems_module.UserData(
                user_id=user.id, trusted=False, blacklisted=False
            ),
        )
        if not user_data.blacklisted:
            self.bot.log.debug("Can't un-blacklist user; user not blacklisted")
            return await inter.send("Can't un-blacklist user; user not blacklisted")
        else:
            user_data.blacklisted = False
            await self.cache.set_user_data(user_id=user.id, new=user_data)
            self.bot.log.info(f"Successfully un-blacklisted the user with id {user.id}")
            await inter.send("Successfully un-blacklisted the user!")

            # TODO: what do I do after a user gets blacklisted? Do I delete their data?

    @commands.slash_command(
        name="guild_blacklist",
        description="Blacklist a guild from this bot",
        options=[
            Option(
                name="guild_id",
                description="The ID of the guild to blacklist",
                type=OptionType.string,
                required=True
            )
        ]
    )
    @checks.trusted_users_only()
    @checks.is_not_blacklisted()
    async def guild_blacklist(self, inter: disnake.ApplicationCommandInteraction, guild_id: str):
        """
        /guild_blacklist [guild_id: int]
        Blacklist a guild from TheDiscordMathProblemBot. Only trusted users can run this command.
        Also, reasons are not shared.
        """

        # Check if the user is blacklisted from using this command
        if await self.bot.is_user_blacklisted(inter.author):
            await inter.send(embed=SimpleEmbed(
                title="Insufficient permissions",
                description="You cannot add guilds to the denylist without proper permissions.",
                color=disnake.Color.red()
            ))
            return

        # Check if the user is trusted to perform this action
        if not await self.bot.is_trusted(inter.author):
            await inter.send(embed=SimpleEmbed(
                title="Insufficient permissions",
                description="You cannot add guilds to the denylist without proper permissions.",
                color=disnake.Color.red()
            ))
            return
        try:
            guild_id = int(guild_id)
        except ValueError:
            await inter.send(embed=ErrorEmbed("The guild ID you provided isn't actually an integer"))
        # Fetch current data of the guild
        old_data = await self.bot.cache.get_guild_data(guild_id=guild_id)

        # Check if the guild is already blacklisted
        if old_data.blacklisted:
            await inter.send(embed=ErrorEmbed("The guild you're trying to denylist is already on the denylist"))
            return

        # Perform the blacklist operation
        old_data.blacklisted = True

        # Update the guild's data in storage or cache
        await self.bot.cache.set_guild_data(new=old_data)

        # Notify the user that the guild has been successfully blacklisted
        await inter.send(
            embed=SuccessEmbed(f"The guild with ID {guild_id} has successfully been added to the denylist"))

        # Notify the bot's owner or admins about the action
        just_denylisted_guild = self.bot.get_guild(guild_id)
        if just_denylisted_guild is not None:
            await self.bot.notify_guild_on_guild_leave_because_guild_blacklist(just_denylisted_guild)

    @commands.slash_command(
        name="guild_unblacklist",
        description="Remove a guild from this bot's blacklist",
        options=[
            Option(
                name="guild_id",
                description="The ID of the guild to un-blacklist",
                type=OptionType.string,
                required=True
            )
        ]
    )
    @checks.trusted_users_only()
    @checks.is_not_blacklisted()
    async def guild_unblacklist(self, inter: disnake.ApplicationCommandInteraction, guild_id: str):
        """
        /guild_unblacklist [guild_id: int]
        Remove a guild from the blacklist of this bot. Only trusted users can run this command.
        """
        # Check if the user is blacklisted from using this command
        if await self.bot.is_user_blacklisted(inter.author):
            await inter.send(embed=SimpleEmbed(
                title="Insufficient permissions",
                description="You cannot remove guilds from the denylist without proper permissions.",
                color=disnake.Color.red()
            ))
            return

        # Check if the user is trusted to perform this action
        if not await self.bot.is_trusted(inter.author):
            await inter.send(embed=SimpleEmbed(
                title="Insufficient permissions",
                description="You cannot remove guilds from the denylist without proper permissions.",
                color=disnake.Color.red()
            ))
            return
        try:
            guild_id = int(guild_id)
        except ValueError:
            await inter.send(embed=ErrorEmbed("The guild ID you provided isn't actually an integer"))
        # Fetch current data of the guild
        old_data = await self.bot.cache.get_guild_data(guild_id=guild_id)

        # Check if the guild is not already blacklisted
        if not old_data.blacklisted:
            await inter.send(
                embed=ErrorEmbed("The guild you're trying to remove from the denylist is not on the denylist!"))
            return

        # Perform the unblacklist operation
        old_data.blacklisted = False

        # Update the guild's data in storage or cache
        await self.bot.cache.set_guild_data(new=old_data)

        # Notify the user that the guild has been successfully unblacklisted
        await inter.send(
            embed=SuccessEmbed(f"The guild with ID {guild_id} has successfully been removed from the denylist"))
