"""
Copyright (c) Samuel Guo 2024-present
You can distribute any version of the Software created and distributed *before* 23:17:55.00 July 28, 2024 UTC-4
under the GNU General Public License version 3 or at your option, any  later option.
But versions of the code created and/or distributed *on or after* that date must be distributed
under the GNU *Affero* General Public License, version 3, or, at your option, any later version.

(Since this specific file was created after 23:17:55.00 July 28, 2024 GMT-4,
all versions of the Software containing this file must be licensed under the GNU *Affero* General Public License,
version 3, or at your option, any later version.)

The Discord Math Problem Bot Repo - Custom Bot

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License
as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License along with this program.
If not, see <https://www.gnu.org/licenses/>.

Author: Samuel Guo (64931063+rf20008@users.noreply.github.com)"""
from .FileDictionaryReader import AsyncFileDict
import abc
import time
import orjson
import aiofiles
import asyncio
import math
import farmhash


def frac(x):
    return x - math.floor(x)


# that is from ChatGPT
async def read_last_n_lines(filename, n):
    if n < 0:
        async with aiofiles.open(filename, "rb") as f:
            lines = await f.readlines()
        return lines
    async with aiofiles.open(filename, 'rb') as f:
        # Move to the end of the file
        await f.seek(0, 2)
        position = await f.tell()
        lines = []
        current_line = []

        # Read backwards until we find the last n lines
        while position >= 0 and len(lines) < n:
            await f.seek(position)
            char = await f.read(1)

            # Check for newline character
            if char == b'\n' and current_line:
                # Store the completed line
                lines.append(current_line[::-1].decode())
                current_line = []
            else:
                current_line.append(char)

            position -= 1

        # Capture the last line if it does not end with a newline
        if current_line:
            lines.append(current_line[::-1].decode())

        # Reverse the lines to get them in the correct order
        return lines[::-1][:n]


class AuditLog:
    buffer: list
    max_buffer_size: int

    @abc.abstractmethod
    def add_log_entry(self, log_entry: str, priority: int = 3, extra_info: dict | None = None):
        if extra_info is None:
            extra_info = dict()
        if not isinstance(extra_info, dict):
            raise TypeError("extra info is not a dict")
        if not isinstance(priority, int):
            raise TypeError("Priority is not an int")
        if not isinstance(log_entry, str):
            raise TypeError("Log entry is not a string")
        raise NotImplementedError("Subclasses must implement this method!")

    @abc.abstractmethod
    async def clear_buffer(self):
        pass

    @abc.abstractmethod
    async def read_from_log(self, n: int = -1):
        pass

    async def add_log_entry_with_clear(self, log_entry: str, priority: int = 3, extra_info: dict | None = None):
        self.add_log_entry(log_entry, priority, extra_info)
        if len(self.buffer) >= self.max_buffer_size:
            await self.clear_buffer()


class FileLog(AuditLog):
    log: AsyncFileDict

    def __init__(self, filename: str, max_buffer_size: int = 200, overwrite: bool = False):
        if overwrite:
            with open(filename, "w") as _:
                pass
        self.filename = filename
        self.buffer = []
        self.max_buffer_size = max_buffer_size
        self.lock = asyncio.Lock()

    def add_log_entry(self, log_entry: str, priority: int = 3, extra_info: dict | None = None):
        if extra_info is None:
            extra_info = dict()
        if not isinstance(extra_info, dict):
            raise TypeError("extra info is not a dict")
        if not isinstance(priority, int):
            raise TypeError("Priority is not an int")
        if not isinstance(log_entry, str):
            raise TypeError("Log entry is not a string")
        if '\n' in log_entry:
            raise ValueError("Log entries must not contain newlines")
        if '|' in log_entry:
            raise ValueError("Log entries must not contain pipe characters")
        cur_time = time.asctime(time.localtime())
        self.buffer.append((cur_time, log_entry, priority, extra_info))

    async def clear_buffer(self):
        async with self.lock:
            things = "\n".join(
                [f"[{cur_time} | {priority}]: {log_entry} | {extra_info}" for cur_time, log_entry, priority, extra_info
                 in self.buffer])
            async with aiofiles.open(self.filename, "a") as file:
                await file.write(f"{things}\n")
            self.buffer.clear()

    async def read_from_log(self, num_last_lines: int = -1):

        if num_last_lines == -1:
            async with self.lock:
                async with aiofiles.open(self.filename, "r") as file:
                    async for line in file:
                        yield line
            return

        async for line in read_last_n_lines(self.filename, num_last_lines):
            yield line


