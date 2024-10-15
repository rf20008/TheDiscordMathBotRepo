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
import time
import aiofiles
import asyncio
import math
import farmhash
frac = lambda x: x - math.floor(x)

# that is from ChatGPT
async def read_last_n_lines(filename, n):
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


class FileLog:
    log: AsyncFileDict
    def __init__(self, filename: str, max_buffer_size: int = 200, overwrite: bool = False):
        if overwrite:
            with open(filename, "w") as file:
                pass
        self.filename = filename
        self.buffer = []
        self.max_buffer_size = max_buffer_size
        self.lock = asyncio.Lock()

    def add_log_entry(self, log_entry: str):
        if not isinstance(log_entry, str):
            raise TypeError("Log entry is not a string")
        if '\n' in log_entry:
            raise ValueError("Log entries must not contain newlines")
        cur_time = time.asctime(time.localtime())
        self.buffer.append((cur_time, log_entry))

    async def add_log_entry_with_buffer_clear(self, log_entry: str):
        self.add_log_entry(log_entry)
        if len(self.buffer) > self.max_buffer_size:
            await self.clear_buffer()
    async def clear_buffer(self):
        async with self.lock:
            things = "\n".join([f"[{cur_time}]: {log_entry}" for cur_time, log_entry in self.buffer])
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

class FileDictLog:
    log: AsyncFileDict

    def __init__(self, filename: str, overwrite: bool = False, max_buffer_size: int = 200):
        self.log = AsyncFileDict(filename, overwrite=overwrite)
        self.buffer = []  # Initialize the buffer
        self.max_buffer_size = max_buffer_size

    async def add_log_entry(self, log_entry: str, priority: int = 3, extra_info: dict | None = None):
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

        if len(self.buffer) > self.max_buffer_size:
            await self.clear_buffer()

    async def clear_buffer(self):
        if not self.buffer:  # Check if buffer is empty
            return

        await self.log.read_from_file()
        old_dict = self.log.dict
        old_dict.update(dict(self.buffer))  # Update the old dictionary with the new logs
        await self.log.update_my_file()  # Ensure this method is defined in AsyncFileDict
        self.buffer.clear()  # Clear the buffer after updating
