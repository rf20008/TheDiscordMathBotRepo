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
import contextlib
import datetime
import io
import textwrap
from os import urandom
from traceback import format_exception

import disnake
from disnake.ext import commands

from helpful_modules import checks
from helpful_modules.custom_bot import TheDiscordMathProblemBot
from helpful_modules.custom_embeds import SuccessEmbed
from helpful_modules.my_modals import MyModal
from helpful_modules.problems_module.cache_rewrite_with_redis import RedisCache
from helpful_modules.threads_or_useful_funcs import (
    get_log,
    log_evaled_code,
    file_version_of_item
)
from helpful_modules.paginator_view import PaginatorView

from .helper_cog import HelperCog
from .interesting_computation_ import InterestingComputationCog

CRTC = InterestingComputationCog.ChineseRemainderTheoremComputer
log = get_log(__name__)


class DebugCog(HelperCog):
    """Commands for debugging :-)"""

    def __init__(self, bot: TheDiscordMathProblemBot):
        super().__init__(bot)

    async def eval_code(self, inter, code: str, ephemeral: bool):
        """Evaluate code"""
        new_stdout = io.StringIO()
        new_stderr = io.StringIO()

        thing_to_run = """async def func(): """  # maybe: just exec() directly
        thing_to_run += "\n"
        thing_to_run += textwrap.indent(code, " " * 4, predicate=lambda l: True)
        compiled = False
        new_globals = {
            "bot": self.bot,
            "cache": self.cache,
            "self": self,
            "inter": inter,
            "author": inter.author,
            "restart": self.bot.restart,
        }
        new_globals.update(
            globals()
        )  # credit: https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/admin.py#L234 (for the idea)
        await log_evaled_code(code, time_ran=datetime.datetime.now())
        try:
            exec(thing_to_run, new_globals, locals())
            compiled = True
        except BaseException as e:
            compiled = False
            new_stderr.write("".join(format_exception(e)))
        if (
            "func" not in globals().keys()
            and "func" not in locals().keys()
            and compiled is True
        ):
            raise RuntimeError("func is not defined")
        err = None
        if compiled:
            try:
                with contextlib.redirect_stdout(new_stdout):
                    with contextlib.redirect_stderr(new_stderr):
                        if "func" in globals().keys():
                            print(
                                await globals()["func"](), file=new_stdout
                            )  # Get the 'func' from the global variables and call it
                            log.info("/eval ran (found in globals)")
                        elif "func" in locals().keys():
                            print(
                                await locals()["func"](), file=new_stdout
                            )  # Get func() from locals and call it
                            log.info("/eval ran (found in locals)")
                        else:
                            raise Exception("fatal: func() not defined")
            except BaseException as e:
                new_stderr.write("".join(format_exception(e)))
                err = None
        text = f"""The code was successfully executed!
            stdout: ```{new_stdout.getvalue()} ```
            stderr: ```{new_stderr.getvalue()} ```"""
        if len(text) <= 4096:
            await inter.send(embed=SuccessEmbed(text), ephemeral=ephemeral)
        else:
            await inter.response.defer()
            stdout_pages = PaginatorView.break_into_pages(new_stdout.getvalue(), max_page_length=2994)

            for i in range(len(stdout_pages)):
                stdout_pages[i] = f"```{stdout_pages[i]}```"
            if stdout_pages:
                stdout_pages[0] = "Stdout: " + stdout_pages[0]
            else:
                stdout_pages = ["Stdout: ``` ```"]
            stderr_pages = PaginatorView.break_into_pages(new_stderr.getvalue(), max_page_length=2994)
            for i in range(len(stderr_pages)):
                stderr_pages[i] = f"```{stderr_pages[i]}```"
            if stderr_pages:
                stderr_pages[0] = "Stderr: " + stderr_pages[0]
            else:
                stderr_pages = ["Stderr: ``` ```"]
            all_pages = []
            all_pages.extend(stdout_pages)
            all_pages.extend(stderr_pages)
            await inter.send(view=PaginatorView(user_id=inter.author.id, pages=all_pages))
        new_stdout.close()
        new_stderr.close()
        if err is not None:
            raise err
        else:
            return

    async def cog_slash_command_check(
        self, inter: disnake.ApplicationCommandInteraction
    ):
        """A check that makes sure only bot owners can use this cog!"""
        if not await self.bot._is_owner(inter.author):
            raise commands.CheckFailure("You are not the owner of this bot!")
        return True
        # if self.bot.owner_id in [None, [], set()] and self.bot.owner_ids is None:
        #     raise commands.CheckFailure(
        #         "Failing to protect myself (neither owner_id nor owner_ids are defined)"
        #     )
        # if self.bot.owner_id in [None, [], set()]:
        #     raise commands.CheckFailure(
        #         "You're not the owner of this bot! You must be the owner to execute debug commands!"
        #     )
        # if self.bot.owner_id == inter.author.id:
        #     return True
        #
        # try:
        #     if (
        #         self.bot.owner_ids not in [None, [], set()]
        #         and inter.author.id in self.bot.owner_ids
        #     ):
        #         return True
        #     raise commands.CheckFailure("You don't own this bot!")
        # except AttributeError:
        #     raise commands.CheckFailure("You don't own this bot!")

    @commands.is_owner()
    @checks.trusted_users_only()
    @commands.slash_command(
        name="sql",
        description="Run SQL",
        options=[
            disnake.Option(
                name="query",
                description="The query to run",
                type=disnake.OptionType.string,
                required=True,
            )
        ],
    )
    async def sql(
        self,
        inter: disnake.ApplicationCommandInteraction,
        query: str,
        ephemeral: bool = False,
    ):
        """/sql [query: str]
        A debug command to run SQL!
        You must own this bot to run this command!"""
        print("hello!")
        try:
            assert await self.cog_slash_command_check(inter)
        except AssertionError:
            await inter.send("I don't believe you own me.")
            raise
        except disnake.ext.commands.CheckFailure:
            raise
        try:
            result = await self.cache.run_sql(query)
        except BaseException as e:
            await inter.send(
                "An exception occurred while running the SQL!", ephemeral=ephemeral
            )
            raise
        if len(f"Result: {result}") < 1800:
            await inter.send(f"Result: {result}", ephemeral=ephemeral)
        else:
            await inter.send(
                "The result is in the attached file!",
                ephemeral=ephemeral,
                file=file_version_of_item(str(result), "sql_result.txt")
            )
        return

    @commands.is_owner()
    @checks.trusted_users_only()
    @commands.slash_command(
        name="eval",
        description="Execute arbitrary python code (only owners can do this)",
        options=[
            disnake.Option(
                name="code",
                description="The code to execute",
                type=disnake.OptionType.string,
                required=True,
            ),
            disnake.Option(
                name="ephemeral",
                description="Whether the result of the code should be printed ephemerally",
                type=disnake.OptionType.boolean,
                required=False,
            ),
        ],
    )
    async def eval(
        self, inter: disnake.ApplicationCommandInteraction, code: str, ephemeral=False
    ):
        """/eval [code: str]
        Evaluate arbitrary python code.
        Any instances of `\n` in code and stdin will be replaced with a newline character!
        This will happen even in strings. Therefore, be very careful!
        Only the owner can run this command!
        This requires both the owner and the bot to have the Administrator permission.
        """
        new_stdout = io.StringIO()
        new_stderr = io.StringIO()
        try:
            if not await self.cog_slash_command_check(inter) or not await self.bot.is_owner(inter.author):
                await inter.send(
                    "I know that you don't own me. You cannot use /eval. Goodbye."
                )
                return
        except disnake.ext.commands.CheckFailure:
            raise

        await self.eval_code(inter, code, ephemeral)

    @commands.is_owner()
    @checks.trusted_users_only()
    @commands.slash_command(
        name="redis",
        description="get redis queries. HOWEVER THIS IS RESTRICTED TO OWNERS ONLY",
        options=[
            disnake.Option(
                name="key",
                description="the key",
                type=disnake.OptionType.string,
                required=True,
            ),
            disnake.Option(
                name="value",
                description="the value",
                type=disnake.OptionType.string,
                required=False,
            ),
        ],
    )
    async def redis(
        self,
        inter: disnake.ApplicationCommandInteraction,
        key: str,
        value: str | None = None,
    ):
        """
        Like the eval and sql command, this command is restricted to owners
        Parameters: key: str: the key we want to view or modify
        value: str. This is an optional parameter. If not specified, it will just tell you what is stored at value

        Parameters
        ----------
        :param inter: the interaction
        :param key: the key
        :param value: the value [not required]

        Returns
        -------
        It doesn't actually return anything as a function, but it does the things.

        """
        if not await self.cog_slash_command_check(inter):
            await inter.send(
                "You do not own me. This command is restricted to **owners only**"
            )
            return
        if not await self.bot.is_owner(inter.author):
            return await inter.send(
                "This command is restricted to owners only, but you are not an owner"
            )
        if not isinstance(self.bot.cache, RedisCache):
            raise RuntimeError(
                "/redis is not supported if the cache is not a RedisCache"
            )
        raise NotImplementedError("This isn't implemented yet")

    @commands.is_owner()
    @checks.trusted_users_only()
    @commands.slash_command(
        name="eval2",
        description="Evaluate Python code (for owners only)- this uses a modal",
        options = [
            disnake.Option(
                name="ephemeral",
                description="Whether to send the results ephermally",
                type=disnake.OptionType.boolean,
                required=False
            )
        ]
    )
    async def eval2(self, inter, ephemeral: bool=False):
        """/eval2

        This does Eval2. It is restricted to owners only. This command gives a modal"""
        if not await self.bot.is_owner(inter.author):
            raise commands.NotOwner("You must be the owner to use /eval2")

        if not await self.bot.is_trusted(inter.author):
            raise RuntimeError("You must be trusted to use /eval2")

        the_custom_id = urandom(20).hex()
        text_inputs = [
            disnake.ui.TextInput(
                label="What code do you want to run?",
                custom_id=the_custom_id,
                style=disnake.TextInputStyle.paragraph,
                required=True,
                max_length=4000,
            )
        ]
        code_to_run = ""

        async def callback(s, modal_inter: disnake.ModalInteraction):
            if modal_inter.author.id != inter.author.id:
                raise RuntimeError
            nonlocal code_to_run
            code_to_run = modal_inter.text_values[the_custom_id]
            await modal_inter.send("Thanks for providing the code to run :-)")

        modal_custom_id = urandom(20).hex()
        modal: MyModal = MyModal(
            timeout=180,
            title="What code do you want to run?",
            custom_id=modal_custom_id,
            callback=callback,
            inter=inter,
            components=[],
            check = checks.always_succeeding_check_unwrapped
        )
        modal.append_component(text_inputs)
        await inter.response.send_modal(modal)
        _ = await self.bot.wait_for(
            "modal_submit",
            check=lambda modal_inter: modal_inter.custom_id == modal_custom_id,
        )
        # await modal_inter.send("Yes!")

        await self.eval_code(inter, code_to_run, ephemeral=ephemeral)