class FileDictLog(AuditLog):
    log: AsyncFileDict

    def __init__(self, filename: str, overwrite: bool = False, max_buffer_size: int = 200):
        self.log = AsyncFileDict(filename, overwrite=overwrite)
        self.buffer = []  # Initialize the buffer
        self.max_buffer_size = max_buffer_size

    def add_log_entry(self, log_entry: str, priority: int = 3, extra_info: dict | None = None):
        if extra_info is None:
            extra_info = {}
        if not isinstance(extra_info, dict):
            raise TypeError("extra_info is not a dict")
        if not isinstance(log_entry, str):
            raise TypeError("Log entry is not a string")

        cur_time = time.asctime(time.localtime())
        cur_time_hashed = hex(farmhash.FarmHash128(str(cur_time) + str(frac(time.time()))))

        self.buffer.append((cur_time + cur_time_hashed, {
            "cur_time": cur_time,
            "log_msg": log_entry,
            "priority": priority,
            "extra_info": extra_info
        }))

    async def clear_buffer(self):
        if not self.buffer:  # Check if buffer is empty
            return

        await self.log.read_from_file()
        old_dict = self.log.dict
        old_dict.update(dict(self.buffer))  # Update the old dictionary with the new logs
        await self.log.update_my_file()  # Ensure this method is defined in AsyncFileDict
        self.buffer.clear()  # Clear the buffer after updating

    async def read_from_log(self, n: int = -1):
        # read the entire file
        await self.log.update_my_file()
        await self.log.read_from_file()
        entries = []
        if n == -1:
            n = len(self.log.items()) + 1
        for key, value in self.log.items():
            entries.append(value)
        cur_time = time.time()
        entries.sort(key=lambda entry: cur_time - time.mktime(time.strptime(entry["timestamp"])))  # type: ignore
        return entries[:n]


class AppendingFileLog(AuditLog):
    def __init__(self, filename: str, overwrite: bool = False, max_buffer_size=1):
        self.buffer = []
        self.max_buffer_size = max_buffer_size
        self.filename = filename
        if overwrite:
            with open(filename, "w"):
                pass

    @staticmethod
    def encode_log_entry(log_entry: str) -> str:
        return log_entry.replace("\\", "\\\\").replace("\n", "\\n").replace("\t", "\\t")

    @staticmethod
    def decode_log_entry(encoded_entry: str) -> str:
        return encoded_entry.replace("\\t", "\t").replace("\\n", "\n").replace("\\\\", "\\")

    async def read_last_n_lines(self, n: int = -1) -> list[str]:
        return await read_last_n_lines(self.filename, n)

    def format_entry(self, log_entry: str, priority: int = 3, extra_info: dict | None = None):
        timestamp = time.asctime(time.localtime())
        if extra_info is None:
            parsed_extra_info = "{}"
        else:
            parsed_extra_info = orjson.dumps(extra_info)
        encoded_extra_info = self.encode_log_entry(parsed_extra_info)
        return f"{timestamp} | {priority} | {self.encode_log_entry(log_entry)} | {encoded_extra_info}"

    def parse_entry(self, entry: str) -> tuple[time.struct_time, int, str, dict]:
        # step 1: extract timestamp
        first_pipe = entry.find("|")
        timestamp: time.struct_time = time.strptime(entry[:first_pipe - 1])  # type: ignore # the space!!
        if first_pipe == -1:
            raise ValueError("Malformed log entry -- log entries must have at least 2 pipe characters")
        # step 2: extract priority
        second_pipe = entry.find("|", first_pipe + 1)
        if second_pipe == -1:
            raise ValueError("Malformed log entry. Log entries must have at least 2 pipes")
        priority = int(entry[first_pipe + 1:second_pipe])
        # step 3: extract log entry
        # step 3a: find where log_entry ends!
        third_pipe = self.find_unescaped_pipe(entry, second_pipe + 1)
        log_entry = self.decode_log_entry(entry[second_pipe + 1:third_pipe - 1])
        extra_info = orjson.loads(self.decode_log_entry(entry[third_pipe + 1:]))
        return timestamp, priority, log_entry, extra_info

    @staticmethod
    def find_unescaped_pipe(string: str, start: int = 0):
        if start >= len(string):
            return -1
        if string[start] == '|':
            return start

        i = start
        while i < len(string):
            i += 1
            if string[i] == '|' and string[i - 1] != "\\":
                return i
        return -1

    def add_log_entry(self, log_entry: str, priority: int = 3, extra_info: dict | None = None):
        self.buffer.append(self.format_entry(log_entry=log_entry, priority=priority, extra_info=extra_info))

    async def clear_buffer(self):
        to_add = "\n".join(self.buffer)
        async with open(self.filename, 'a') as file:
            file.write(to_add)
        self.buffer.clear()

    async def add_log_entry_with_clear(self, log_entry: str, priority: int = 3, extra_info: dict | None = None):
        self.add_log_entry(log_entry, priority, extra_info)
        if len(self.buffer) >= self.max_buffer_size:
            await self.clear_buffer()

    async def read_from_log(self, n: int = -1):
        last_n_lines = await read_last_n_lines(self.filename, n)
        return list(map(self.decode_log_entry, last_n_lines))
