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

import io
import json
import unittest

from helpful_modules import StatsTrack

USAGE = StatsTrack.CommandUsage(user_id=3, command_name="test", time=-1.0)


class TestCommandUsage(unittest.TestCase):
    """Test cases for the CommandUsage class."""

    def test_to_dict(self):
        """Test the to_dict method of the CommandUsage class."""
        self.assertEqual(
            USAGE.to_dict(), {"user_id": 3, "command_name": "test", "time": -1.0}
        )

    def test_from_dict(self):
        """Test the from_dict method of the CommandUsage class."""
        self.assertEqual(
            StatsTrack.CommandUsage.from_dict(
                {"user_id": 3, "command_name": "test", "time": -1.0}
            ),
            USAGE,
        )


class TestCommandStats(unittest.TestCase):
    """Test cases for the CommandStats class."""

    def setUp(self):
        """Set up common objects for test cases."""
        self.default_command_stats = StatsTrack.CommandStats()
        self.usage1 = StatsTrack.CommandUsage(user_id=1, command_name="test", time=0.5)
        self.usage2 = StatsTrack.CommandUsage(
            user_id=2, command_name="command", time=1.0
        )

    def test_eq_basic_1(self):
        """Test the equality of CommandStats with default values."""
        self.assertEqual(
            self.default_command_stats,
            StatsTrack.CommandStats(usages=[], unique_users=[], total_cmds=0),
        )

    def test_eq_type_reject_1(self):
        """Test inequality when comparing CommandStats with a different type."""
        self.assertNotEqual(self.default_command_stats, "hehe boi")

    def test_eq_basic_2(self):
        """Test the equality of CommandStats with a specified total_cmds value."""
        self.assertEqual(
            StatsTrack.CommandStats(total_cmds=737),
            StatsTrack.CommandStats(usages=[], unique_users=[], total_cmds=737),
        )

    def test_eq_cmd_diff(self):
        """Test inequality when comparing CommandStats with different total_cmds values."""
        self.assertNotEqual(
            StatsTrack.CommandStats(total_cmds=32),
            StatsTrack.CommandStats(total_cmds=33),
        )

    def test_eq_usr_diff(self):
        """Test inequality when comparing CommandStats with different unique_users values."""
        self.assertNotEqual(
            StatsTrack.CommandStats(unique_users=[3, 4]),
            StatsTrack.CommandStats(unique_users=[3, 81]),
        )

    def test_update(self):
        """Test the update_with_new_usage method of CommandStats."""
        old = StatsTrack.CommandStats()
        self.assertEqual(old.total_cmds, 0)
        old.update_with_new_usage(USAGE)
        self.assertEqual(
            old, StatsTrack.CommandStats(usages=[USAGE], unique_users=[3], total_cmds=1)
        )

    def test_num_unique_users(self):
        """Test the num_unique_users property of CommandStats."""
        old = StatsTrack.CommandStats()
        self.assertEqual(old.num_unique_users, 0)
        old.update_with_new_usage(USAGE)
        self.assertEqual(old.num_unique_users, 1)
        old.update_with_new_usage(USAGE)
        self.assertEqual(old.num_unique_users, 1)
        old.update_with_new_usage(
            StatsTrack.CommandUsage(user_id=129, command_name="test", time=-1.0)
        )
        self.assertEqual(old.num_unique_users, 2)
        old.unique_users = {1, 2, 3, 4, 5, 6, 7, 8, 129}
        self.assertEqual(old.num_unique_users, 9)

    def test_to_dict_1(self):
        stats = StatsTrack.CommandStats(
            usages=[self.usage1, self.usage2], total_cmds=2, unique_users={1, 2}
        )
        expected_dict = {
            "usages": [
                {"user_id": 1, "command_name": "test", "time": 0.5},
                {"user_id": 2, "command_name": "command", "time": 1.0},
            ],
            "unique_users": [1, 2],
            "total_cmds": 2,
        }
        self.assertEqual(stats.to_dict(), expected_dict)

    def test_from_dict_1(self):
        input_dict = {
            "usages": [
                {"user_id": 1, "command_name": "test", "time": 0.5},
                {"user_id": 2, "command_name": "command", "time": 1.0},
            ],
            "unique_users": [1, 2],
            "total_cmds": 2,
        }
        expected_stats = StatsTrack.CommandStats(
            usages=[self.usage1, self.usage2], total_cmds=2, unique_users={1, 2}
        )
        self.assertEqual(StatsTrack.CommandStats.from_dict(input_dict), expected_stats)

    def test_represent(self):
        stats = StatsTrack.CommandStats(
            usages=[self.usage1, self.usage2], total_cmds=2, unique_users={1, 2}
        )
        expected_representation = str(stats.to_dict())
        self.assertEqual(stats.represent(), expected_representation)

    def test_to_dict_2(self):
        usage = StatsTrack.CommandUsage(user_id=1, command_name="test", time=0.5)
        expected_dict = {"user_id": 1, "command_name": "test", "time": 0.5}
        self.assertEqual(usage.to_dict(), expected_dict)

    def test_from_dict_2(self):
        input_dict = {"user_id": 1, "command_name": "test", "time": 0.5}
        expected_usage = StatsTrack.CommandUsage(
            user_id=1, command_name="test", time=0.5
        )
        self.assertEqual(StatsTrack.CommandUsage.from_dict(input_dict), expected_usage)


class TestStreamWrapperStorer(unittest.TestCase):
    def test_write_stats(self):
        stream = io.StringIO()
        storer = StatsTrack.StreamWrapperStorer(stream=stream, reading=io.StringIO())
        usage = StatsTrack.CommandUsage(user_id=1, command_name="test", time=0.5)
        stats = StatsTrack.CommandStats(usages=[usage], total_cmds=1, unique_users={1})

        storer.writeStats(stats)

        expected_json = json.dumps(stats.to_dict())
        self.assertEqual(
            stream.getvalue().replace('"', "'"), expected_json.replace('"', "'")
        )

    def test_return_stats(self):
        stream = io.StringIO()
        usage = StatsTrack.CommandUsage(user_id=1, command_name="test", time=0.5)
        stats = StatsTrack.CommandStats(usages=[usage], total_cmds=1, unique_users={1})
        reading = io.StringIO(json.dumps(stats.to_dict()))
        # print(reading.getvalue())
        storer = StatsTrack.StreamWrapperStorer(stream=stream, reading=reading)

        # print("read: " + reading.read(3333333))
        returned_stats = storer.return_stats()

        self.assertEqual(returned_stats, stats)

    def test_close(self):
        stream = io.StringIO()
        reading = io.StringIO()
        storer = StatsTrack.StreamWrapperStorer(stream=stream, reading=reading)

        storer.close()

        self.assertTrue(stream.closed)


if __name__ == "__main__":
    unittest.main()
