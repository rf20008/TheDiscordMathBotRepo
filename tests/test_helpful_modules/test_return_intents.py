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

from disnake import Intents

from helpful_modules.return_intents import (
    return_intents,
)  # Make sure to replace 'your_module' with the actual module name


class TestReturnIntents(unittest.TestCase):
    def test_return_intents(self):
        result = return_intents()

        # Ensure the returned object is an instance of Intents
        self.assertIsInstance(result, Intents)

        # Check specific attributes of the Intents object
        self.assertFalse(result.typing)
        self.assertFalse(result.presences)
        self.assertFalse(result.members)
        self.assertFalse(result.reactions)
        self.assertFalse(result.bans)


if __name__ == "__main__":
    unittest.main()
