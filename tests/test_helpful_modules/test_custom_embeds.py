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

import unittest
from unittest.mock import patch

from disnake import Color, Embed

from helpful_modules.custom_embeds import (
    ErrorEmbed,
    SimpleEmbed,
    SuccessEmbed,
    generate_random_color,
)


class TestEmbeds(unittest.TestCase):
    @patch(
        "helpful_modules.custom_embeds.generate_random_color",
        return_value=Color.from_rgb(100, 150, 200),
    )
    def test_simple_embed(self, mock_generate_random_color):
        simple_embed = SimpleEmbed(
            title="Test Title", description="Test Description", footer="Test Footer"
        )

        self.assertEqual(simple_embed.title, "Test Title")
        self.assertEqual(simple_embed.description, "Test Description")
        self.assertEqual(simple_embed.footer.text, "Test Footer")
        self.assertEqual(simple_embed.color, Color.from_rgb(100, 150, 200))

        mock_generate_random_color.assert_called()

    def test_error_embed(self):
        error_embed = ErrorEmbed(description="Error Description", footer="Error Footer")

        self.assertEqual(error_embed.title, "Error")
        self.assertEqual(error_embed.description, "Error Description")
        self.assertEqual(error_embed.footer.text, "Error Footer")
        self.assertEqual(error_embed.color, Color.red())

    def test_success_embed(self):
        success_embed = SuccessEmbed(
            description="Success Description", footer="Success Footer"
        )

        self.assertEqual(success_embed.title, "Success!")
        self.assertEqual(success_embed.description, "Success Description")
        self.assertEqual(success_embed.footer.text, "Success Footer")
        self.assertEqual(success_embed.color, Color.green())


if __name__ == "__main__":
    unittest.main()
