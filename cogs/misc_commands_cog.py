<<<<<<< HEAD
from dislash import *
import nextcord
import dislash
=======
from disnake import *
from disnake.ext import commands
import disnake
>>>>>>> disnake
from .helper_cog import HelperCog
from sys import version_info, version
from os import cpu_count
from helpful_modules import cooldowns
<<<<<<< HEAD
from nextcord.ext import commands
=======
>>>>>>> disnake
from helpful_modules import checks
from helpful_modules.custom_embeds import SimpleEmbed, ErrorEmbed, SuccessEmbed
from helpful_modules.save_files import FileSaver
from helpful_modules import problems_module
from helpful_modules.custom_buttons import *
from helpful_modules.threads_or_useful_funcs import get_git_revision_hash
from asyncio import sleep as asyncio_sleep
from time import asctime
import resource
from typing import Union
from copy import copy
import orjson
from io import BytesIO  # For file submitting!


class MiscCommandsCog(HelperCog):
    def __init__(self, bot: commands.Bot):
        super().__init__(bot)
        checks.setup(bot)  # Sadly, Interactions do not have a bot parameter
        self.bot: commands.Bot = bot
        self.cache: problems_module.MathProblemCache = bot.cache

<<<<<<< HEAD
    @slash_command(
=======
    @commands.slash_command(
>>>>>>> disnake
        name="info",
        description="Bot info!",
        options=[
            Option(
                name="include_extra_info",
                description="Whether to include extra, technical info",
                required=False,
<<<<<<< HEAD
                type=OptionType.BOOLEAN,
            )
        ],
    )
    @dislash.cooldown(1, 150, commands.BucketType.user)
    async def info(self, inter: SlashInteraction, include_extra_info: bool = False):
=======
                type=OptionType.boolean,
            )
        ],
    )
    @commands.cooldown(1, 150, commands.BucketType.user)
    async def info(
        self,
        inter: disnake.ApplicationCommandInteraction,
        include_extra_info: bool = False,
    ):
>>>>>>> disnake
        """/info [include_extra_info: bool = False]
        Show bot info. include_extra_info shows technical information!"""
        embed = SimpleEmbed(title="Bot info", description="")
        embed = embed.add_field(
            name="Original Bot Developer", value="ay136416#2707", inline=False
        )  # Could be sufficient for attribution (except for stating changes).
        embed = embed.add_field(
<<<<<<< HEAD
            name="Github Repository Link",
            value=self.bot.constants.SOURCE_CODE_LINK
=======
            name="Github Repository Link", value=self.bot.constants.SOURCE_CODE_LINK
>>>>>>> disnake
        )
        embed = embed.add_field(
            name="Latest Git Commit Hash",
            value=str(get_git_revision_hash()),
            inline=False,
        )
        embed = embed.add_field(
            name="Current Latency to Discord",
            value=f"{round(self.bot.latency*10000)/10}ms",
            inline=False,
        )
        current_version_info = version_info
        python_version_as_str = f"Python {current_version_info.major}.{current_version_info.minor}.{current_version_info.micro}{current_version_info.releaselevel}"

        embed = embed.add_field(
            name="Python version", value=python_version_as_str, inline=False
        )
        if include_extra_info:
            embed = embed.add_field(
                name="Python version given by sys.version", value=str(version)
            )

            embed = embed.add_field(
                name="Nextcord version", value=str(nextcord.__version__)
            )
<<<<<<< HEAD
=======
            embed = embed.add_field(
                name="Disnake version", value=str(disnake.__version__)
            )
>>>>>>> disnake

            memory_limit = resource.getrlimit(resource.RUSAGE_SELF)[0]
            current_usage = resource.getrusage(resource.RUSAGE_SELF)

            embed = embed.add_field(
                name="Memory Usage",
                value=f"{round((current_usage[3]/memory_limit)*1000)/100}%",
            )
            embed = embed.add_field(
                name="CPU count (which may not necessarily be the amount of CPU avaliable to the bot due to a Python limitation)",
                value=str(cpu_count()),
            )
            embed = embed.add_field(
<<<<<<< HEAD
                name="License", value="This bot is licensed under GPLv3"
            )
        await inter.reply(embed=embed)

    @slash_command(name="list_trusted_users", description="list all trusted users")
=======
                name="License",
                value="This bot is licensed under GPLv3. Please see [the official GPLv3 website](https://www.gnu.org/licenses/gpl-3.0.en.html) for more details.",
            )

        await inter.send(embed=embed)

    @commands.slash_command(
        name="list_trusted_users", description="list all trusted users"
    )
