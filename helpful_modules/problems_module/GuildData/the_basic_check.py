import typing as t

import disnake
import orjson


class CheckForUserPassage:
    def __init__(
        self,
        blacklisted_users: t.List[int],
        whitelisted_users: t.List[int],
        roles_allowed: t.List[int],
        permissions_needed: t.List[str],
    ):
        self.blacklisted_users = blacklisted_users
        self.whitelisted_users = whitelisted_users
        self.roles_allowed = roles_allowed
        self.permissions_needed = permissions_needed

    def check_for_user_passage(self, member: disnake.Member) -> bool:
        "Return whether the user passes this check. First we check for blacklisted/whitelisted people. Then roles and permissions are checked. If none of those checks succeed, False is returned. Otherwise True is returned"
        if member.id in self.blacklisted_users:
            return False
        if member.id in self.whitelisted_users:
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
            blacklisted_users=data["blacklisted_users"],
            permissions_needed=data["permissions_needed"],
            roles_allowed=data["roles_needed"],
            whitelisted_users=data["whitelisted_users"],
        )

    def to_dict(self):
        "Convert myself to a dictionary"
        return {
            "blacklisted_users": self.blacklisted_users,
            "whitelisted_users": self.whitelisted_users,
            "roles_allowed": self.roles_allowed,
            "permissions_needed": self.permissions_needed,
        }
