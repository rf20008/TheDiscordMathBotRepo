import json
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import disnake
from disnake.ext import commands

import cogs


class TestDataModificationCog(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.bot = MagicMock()
        self.cog = cogs.DataModificationCog(self.bot)

    async def asyncSetUp(self):
        # Set up any asynchronous fixtures or test data
        pass

    def test_user_data_command(self):
        # Mock interaction for user_data command
        interaction = MagicMock(spec=disnake.ApplicationCommandInteraction)
        interaction.author.id = 123456789

        # Call the user_data command
        with unittest.mock.patch.object(
            self.cog, "_get_json_data_by_user", AsyncMock()
        ):
            self.cog.user_data.callback(self.cog, interaction)
        raise Exception("This test is unfinished, and should not pass by default")
        # Add assertions based on expected behavior of user_data command

    async def test_delete_all_command(self):
        # Mock interaction for delete_all command
        interaction = AsyncMock(spec=disnake.ApplicationCommandInteraction)
        interaction.author.id = 123456789
        interaction.response.defer.return_value = None

        # Mock cache methods
        self.bot.cache.get_problems_by_func.return_value = []
        self.bot.cache.get_user_data.return_value = MagicMock(
            user_id=interaction.author.id, trusted=False, denylisted=False
        )

        # Call the delete_all command
        with patch.object(self.cog, "_get_json_data_by_user", AsyncMock()):
            await self.cog.delete_all.callback(self.cog, inter=interaction)
        raise Exception("This test is unfinished, and should not pass by default")
        # Add assertions based on expected behavior of delete_all command

    async def test_get_data_command(self):
        # Mock interaction for get_data command
        interaction = AsyncMock(
            spec=disnake.ApplicationCommandInteraction, response=AsyncMock()
        )
        interaction.author.id = 123456789
        interaction.response.defer.return_value = None
        with patch.object(
            self.bot.cache,
            "get_all_by_author_id",
            new=AsyncMock(
                return_value={
                    "problems": [],
                    "quiz_problems": [],
                    "quiz_submissions": [],
                    "sessions": [],
                    "descriptions_created": [],
                    "appeals": [],
                }
            ),
        ):
            # Mock cache methods

            # Call the get_data command
            await self.cog.get_data.callback(self.cog, inter=interaction)
            raise Exception("This test is unfinished, and should not pass by default")
            # Add assertions based on expected behavior of get_data command


if __name__ == "__main__":
    unittest.main()
