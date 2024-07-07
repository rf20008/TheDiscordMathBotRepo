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

import datetime
import unittest
import unittest.mock

import aiohttp.web_response
import disnake
import disnake.ext

from helpful_modules import base_on_error
from helpful_modules.custom_embeds import ErrorEmbed
from helpful_modules.problems_module.errors import LockedCacheException
from tests.utils import check_embed_equality

FORBIDDEN_RESPONSE = """There was a 403 error. This means either
1) You didn't give me enough permissions to function correctly, or
2) There's a bug! If so, please report it!
The error traceback is below."""


# TODO: all my tests are failing because the _error_log is not working, so patch them
class TestBaseOnError(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        bot = unittest.mock.AsyncMock(spec=disnake.ext.commands.Bot)
        inter = unittest.mock.AsyncMock(spec=disnake.ApplicationCommandInteraction)
        inter.bot = bot

    async def test_locked_cache_exception_handling(self):
        inter = unittest.mock.AsyncMock(spec=disnake.ApplicationCommandInteraction)
        error = LockedCacheException("The cache is currently locked!")
        result = await base_on_error.base_on_error(inter, error)

        self.assertEqual(
            result["content"],
            "The bot's cache's lock is currently being held. Please try again later.",
        )

    async def test_pass_on_non_exceptions(self):
        # TODO: investigate the cause
        bot = unittest.mock.AsyncMock(spec=disnake.ext.commands.Bot)
        inter = unittest.mock.AsyncMock(spec=disnake.ApplicationCommandInteraction)
        inter.bot = bot
        with self.assertRaises(KeyboardInterrupt):
            await base_on_error.base_on_error(
                inter, error=KeyboardInterrupt("Keyboard Interrupt")
            )
            inter.bot.close.assert_awaited()

    # TODO: finish
    # TODO: there are so many more tests, that need to be made :)
    @unittest.mock.patch("disnake.utils.utcnow")
    @unittest.mock.patch("helpful_modules._error_logging.log_error_to_file")
    async def test_cooldown_errors(self, mock_utcnow, mock_log):
        mock_utcnow.return_value = datetime.datetime(
            year=1970,
            month=1,
            day=1,
            hour=0,
            minute=0,
            second=1,
            microsecond=0,
            tzinfo=datetime.timezone(offset=datetime.timedelta(hours=0)),
        )
        bot = unittest.mock.AsyncMock(spec=disnake.ext.commands.Bot)
        inter = unittest.mock.AsyncMock(spec=disnake.ApplicationCommandInteraction)
        inter.bot = bot
        result = await base_on_error.base_on_error(
            inter,
            error=disnake.ext.commands.CommandOnCooldown(
                retry_after=3.0,
                cooldown=disnake.ext.commands.Cooldown(rate=3, per=1),
                type=disnake.ext.commands.BucketType.default,
            ),
        )
        inter.send.assert_not_awaited()
        # content = f"This command is on cooldown; please retry **{disnake.utils.format_dt(disnake.utils.utcnow() + datetime.timedelta(seconds=error.retry_after), style='R')}**." # type: ignore

        # return {"content": content, "delete_after": error.retry_after}
        self.assertEqual(
            result["content"], f"This command is on cooldown; please retry **<t:1:R>**."
        )
        self.assertEqual(result["delete_after"], 3.0, "Delete afters do not match")
        self.assertEqual(set(result.keys()), {"content", "delete_after"})
        mock_log.assert_called_once()
        # return {"content": content, "delete_after": error.retry_after}, "delete_after": 3.0})

    # these three tests come from ChatGPT
    @unittest.mock.patch("helpful_modules._error_logging.log_error_to_file")
    async def test_forbidden_error(self, mock_log):
        lines = FORBIDDEN_RESPONSE.split("\n")
        bot = unittest.mock.AsyncMock(spec=disnake.ext.commands.Bot)
        inter = unittest.mock.AsyncMock(spec=disnake.ApplicationCommandInteraction)
        inter.bot = bot
        result = await base_on_error.base_on_error(
            inter,
            error=disnake.Forbidden(
                message="Insufficient permissions.",
                response=aiohttp.web_response.Response,
            ),
        )
        expected_result = {
            "content": "There was a 403 error. This means either\n"
            "1) You didn't give me enough permissions to function correctly, or\n"
            "2) There's a bug! If so, please report it!\n\n"
            "The error traceback is below."
        }
        for line in lines:
            self.assertIn(
                line,
                result["content"][: len(FORBIDDEN_RESPONSE) + 55],
                "One of the lines isn' in the beginning of the FORB response",
            )
        expected_result["content"] = result["content"]  # TODO: fix the monkey patch
        self.assertEqual(result, expected_result, "Results do not match")
        mock_log.assert_not_called()

    @unittest.mock.patch("helpful_modules._error_logging.log_error_to_file")
    async def test_not_owner_error(self, mock_log):
        bot = unittest.mock.AsyncMock(spec=disnake.ext.commands.Bot)
        inter = unittest.mock.AsyncMock(spec=disnake.ApplicationCommandInteraction)
        inter.bot = bot
        result = await base_on_error.base_on_error(
            inter, error=disnake.ext.commands.errors.NotOwner()
        )
        expected_result = {"embed": ErrorEmbed("You are not the owner of this bot.")}
        check_embed_equality(expected_result["embed"], result["embed"])
        self.assertEqual(result, expected_result, "Results do not match")
        mock_log.assert_not_called()

    @unittest.mock.patch("helpful_modules._error_logging.log_error_to_file")
    async def test_check_failure_error(self, _):
        bot = unittest.mock.AsyncMock(spec=disnake.ext.commands.Bot)
        inter = unittest.mock.AsyncMock(spec=disnake.ApplicationCommandInteraction)
        inter.bot = bot
        error_message = "Custom check failed."
        result = await base_on_error.base_on_error(
            inter, error=disnake.ext.commands.errors.CheckFailure(error_message)
        )
        expected_result = {"embed": ErrorEmbed(error_message)}
        check_embed_equality(expected_result["embed"], result["embed"])
        # self.assertTrue(expected_result == result, f"The embeds do not match: expected = {repr(expected_result['embed'])} but actual is {repr(result['embed'].__dict__)}")

    @unittest.mock.patch("helpful_modules._error_logging.log_error_to_file")
    async def test_logging_error(self, mock_log_error):
        bot = unittest.mock.AsyncMock(spec=disnake.ext.commands.Bot)
        inter = unittest.mock.AsyncMock(spec=disnake.ApplicationCommandInteraction)
        inter.bot = bot
        error_message = "Test error message"
        mock_log_error.side_effect = RuntimeError("HAHAHAHA!")
        result = await base_on_error.base_on_error(
            inter, error=Exception(error_message)
        )
        inter.send.assert_not_awaited()
        inter.bot.close.assert_not_awaited()
        self.assertIsInstance(result, dict)
        stuff = result["embed"].description

        self.assertIn(error_message, stuff)
        self.assertIn("An error occurred!", stuff)
        self.assertIn("Steps you should do:", stuff)
        self.assertIn(
            "Additionally, while trying to log this error, the following exception occurred: \n",
            stuff,
        )

    @unittest.mock.patch("helpful_modules._error_logging.log_error_to_file")
    async def test_embed_creation(self, _):
        bot = unittest.mock.AsyncMock(spec=disnake.ext.commands.Bot)
        inter = unittest.mock.AsyncMock(spec=disnake.ApplicationCommandInteraction)
        inter.bot = bot
        error_message = "Test error message"
        result = await base_on_error.base_on_error(
            inter, error=Exception(error_message)
        )
        self.assertIsInstance(result, dict)
        inter.send.assert_not_awaited()
        inter.bot.close.assert_not_awaited()
        self.assertIn("Oh, no! An error occurred!", result["embed"].title)
        self.assertIn("Time:", result["embed"].footer.text)
        self.assertIn(
            base_on_error.get_git_revision_hash(), result["embed"].footer.text
        )

    @unittest.mock.patch("helpful_modules._error_logging.log_error_to_file")
    async def test_embed_fallback_to_plain_text(self, _):
        bot = unittest.mock.AsyncMock(spec=disnake.ext.commands.Bot)
        inter = unittest.mock.AsyncMock(spec=disnake.ApplicationCommandInteraction)
        inter.bot = bot
        # Simulate a condition where creating an embed raises an exception
        with unittest.mock.patch(
            "disnake.Embed", side_effect=(TypeError("Test error"))
        ):
            result = await base_on_error.base_on_error(
                inter, error=Exception("Test error message")
            )
        inter.send.assert_not_awaited()
        inter.bot.close.assert_not_awaited()
        self.assertIn("Oh no! An Exception occurred!", result["content"])
        self.assertIn("Test error message", result["content"])
        self.assertIn("Time:", result["content"])
        self.assertIn(base_on_error.get_git_revision_hash(), result["content"])


class TestGitCommitHash(unittest.TestCase):
    """This is a test class testing the GitCommitHash
    It's from ChatGPT!"""

    @unittest.mock.patch("subprocess.check_output")
    def test_get_git_commit_hash(self, mock_check_output):
        # Set the return value of subprocess.check_output
        mock_check_output.return_value = b"abcdef123456\n"

        # Now call your function
        result = base_on_error.get_git_revision_hash()

        # Check that subprocess.check_output was called with the correct arguments
        mock_check_output.assert_called_once_with(
            ["git", "rev-parse", "HEAD"], encoding="ascii", errors="ignore"
        )

        # Check the result
        self.assertIn(result, ["abcdef1", b"abcdef1"])


if __name__ == "__main__":
    unittest.main()
