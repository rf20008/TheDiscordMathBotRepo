"""You can distribute any version of the Software created and distributed *before* 23:17:55.00 July 28, 2024 GMT-4
under the GNU General Public License version 3 or at your option, any  later option.
But versions of the code created and/or distributed *on or after* that date must be distributed
under the GNU *Affero* General Public License, version 3, or, at your option, any later version.

The Discord Math Problem Bot Repo - FileDictionaryReader

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License
as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License along with this program.
If not, see <https://www.gnu.org/licenses/>.

Author: Samuel Guo (64931063+rf20008@users.noreply.github.com)"""
import asyncio
import json
import warnings

import aiofiles

__all__ = ("AsyncFileDict",)


class AsyncFileDict:
    """A class for asynchronously managing JSON data stored in a file."""

    def __init__(self, filename, overwrite=False):
        """
        Initialize the AsyncFileDict.

        Parameters:
        - filename (str): The name of the file to read or write JSON data.
        - overwrite (bool): If True, overwrite the file if it exists.

        """
        self.filename = filename
        self.dict = {}
        if overwrite:
            warnings.warn("`overwrite` calls asyncio.run. Use with caution (since you can only run `asyncio.run` a few times)", category=RuntimeWarning)
            asyncio.run(self.update_my_file())

    async def update_my_file(self):
        """
        Asynchronously update the file with the internal dictionary.

        Returns:
        - None

        """
        async with aiofiles.open(self.filename, "w") as file:
            await file.write(str(json.dumps(self.dict)))

    async def read_from_file(self) -> dict:
        """
        Asynchronously read JSON data from the file into the internal dictionary.

        Returns:
        - dict: The internal dictionary.

        """
        async with aiofiles.open(self.filename, "r") as file:
            stuff = await file.read(-1)
            self.dict = json.loads(stuff)
        return self.dict

    async def get_key(self, key, use_cached=False):
        """
        Asynchronously get the value associated with the given key.

        Parameters:
        - key: The key to retrieve.

        Returns:
        - The value associated with the key.

        """
        if use_cached:
            return self.dict[key]
        return (await self.read_from_file())[key]

    async def set_key(self, key, val, update_file_behind: bool=True):
        """
        Asynchronously set a key-value pair and update the file.

        Parameters:
        - key: The key to set.
        - val: The value to associate with the key.

        Returns:
        - None

        """
        self.dict[key] = val
        if update_file_behind:
            await self.update_my_file()

    async def del_key(self, key, update_file_behind: bool=True):
        """
        Asynchronously delete a key-value pair and update the file.

        Parameters:
        - key: The key to delete.

        Returns:
        - None

        """
        del self.dict[key]
        if update_file_behind:
            await self.update_my_file()

    def __iter__(self):
        """
        Return an iterator for the keys in the internal dictionary. Note: this uses the cached dictionary

        Returns:
        - Iterator for keys.


        """
        return self.dict.__iter__()

    def keys(self):
        """
        Return a view of the keys in the internal dictionary. Note: this uses the cached dictionary

        Returns:
        - View of keys.

        """
        return self.dict.keys()

    def values(self):
        """
        Return a view of the values in the internal dictionary. Note: this uses the cached dictionary

        Returns:
        - View of values.

        """
        return self.dict.items()

    def items(self):
        """
        Return a view of the key-value pairs in the internal dictionary.

        Returns:
        - View of key-value pairs.

        """
        return self.dict.items()
