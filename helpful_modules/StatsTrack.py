"""
You can distribute any version of the Software created and distributed *before* 23:17:55.00 July 28, 2024 GMT-4
under the GNU General Public License version 3 or at your option, any  later option.
But versions of the code created and/or distributed *on or after* that date must be distributed
under the GNU *Affero* General Public License, version 3, or, at your option, any later version.

This file is part of The Discord Math Problem Bot Repo

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

Author: Samuel Guo (64931063+rf20008@users.noreply.github.com)
"""
import dataclasses
import io

try:
    import orjson as json
except ImportError:
    import json


@dataclasses.dataclass
class CommandUsage:
    user_id: int
    command_name: str
    time: float

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "command_name": self.command_name,
            "time": self.time,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(**d)


class CommandStats:
    usages: [CommandUsage]
    unique_users: set[int]
    total_cmds_used: int

    def __init__(self, usages=None, total_cmds=0, unique_users=()):
        self.usages = usages
        if usages is None:
            self.usages = []
        self.total_cmds = total_cmds
        self.unique_users = set(unique_users)

    def update_with_new_usage(self, usage: CommandUsage):
        self.usages.append(usage)
        self.unique_users.add(usage.user_id)
        self.total_cmds += 1

    @property
    def num_unique_users(self):
        # this could be more efficient by adding more properties
        return len(self.unique_users)

    def to_dict(self):
        return {
            "usages": [usage.to_dict() for usage in self.usages],
            "unique_users": list(self.unique_users),
            "total_cmds": self.total_cmds,
        }

    def represent(self):
        # represent self as a string
        return str(self.to_dict())

    def __str__(self):
        return self.represent()

    @classmethod
    def from_dict(cls, data):
        if "usages" in data.keys():
            data["usages"] = list(map(CommandUsage.from_dict, data["usages"]))
        return cls(**data)

    def __eq__(self, other):
        if not isinstance(other, CommandStats):
            return False
        return (
            self.usages == other.usages
            and self.unique_users == other.unique_users
            and self.total_cmds == other.total_cmds
        )


class StreamWrapperStorer:
    stream: [io.StringIO]
    reading: [io.StringIO]  # must have a readline() function

    def __init__(self, stream, reading):
        self.stream = stream
        self.reading = reading

    def writeStats(self, stats: CommandStats):
        self.stream.write(str(stats))

    def return_stats(self):
        # assume the stats object is in ONE LINE (not multiple)
        return CommandStats.from_dict(json.loads(self.reading.readline()))

    def close(self):
        self.stream.close()
