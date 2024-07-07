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

import os
import unittest
from unittest.mock import AsyncMock

import disnake

import helpful_modules.paginator_view

PaginatorView = helpful_modules.paginator_view.PaginatorView
break_into_pages = PaginatorView.break_into_pages
FINAL_BYTES = b"\x31\x41\x59\x26\x53\x59"
FINAL_VALUE = "314159265359"


# TODO: I NEED TO USE MOCK INTERACTIONS


class TestPaginatorView(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Initialize any required objects or setup before each test
        self.user_id = -100
        self.pages = ["Page 1", "Page 2", "Page 3"]
        self.paginator_view = PaginatorView(self.user_id, self.pages)

    async def test_interaction_check_valid_user(self):
        interaction = AsyncMock(spec=disnake.Interaction)
        interaction.author = AsyncMock(spec=disnake.User, id=self.user_id)
        result = await self.paginator_view.interaction_check(interaction)
        self.assertTrue(result)

    async def test_interaction_check_invalid_user(self):
        interaction = AsyncMock(
            spec=disnake.Interaction, author=AsyncMock(id=self.user_id + 1)
        )

        result = await self.paginator_view.interaction_check(interaction)
        self.assertFalse(result)

    async def test_next_page_button(self):
        author = AsyncMock(spec=disnake.User, id=self.user_id)
        interaction = AsyncMock(spec=disnake.MessageInteraction, author=author)
        original_message = AsyncMock(
            spec=disnake.Message,
            id=-123,
            channel=AsyncMock(spec=disnake.PartialMessageable, id=-123),
            interaction=interaction,
        )

        await self.paginator_view.next_page_button.callback(interaction)

        interaction.edit_original_message.assert_awaited_once_with(
            view=self.paginator_view, embed=self.paginator_view.create_embed()
        )

    async def test_prev_page_button(self):
        author = AsyncMock(spec=disnake.User, id=self.user_id)
        interaction = AsyncMock(spec=disnake.MessageInteraction, author=author)
        # original_message = disnake.Message(id=-123, channel=disnake.TextChannel(id=456), interaction=interaction)
        original_message = AsyncMock(
            spec=disnake.Message,
            id=-123,
            channel=AsyncMock(spec=disnake.PartialMessageable, id=-123),
            interaction=interaction,
        )

        self.paginator_view.page_num = 2
        await self.paginator_view.prev_page_button.callback(interaction)

        interaction.edit_original_message.assert_awaited_once_with(
            view=self.paginator_view, embed=self.paginator_view.create_embed()
        )
        self.assertEqual(1, self.paginator_view.page_num)

    async def test_on_timeout(self):
        # Set up the view with some items
        self.paginator_view.items = [disnake.ui.Button(), disnake.ui.Button()]

        # Mock the disabling of items
        await self.paginator_view.on_timeout()

        # Check that items were disabled
        self.assertTrue(self.paginator_view.items[0].disabled)
        self.assertTrue(self.paginator_view.items[1].disabled)

    async def test_create_embed(self):
        expected_embed = disnake.Embed(
            title=f"Page {self.paginator_view.page_num} of {len(self.paginator_view.pages)}:",
            description=self.paginator_view.pages[self.paginator_view.page_num],
            color=disnake.Color.from_rgb(50, 50, 255),
        )

        result_embed = self.paginator_view.create_embed()

        self.assertEqual(expected_embed.title, result_embed.title)
        self.assertEqual(expected_embed.description, result_embed.description)
        self.assertEqual(expected_embed.color, result_embed.color)

    # Add more test cases for other methods as needed

    async def test_go_to_page_button_valid_input_1(self):
        author = AsyncMock(spec=disnake.User, id=self.id)
        interaction = AsyncMock(spec=disnake.MessageInteraction, author=author)
        original_message = AsyncMock(
            spec=disnake.Message,
            id=-123,
            channel=AsyncMock(spec=disnake.PartialMessageable, id=-123),
            interaction=interaction,
        )

        # Mock the modal response

        with unittest.mock.patch("os.urandom", return_value=FINAL_BYTES):
            modal_interaction = AsyncMock(
                spec=disnake.ModalInteraction,
                text_values={"page_num_ui_modal314159265359": "2"},
            )

            modal = await self.paginator_view.go_to_page_button.callback(interaction)
            await modal.callback(modal_interaction)
            modal_interaction.edit_original_message.assert_awaited()

    async def test_go_to_page_button_valid_input_2(self):
        # Mock interaction with the expected user
        interaction = AsyncMock(
            spec=disnake.MessageInteraction,
            author=AsyncMock(id=self.user_id),
            response=AsyncMock(spec=disnake.InteractionResponse),
        )
        interaction.response.send_modal.return_value = AsyncMock()

        # Mock the modal interaction with valid input
        modal_interaction = AsyncMock(
            spec=disnake.ModalInteraction,
            text_values={"page_num_ui_modal" + FINAL_VALUE: "2"},
        )
        # Patch the response.send_modal method to return the modal interaction
        with unittest.mock.patch("os.urandom", return_value=FINAL_BYTES):

            # Call the go_to_page_button method
            modal = await self.paginator_view.go_to_page_button.callback(interaction)

        # Assertions
        interaction.response.send_modal.assert_called_once()
        modal_interaction = AsyncMock(
            spec=disnake.ModalInteraction, response=AsyncMock()
        )
        await modal.callback(modal_interaction)
        modal_interaction.response.edit_original_message.assert_called_once_with(
            embed=self.paginator_view.create_embed(), view=self.paginator_view
        )

    async def test_go_to_page_button_invalid_input_not_an_integer(self):
        author = AsyncMock(spec=disnake.User, id=self.id)
        interaction = AsyncMock(spec=disnake.MessageInteraction, author=author)
        original_message = AsyncMock(
            spec=disnake.Message,
            id=-123,
            channel=AsyncMock(spec=disnake.PartialMessageable, id=-123),
            interaction=interaction,
        )

        modal_interaction = AsyncMock(
            spec=disnake.ModalInteraction,
            text_values={"page_num_ui_modal314159265359": "HEHEHEHEHEHEHE"},
        )
        # Call the function!
        with unittest.mock.patch("os.urandom", return_value=FINAL_BYTES):
            with unittest.mock.patch.object(
                interaction.response, "send_modal", return_value=modal_interaction
            ):
                modal = await self.paginator_view.go_to_page_button.callback(
                    interaction
                )
                await modal.callback(modal_interaction)
        # asserts

        modal_interaction.assert_not_awaited()

    async def test_go_to_page_button_invalid_input_out_of_bounds(self):
        interaction = AsyncMock(
            spec=disnake.MessageInteraction,
            author=AsyncMock(id=self.user_id),
            response=AsyncMock(),
        )
        original_message = AsyncMock(
            spec=disnake.Message,
            id=-123,
            channel=AsyncMock(spec=disnake.PartialMessageable, id=-123),
            interaction=interaction,
        )
        modal_interaction = unittest.mock.AsyncMock(
            spec=disnake.ModalInteraction,
            text_values={"page_num_ui_modal314159265359": "10"},
            response=AsyncMock(),
            _check=lambda *args, **kwargs: True,
        )  # Out of bounds
        # Mock the modal response
        with unittest.mock.patch("os.urandom", return_value=FINAL_BYTES):

            modal = await self.paginator_view.go_to_page_button.callback(interaction)
            await modal.callback(modal_interaction)
            self.assertNotEqual(self.paginator_view.page_num, 10)
            modal_interaction.send.assert_awaited()


class TestBreakIntoPages(unittest.TestCase):
    def test_example_1(self):
        text = "Hello!!!!!"
        max_page_length = 20
        expected_result = ["Hello!!!!!"]
        self.assertEqual(break_into_pages(text, max_page_length), expected_result)

    def test_example_2(self):
        text = "Hello!!!!!"
        max_page_length = 5
        expected_result = ["Hello", "!", "!!!!"]
        self.assertEqual(break_into_pages(text, max_page_length), expected_result)

    def test_example_3(self):
        text = "HELLOOO"
        max_page_length = 1
        expected_result = ["H", "E", "L", "L", "O", "O", "O"]
        self.assertEqual(break_into_pages(text, max_page_length), expected_result)

    def test_example_4(self):
        text = "Hello! I am rf20008"
        max_page_length = 6
        expected_result = ["Hello!", " I am ", "rf2000", "8"]
        self.assertEqual(expected_result, break_into_pages(text, max_page_length))

    def test_custom_1(self):
        text = "A long text with many characters."
        max_page_length = 10
        expected_result = ["A long ", "text with ", "many ", "characters", "."]
        self.assertEqual(break_into_pages(text, max_page_length), expected_result)

    def test_custom_2(self):
        text = "Short"
        max_page_length = 10
        expected_result = ["Short"]
        self.assertEqual(break_into_pages(text, max_page_length), expected_result)


if __name__ == "__main__":
    unittest.main()
