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


This is used for permissions required cache
Because there are only a finite amount of permissions needed, this internally uses a JSON file instead of a SQL Database

This uses config.json.

The dict in the permissions_needed key should not be modified.

Also, most of the logic is delegated either to UserDataRequiredCache or AsyncFileReader

Of course, this is licensed under the AGPLv3.

"""


import typing

from ...FileDictionaryReader import AsyncFileDict
from ..user_data import UserData
from .user_data_related_cache import UserDataRelatedCache


class PermissionsRequiredRelatedCache(UserDataRelatedCache):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._async_file_dict = AsyncFileDict("config.json")

    async def get_permissions_required_for_command(
        self, command_name
    ) -> typing.Dict[str, bool]:
        await self._async_file_dict.read_from_file()
        return self._async_file_dict.dict["permissions_required"][command_name]

    async def user_meets_permissions_required_to_use_command(
        self,
        user_id: int,
        permissions_required: typing.Optional[typing.Dict[str, bool]] = None,
        command_name: str | None = None,
    ) -> bool:
        """Return whether the user meets permissions required to use the command"""
        if permissions_required is None:
            permissions_required = await self.get_permissions_required_for_command(
                command_name
            )

        user_data = await self.get_user_data(user_id)
        if "trusted" in permissions_required.keys():
            if user_data.trusted != permissions_required["trusted"]:
                return False

        if "denylisted" in permissions_required.keys():
            if user_data.is_denylisted() != permissions_required["denylisted"]:
                return False
        UDTD = user_data.to_dict()
        for key, val in permissions_required.items():
            try:

                if key != 'denylisted' and UDTD[key] != val: # we have to treat 'denylisted` specially
                    return False
            except KeyError:
                pass

        return True

    async def initialize_sql_table(self) -> None:
        """Initialize file dictionary from config.json."""
        await super().initialize_sql_table()
        if not hasattr(self, "_async_file_dict"):
            self._async_file_dict = AsyncFileDict("config.json")
        await self._async_file_dict.read_from_file()
