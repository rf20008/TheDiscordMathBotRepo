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
import typing as t

import disnake
import orjson


class CheckForUserPassage:
    def __init__(
        self,
        denylisted_users: t.List[int],
        allowlisted_users: t.List[int],
        roles_allowed: t.List[int],
        permissions_needed: t.List[str],
    ):
        self.denylisted_users = denylisted_users
        self.allowlisted_users = allowlisted_users
        self.roles_allowed = roles_allowed
        self.permissions_needed = permissions_needed

    def check_for_user_passage(self, member: disnake.Member) -> bool:
        "Return whether the user passes this check. First we check for denylisted/allowlisted people. Then roles and permissions are checked. If none of those checks succeed, False is returned. Otherwise True is returned"
        if member.id in self.denylisted_users:
            return False
        if member.id in self.allowlisted_users:
            return True

        role_ids_of_this_user: set = {
            role.id for role in member.roles
        }  # Create a list containing the ids of the member's roles
        roles_allowed: set = set(self.allowed_roles)
        if (
            role_ids_of_this_user.intersection(roles_allowed) != set()
        ):  # This user has at least 1 of the allowed roles
            return True
        if not self.permissions_needed:
            return True
        _permissions_needed_dict = dict.fromkeys(self.permissions_needed, True)

        all_permissions_needed = disnake.Permissions(
            **_permissions_needed_dict
        )  # Create the Permissions instance based on what permissions are required

        if member.guild_permissions.is_superset(all_permissions_needed):
            return True

        return False

    @classmethod
    def from_dict(cls, data: dict) -> "CheckForUserPassage":
        "Convert a dictionary into an instance of CheckForUserPassage"
        return cls(
            denylisted_users=data["denylisted_users"],
            permissions_needed=data["permissions_needed"],
            roles_allowed=data["roles_allowed"],
            allowlisted_users=data["allowlisted_users"],
        )

    def to_dict(self):
        "Convert myself to a dictionary"
        return {
            "denylisted_users": self.denylisted_users,
            "allowlisted_users": self.allowlisted_users,
            "roles_allowed": self.roles_allowed,
            "permissions_needed": self.permissions_needed,
        }
