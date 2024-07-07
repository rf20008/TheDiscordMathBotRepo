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

from helpful_modules.problems_module import UserData


class TestUserData(unittest.TestCase):

    def test_init_with_valid_input(self):
        # Arrange
        user_id = -123
        trusted = True
        denylisted = False

        # Act
        user_data = UserData(user_id=user_id, trusted=trusted, denylisted=denylisted)

        # Assert
        self.assertEqual(user_data.user_id, user_id)
        self.assertEqual(user_data.trusted, trusted)
        self.assertEqual(user_data.denylisted, denylisted)

    def test_init_with_invalid_input(self):
        # Arrange & Act & Assert
        with self.assertRaises(TypeError):
            UserData(user_id="-123", trusted=True, denylisted=False)

        with self.assertRaises(TypeError):
            UserData(user_id=-123, trusted="True", denylisted=False)

        with self.assertRaises(TypeError):
            UserData(user_id=-123, trusted=True, denylisted="False")

    def test_from_dict(self):
        # Arrange
        user_data_dict = {"user_id": -123, "trusted": True, "denylisted": False}

        # Act
        user_data = UserData.from_dict(user_data_dict)

        # Assert
        self.assertEqual(user_data.user_id, user_data_dict["user_id"])
        self.assertEqual(user_data.trusted, user_data_dict["trusted"])
        self.assertEqual(user_data.denylisted, user_data_dict["denylisted"])

    def test_to_dict(self):
        # Arrange
        user_id = -123
        trusted = True
        denylisted = False
        user_data = UserData(user_id=user_id, trusted=trusted, denylisted=denylisted)

        # Act
        user_data_dict = user_data.to_dict()

        # Assert
        self.assertEqual(user_data_dict["user_id"], user_id)
        self.assertEqual(user_data_dict["trusted"], trusted)
        self.assertEqual(user_data_dict["denylisted"], denylisted)

    def test_default_method(self):
        # Arrange
        user_id = -123

        # Act
        user_data = UserData.default(user_id)

        # Assert
        self.assertEqual(user_data.user_id, user_id)
        self.assertFalse(user_data.trusted)
        self.assertFalse(user_data.denylisted)


if __name__ == "__main__":
    unittest.main()