>>>>>>> disnake
    @commands.cooldown(1, 5, commands.BucketType.user)  # 5 second user cooldown
    @commands.cooldown(
        20, 50, commands.BucketType.default
    )  # 20 times before a global cooldown of 50 seconds is established
    @commands.guild_only()  # Due to bugs, it doesn't work in DM's
    async def list_trusted_users(self, inter):
<<<<<<< HEAD
        "List all trusted users in username#discriminator format (takes no arguments)"
        # await inter.reply(type=5)  # Defer
=======
        """/list_trusted_users
        List all trusted users in username#discriminator format (takes no arguments)"""
        # await inter.send(type=5)  # Defer
>>>>>>> disnake
        # Deferring might be unnecessary & and cause errors
        # We might not be able to respond in time because of the 100ms delay between user fetching
        # This is to respect the API rate limit.
        if len(self.bot.trusted_users) == 0:
<<<<<<< HEAD
            await inter.reply("There are no trusted users.")
=======
            await inter.send("There are no trusted users.")
>>>>>>> disnake
            return
            # raise Exception("There are no trusted users!")

        __trusted_users = ""

        for user_id in self.bot.trusted_users:
            try:
                user = await self.bot.fetch_user(user_id)
                __trusted_users += f"""{user.name}#{user.discriminator}
            """
<<<<<<< HEAD
            except nextcord.NotFound:
=======
            except (nextcord.NotFound, disnake.NotFound):
>>>>>>> disnake
                # A user with this ID does not exist
                self.bot.trusted_users.remove(user_id)  # delete the user!
                try:
                    f = FileSaver(name=4, enabled=True)
                    f.save_files(
                        self.bot.cache,
                        vote_threshold=self.bot.vote_threshold,
                        trusted_users_list=self.bot.trusted_users,
                    )
                    f.goodbye()  # This should delete it
                    try:
                        del f
                    except NameError:
                        pass
                except BaseException as e:
                    raise RuntimeError(
                        "Could not save the files after removing the trusted user with ID that does not exist!"
                    ) from e
<<<<<<< HEAD
            except nextcord.Forbidden as exc:  # Cannot fetch this user!
=======
            except (
                nextcord.Forbidden,
                disnake.Forbidden,
            ) as exc:  # Cannot fetch this user!
>>>>>>> disnake
                raise RuntimeError("Cannot fetch users") from exc
            else:
                await asyncio_sleep(
                    0.1
                )  # 100 ms between fetching to respect the rate limit (and to prevent spam)

