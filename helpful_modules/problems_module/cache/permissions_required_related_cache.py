"""

This is used for permissions required cache
Because there are only a finite amount of permissions needed, this internally uses a JSON file instead of a SQL Database

This uses config.json.

The dict in the permissions_needed key should not be modified.

Also, most of the logic is delegated either to UserDataRequiredCache or AsyncFileReader


Of course, this is licensed under the GPLv3.

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

        await self.update_cache()
        if "trusted" in permissions_required.keys():
            if (
                await self.get_user_data(
                    user_id, default=UserData.default(user_id=user_id)
                )
            ).trusted != permissions_required["trusted"]:
                return False

        if "denylisted" in permissions_required.keys():
            if (
                (
                    await self.get_user_data(
                        user_id, default=UserData.default(user_id=user_id)
                    )
                )
            ).denylisted != permissions_required["denylisted"]:
                return False

        for key, val in permissions_required.items():
            try:
                if self.cached_user_data[user_id].to_dict()[key] != val:
                    return False
            except KeyError:
                pass

        return True

    async def initialize_sql_table(self) -> None:
        """Initialize file dictionary from config.json."""
        await super().initialize_sql_table()
        await self._async_file_dict.read_from_file()