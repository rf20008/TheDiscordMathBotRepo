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
from typing import Any, Dict, List


class MockableAioFiles:
    """
    A mockable class for asynchronous file operations, intended for unit tests.
    This class can be used as an asynchronous context manager.
    For actual production, please use the real aiofiles.open :)
    Usage Example:
    ```
    async with MockableAioFiles('example.txt', 'w') as mock_file:
        await mock_file.write('This is a mock file.')
    ```

    Attributes:
        file_name (str): The name of the file to be opened.
        mode (str): The mode in which the file is opened.
        args (List): Additional arguments for file opening.
        kwargs (Dict): Additional keyword arguments for file opening.
        file (io.StringIO | io.TextIOBase): The file object.

    Methods:
        __aenter__: Enters the context for file operations.
        __aexit__: Exits the context and ensures proper file closure.
        write: Writes the provided content to the file.
        read_byte: Reads the specified number of bytes from the file.

    Raises:
        RuntimeError: If an attempt is made to enter a context for the same file when it's already open,
                     or if there are issues with file opening, closing, writing, or reading.
        TypeError: If the content provided to the write method is not a string.
    """

    file_name: str
    mode: str
    args: List[Any]
    file: io.StringIO | io.TextIOBase
    kwargs: Dict[str, Any]

    def __init__(self, file_name: str, mode: str = "r", *args, **kwargs):
        self.file_name = file_name
        self.mode = mode
        self.args = args
        self.kwargs = kwargs
        self.file = None

    async def __aenter__(self):
        """
        Enters the context for file operations.

        Raises:
            RuntimeError: If an attempt is made to enter a context for the same file when it's already open,
                         or if there are issues with file opening.
        """
        if self.file:
            raise RuntimeError(
                "Cannot enter a context manager for the same file when it's already open."
            )
        self.file = open(self.file_name, self.mode, *self.args, **self.kwargs)
        return self

    async def __aexit__(self, exc_type=None, exc_value=None, traceback=None):
        """
        Exits the context and ensures proper file closure.

        Raises:
            RuntimeError: If there are issues with file closing.
        """
        if exc_type is not None and exc_value is not None and traceback is not None:
            await self.close()
            raise RuntimeError("I do not know how to deal with this") from exc_value
        if not self.file:
            raise RuntimeError("Cannot close an already closed file.")
        self.file.close()
        self.file = None

    async def write(self, content: str | bytes | bytearray):
        """
        Writes the provided content to the file.

        Args:
            content (str): The content to be written to the file.

        Raises:
            TypeError: If the content is not a string.
            RuntimeError: If there are issues with writing to the file.
            ValueError: If the file is not open in a write or append mode.
        """
        if "b" not in self.mode and not isinstance(content, str):
            raise TypeError("Content is not a string.")
        if "b" in self.mode and not isinstance(content, (bytes, bytearray)):
            raise TypeError("Bytes mode but writing non-bytes characters")
        if not self.file:
            raise RuntimeError("Cannot write to a closed file.")
        if self.mode not in {"w", "a", "wb", "ab"}:
            raise ValueError("File is not open in write or append mode.")
        self.file.write(content)

    async def read(self, size: int = 1) -> str:
        """
        Reads the specified number of bytes from the file.

        Args:
            size (int): The number of bytes to read.

        Returns:
            str: The read content.

        Raises:
            RuntimeError: If there are issues with reading from the file.
            ValueError: If the file is not open in read mode.
        """
        if not self.file:
            raise RuntimeError("Cannot read from a closed file.")
        if self.mode != "r":
            raise ValueError("File is not open in read mode.")
        return self.file.read(size)

    async def readline(self):
        if not self.file:
            raise RuntimeError("Cannot read from a closed file")
        txt = []
        try:
            while len(txt) == 0 or txt[-1] != "\n":
                char = await self.read(1)
                if not char:
                    return "".join(txt)
                txt.append(char)

            return "".join(txt)
        except EOFError:
            return "".join(txt)

    async def readall(self):
        if not self.file:
            raise RuntimeError("Cannot read from a closed file")
        try:
            while True:
                thing = await self.read(1)
                if not thing:
                    break
                    # raise StopIteration("there's nothing to read anymore")
                yield thing
        except EOFError:
            pass

    async def readlines(self):
        if not self.file:
            raise RuntimeError("Cannot read from a closed file")
        try:
            while True:
                line = await self.readline()
                if not line:
                    break
                yield line
        except EOFError:
            pass

    async def close(self):
        """
        Closes the file.

        Raises:
            RuntimeError: If the file is already closed.
        """
        if not self.file:
            raise RuntimeError("Cannot close an already closed file.")
        self.file.close()
        self.file = None

    async def __aiter__(self):
        """
        Allows the class to be an iterable.

        Returns:
            Generator[str]: the iterable object
        """
        async for line in self.readlines():
            yield line