<<<<<<< HEAD
        await inter.reply(__trusted_users, ephemeral=True)

    @slash_command(name="ping", description="Prints latency and takes no arguments")
    async def ping(self, inter):
        "Ping the bot which returns its latency!"
        await cooldowns.check_for_cooldown(inter, "ping", 5)
        await inter.reply(
=======
        await inter.send(__trusted_users, ephemeral=True)

    @commands.slash_command(
        name="ping", description="Prints latency and takes no arguments"
    )
    async def ping(self, inter: disnake.ApplicationCommandInteraction):
        "Ping the bot which returns its latency! This command does not take any arguments."
        await cooldowns.check_for_cooldown(inter, "ping", 5)
        await inter.send(
>>>>>>> disnake
            embed=SuccessEmbed(
                f"Pong! My latency is {round(self.bot.latency*1000)}ms."
            ),
            ephemeral=True,
        )

<<<<<<< HEAD
    @slash_command(
        name="what_is_vote_threshold",
        description="Prints the vote threshold and takes no arguments",
    )
    async def what_is_vote_threshold(self, inter: SlashInteraction):
        "Returns the vote threshold"
        await cooldowns.check_for_cooldown(inter, "what_is_vote_threshold", 5)
        await inter.reply(
=======
    @commands.slash_command(
        name="what_is_vote_threshold",
        description="Prints the vote threshold and takes no arguments",
    )
    async def what_is_vote_threshold(
        self, inter: disnake.ApplicationCommandInteraction
    ):
        "Returns the vote threshold"
        await cooldowns.check_for_cooldown(inter, "what_is_vote_threshold", 5)
        await inter.send(
>>>>>>> disnake
            embed=SuccessEmbed(f"The vote threshold is {self.bot.vote_threshold}."),
            ephemeral=True,
        )

<<<<<<< HEAD
    @slash_command(
        name="generate_invite_link",
        description="Generates a invite link for this bot! Takes no arguments",
    )
    @dislash.cooldown(1,5,nextcord.ext.commands.BucketType.user)
    async def generate_invite_link(self, inter):
        "Generate an invite link for the bot. This command has been deprecated."
        await cooldowns.check_for_cooldown(inter, "generateInviteLink", 5)
        await inter.reply(
            embed=SuccessEmbed(
                self.bot.constants.SOURCE_CODE_LINK+"\n (This command has been deprecated)"
=======
    @commands.slash_command(
        name="generate_invite_link",
        description="Generates a invite link for this bot! Takes no arguments",
    )
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def generate_invite_link(self, inter: disnake.ApplicationCommandInteraction):
        "Generate an invite link for the bot. This command has been deprecated."
        await cooldowns.check_for_cooldown(inter, "generateInviteLink", 5)
        await inter.send(
            embed=SuccessEmbed(
                self.bot.constants.SOURCE_CODE_LINK
                + "\n (This command has been deprecated)"
>>>>>>> disnake
            ),
            ephemeral=True,
        )

<<<<<<< HEAD
    @slash_command(
        name="github_repo", description="Returns the link to the github repo"
    )
    @commands.cooldown(2, 120, commands.BucketType.user)
    async def github_repo(self, inter):
        """/github_repo
        Gives you the link to the bot's github repo.
        If you are modifying this, because of the GPLv3 license, you must change this to reflect the new location of the bot's source code.
        """
        await inter.reply(
=======
    @commands.slash_command(
        name="github_repo", description="Returns the link to the github repo"
    )
    @commands.cooldown(2, 120, commands.BucketType.user)
    async def github_repo(self, inter: disnake.ApplicationCommandInteraction):
        """/github_repo
        Gives you the link to the bot's github repo.
        If you are modifying this, because of the GPLv3 license, you must change this to reflect the new location of the bot's source code.
        There is a 120 second cooldown on this command (after it has been executed 2 times)
        """
        await inter.send(
>>>>>>> disnake
            embed=SuccessEmbed(
                f"[Repo Link:]{self.bot.constants.GITHUB_REPO_LINK}",
                successTitle="Here is the Github Repository Link.",
            )
        )

<<<<<<< HEAD
    @slash_command(
=======
    @commands.slash_command(
>>>>>>> disnake
        name="set_vote_threshold",
        description="Sets the vote threshold",
        options=[
            Option(
                name="threshold",
                description="the threshold you want to change it to",
<<<<<<< HEAD
                type=OptionType.INTEGER,
=======
                type=OptionType.integer,
>>>>>>> disnake
                required=True,
            )
        ],
    )
    @checks.trusted_users_only()
    @commands.cooldown(
<<<<<<< HEAD
        1, 50, BucketType.user
    )  # Don't overload the bot (although trusted users will probably not)
    @commands.cooldown(
        15, 500, BucketType.default
    )  # To prevent wars! If you want your own version, self host it :-)
    async def set_vote_threshold(self, inter: dislash.SlashInteraction, threshold: int):
        """/set_vote_threshold [threshold: int]
        Set the vote threshold. Only trusted users may do this."""
        # try:
        #    threshold = int(threshold)
        # except TypeError:  # Conversion failed!
        #    await inter.reply(
=======
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
        There is a 50 second cooldown.
        This might cause a race condition"""
        # try:
        #    threshold = int(threshold)
        # except TypeError:  # Conversion failed!
        #    await inter.send(
>>>>>>> disnake
        #        embed=ErrorEmbed(
        #            "Invalid threshold argument! (threshold must be an integer)"
        #        ),
        #        ephemeral=True,
        #    )
        #    return
<<<<<<< HEAD
        # Unnecessary because the type
        if threshold < 1:  # Threshold must be greater than 1!
            await inter.reply(
=======
        # Unnecessary because the type is an integer
        if threshold < 1:  # Threshold must be greater than 1!
            await inter.send(
>>>>>>> disnake
                embed=ErrorEmbed("You can't set the threshold to smaller than 1."),
                ephemeral=True,
            )
            return
<<<<<<< HEAD
        vote_threshold = int(threshold)
        for problem in await self.bot.cache.get_global_problems():
            if problem.get_num_voters() > vote_threshold:
                await self.cache.remove_problem(problem.guild_id, problem.id)
        await inter.reply(
=======
        try:
            vote_threshold = int(threshold)  # Probably unnecessary
        except:
            raise
        for problem in await self.bot.cache.get_global_problems():
            if problem.get_num_voters() > vote_threshold:
                await self.cache.remove_problem(problem.guild_id, problem.id)
        await inter.send(
>>>>>>> disnake
            embed=SuccessEmbed(
                f"The vote threshold has successfully been changed to {threshold}!"
            ),
            ephemeral=True,
        )
        return

<<<<<<< HEAD
    @slash_command(description="Interact with your user data")
    async def user_data(self: "MiscCommandsCog", inter: dislash.SlashInteraction):
        "The base command to interact with your user data. This doesn't do anything (you need to call a subcommand"
        pass

    @nextcord.ext.commands.cooldown(
        1, 500, nextcord.ext.commands.BucketType.user
=======
    @commands.slash_command(
        name="user_data", description="Interact with your user data"
        )
    async def user_data(
        self, inter: disnake.ApplicationCommandInteraction
    ):
        "The base command to interact with your user data. This doesn't do anything (you need to call a subcommand)"
        print('user_data command invoked!')

    @commands.cooldown(
        1, 500, commands.BucketType.user
>>>>>>> disnake
    )  # To prevent abuse
    @user_data.sub_command(
        name="delete_all",
        description="Delete all problems, quizzes, and quiz submissions you created!",
        options=[
            Option(
                name="save_data_before_deletion",
                description="Whether to give you your problems or submissions, in JSON format! Defaults to True",
<<<<<<< HEAD
                type=OptionType.BOOLEAN,
=======
                type=OptionType.boolean,
>>>>>>> disnake
                required=False,
            ),
            Option(
                name="delete_votes",
                description="Whether to delete your votes. ",
<<<<<<< HEAD
                type=OptionType.BOOLEAN,
=======
                type=OptionType.boolean,
>>>>>>> disnake
                required=False,
            ),
            Option(
                name="delete_solves",
                description="Whether to erase whether you have solved a problem or not",
<<<<<<< HEAD
                type=OptionType.BOOLEAN,
=======
                type=OptionType.boolean,
>>>>>>> disnake
                required=False,
            ),
        ],
    )
    async def delete_all(
        self: "MiscCommandsCog",
<<<<<<< HEAD
        inter: dislash.SlashInteraction,
=======
        inter: disnake.ApplicationCommandInteraction,
>>>>>>> disnake
        save_data_before_deletion: bool = True,
        delete_votes=False,
        delete_solves=False,
    ):
        """/user_data delete_all [save_data_before_deletion: bool = True] [delete_votes: bool = False] [delete_solves: bool = False]
        Delete all your data. YOU MUST CONFIRM THIS!
        If save_data_before_deletion, the data about you will be sent as a json file
        This has a 500 second cooldown."""
        if save_data_before_deletion:
            json_data: dict = await self._get_json_data_by_user(
                inter.author
            )  # Get the data
            file_version = self._file_version_of_item(
                str(json_data), file_name="your_data.json"
            )  # Turn it into a dictionary

        async def confirm_callback(
            self: ConfirmationButton,
            interaction: nextcord.Interaction,
            _extra_data: dict,
        ):
            "The function that runs when the button gets pressed. This actually deletes the data"
            assert self.check(interaction)
            kwargs = {
                "content": "Successfully deleted your data! Your data should now be cleared now."
            }
            if "file" in _extra_data.keys():
                # Return the file
                kwargs["file"] = _extra_data["file"]

            await _extra_data["cache"].delete_all_by_user_id(interaction.user.id)
            if _extra_data["delete_votes"]:
                problems_to_remove_votes_for = await _extra_data[
                    "cache"
                ].get_problems_by_func(
                    func=lambda problem, user_id: user_id in problem.voters,
                    args=[interaction.user.id],
                )
                for problem in problems_to_remove_votes_for:
                    problem.voters.remove(interaction.user.id)
                    await problem.update_self()
            if _extra_data["delete_solves"]:
                problems_to_remove_solves_for = await _extra_data[
                    "cache"
                ].get_problems_by_func(
                    func=lambda problem, user_id: user_id in problem.solvers,
                    args=[interaction.user.id],
                )
                for problem in problems_to_remove_solves_for:
                    problem.solvers.remove(interaction.user.id)
                    await problem.update_self()

            await interaction.responder.send_message(**kwargs)
            self.disable()
            self.view.stop()
            return

<<<<<<< HEAD
        async def deny_callback(self: BasicButton, interaction: nextcord.Interaction):
=======
        async def deny_callback(self: BasicButton, interaction: disnake.Interaction):
>>>>>>> disnake
            "A function that runs when the"
            await interaction.response.reply(
                "Your data is safe! It has not been deleted."
            )
            self.disable()
            self.view.stop()
            return

        _extra_data = {
            "cache": copy(self.bot.cache),
            "delete_votes": delete_votes,
            "delete_solves": delete_solves,
        }
        if save_data_before_deletion:
            _extra_data["file"] = file_version
        confirmation_button = ConfirmationButton(
            callback=confirm_callback,
            style=nextcord.ButtonStyle.danger,
            label="I'm 100\% \sure I want to delete my data!",
            disabled=False,
            _extra_data=_extra_data,
        )
        deny_button = BasicButton(
            check=lambda self, inter: inter.user.id == self.user_for,
            callback=deny_callback,
            style=nextcord.ButtonStyle.green,
            disabled=False,
            label="Never mind....",
        )
        view = MyView(timeout=30)
        view.add_item(confirmation_button)
        view.add_item(deny_button)
<<<<<<< HEAD
        return await inter.reply(
=======
        return await inter.send(
>>>>>>> disnake
            embed=SimpleEmbed(
                title="Are you sure?", description="This will delete all your data!"
            ),
            view=view,
        )

    async def _get_json_data_by_user(
<<<<<<< HEAD
        self, author: Union[nextcord.User, nextcord.Member]
=======
        self, author: Union[disnake.User, disnake.Member]
>>>>>>> disnake
    ) -> dict:
        "A helper function to obtain a user's stored data and return the dictionarified version of it."
        raw_data = await self.cache.get_all_by_author_id(author.id)
        problems_user_voted_for = await self.cache.get_problems_by_func(
            func=lambda problem, user_id: user_id in problem.voters, args=(author,)
        )
        print(problems_user_voted_for)
        problems_user_solved = await self.cache.get_problems_by_func(
            func=lambda problem, user_id: user_id in problem.solvers, args=(author,)
        )
        new_data = {
            "Problems": [problem.to_dict() for problem in raw_data["problems"]],
            "Quiz Problems": [
                quiz_problem.to_dict() for quiz_problem in raw_data["quiz_problems"]
            ],
            "Quiz Submissions": [
                submission.to_dict() for submission in raw_data["quiz_submissions"]
            ],
            "Problems the user voted for": [
                problem.to_dict(show_answers=False)
                for problem in problems_user_voted_for
            ],
            "Problems the user solved": [
                problem.to_dict() for problem in problems_user_solved
            ],
        }
        return new_data

<<<<<<< HEAD
    def _file_version_of_item(self, item: str, file_name) -> nextcord.File:
        assert isinstance(item, str)
        return nextcord.File(BytesIO(bytes(item, "utf-8")), filename=file_name)
    @nextcord.ext.commands.cooldown(1, 100, nextcord.ext.commands.BucketType.user)
=======
    def _file_version_of_item(self, item: str, file_name) -> disnake.File:
        assert isinstance(item, str)
        return disnake.File(BytesIO(bytes(item, "utf-8")), filename=file_name)

    @commands.cooldown(1, 100, commands.BucketType.user)
>>>>>>> disnake
    @user_data.sub_command(
        name="get_data",
        description="Get a jsonified version of the data stored with this application!",
    )
    async def get_data(self, inter):
        """/user_data get_data
        Get all the data the bot stores about you.
        Due to a Discord limitation, the bot cannot send the file in the interaction response, so you will be DMed instead.
        To prevent spam and getting ratelimited, there is a 100 second cooldown."""
        file = nextcord.File(
            BytesIO(
                orjson.dumps(
                    await self._get_json_data_by_user(inter.author),
                    option=orjson.OPT_INDENT_2,
                )
            ),
            filename="your_data.json",
        )
<<<<<<< HEAD
        # await inter.reply(
=======
        # await inter.send(
>>>>>>> disnake
        #  embed=SuccessEmbed(
        #    "Your json data will be attached in the next message due to API #limitations!"
        #  ),
        #  ephemeral = True
        # )
        successful = None
        exc_raised = None
        try:
            await inter.author.send(
                embed=SuccessEmbed("Your data has been attached in this message!"),
                file=file,
            )
<<<<<<< HEAD
            successful = True
        except BaseException as e:
            successful = False
            exc_raised = e
        if successful:
            return await inter.reply(
                embed=SuccessEmbed("I have DMed you your data!"), ephemeral=True
            )
        else:
            await inter.reply(
=======
            # TODO: when discord api allows sending files in interaction replies, send them the file
            successful = True
        except BaseException as e:  # We can't send
            successful = False
            exc_raised = e
        if successful:
            return await inter.send(
                embed=SuccessEmbed(":) I have DMed you your data!"), ephemeral=True
            )
        else:
            await inter.send(
>>>>>>> disnake
                embed=ErrorEmbed(
                    "I was unable to DM you your data. Please check your privacy settings. If this is a bug, please report it!"
                )
            )
            raise exc_raised

<<<<<<< HEAD
    @slash_command(
=======
    @commands.slash_command(
>>>>>>> disnake
        name="submit_a_request",
        description="Submit a request. I will know!",
        options=[
            Option(
                name="offending_problem_guild_id",
                description="The guild id of the problem you are trying to remove. The guild id of a global problem is null",
<<<<<<< HEAD
                type=OptionType.INTEGER,
=======
                type=OptionType.integer,
>>>>>>> disnake
                required=False,
            ),
            Option(
                name="offending_problem_id",
                description="The problem id of the problem. Very important (so I know which problem to check)",
<<<<<<< HEAD
                type=OptionType.INTEGER,
=======
                type=OptionType.integer,
>>>>>>> disnake
                required=False,
            ),
            Option(
                name="extra_info",
                description="A up to 5000 character description (about 2 pages) Use this wisely!",
<<<<<<< HEAD
                type=OptionType.STRING,
=======
                type=OptionType.string,
>>>>>>> disnake
                required=False,
            ),
            Option(
                name="copyrighted_thing",
                description="The copyrighted thing that this problem is violating",
<<<<<<< HEAD
                type=OptionType.STRING,
=======
                type=OptionType.string,
>>>>>>> disnake
                required=False,
            ),
            Option(
                name="type",
                description="Request type",
                required=False,
<<<<<<< HEAD
                type=OptionType.BOOLEAN,
=======
                type=OptionType.boolean,
>>>>>>> disnake
            ),
        ],
    )
    async def submit_a_request(
        self,
<<<<<<< HEAD
        inter: dislash.SlashInteraction,
=======
        inter: disnake.ApplicationCommandInteraction,
>>>>>>> disnake
        offending_problem_guild_id: int = None,
        offending_problem_id: int = None,
        extra_info: str = None,
        copyrighted_thing: str = Exception,
        type: str = "",
    ):
        "Submit a request! I will know! It uses a channel in my discord server and posts an embed"
        if (
            extra_info is None
            and type == ""
            and copyrighted_thing is not Exception
            and offending_problem_guild_id is None
            and offending_problem_id is None
        ):
<<<<<<< HEAD
            await inter.reply(embed=ErrorEmbed("You must specify some field."))
        if extra_info is None:
            await inter.reply(embed=ErrorEmbed("Please provide extra information!"))
=======
            await inter.send(embed=ErrorEmbed("You must specify some field."))
        if extra_info is None:
            await inter.send(embed=ErrorEmbed("Please provide extra information!"))
>>>>>>> disnake
        assert len(extra_info) <= 5000
        try:
            channel = await self.bot.fetch_channel(
                901464948604039209
            )  # CHANGE THIS IF YOU HAVE A DIFFERENT REQUESTS CHANNEL! (the part after id)
<<<<<<< HEAD
        except (nextcord.ext.commands.ChannelNotReadable, nextcord.Forbidden):
=======
        except (commands.ChannelNotReadable, disnake.Forbidden):
>>>>>>> disnake
            raise RuntimeError("The bot cannot send messages to the channel!")
        try:
            Problem = await self.bot.cache.get_problem(
                offending_problem_guild_id, offending_problem_id
            )
            problem_found = True
        except (TypeError, KeyError, problems_module.ProblemNotFound):
            # Problem not found
            problem_found = False
        content = self.bot.owner_id
        embed = nextcord.Embed(
            title=f"A new {type} request has been recieved from {inter.author.name}#{inter.author.discriminator}!",
            description="",
        )

        if problem_found:
            embed.description = f"Problem_info:{ str(Problem)}"
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
<<<<<<< HEAD
        await inter.reply("Your request has been submitted!")
=======
        await inter.send("Your request has been submitted!")
>>>>>>> disnake
