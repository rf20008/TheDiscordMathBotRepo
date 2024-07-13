"""
The Discord Math Problem Bot Repo - GuildData
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
import json

import disnake

from ..errors import InvalidDictionaryInDatabaseException
from .the_basic_check import CheckForUserPassage
from ..denylistable import Denylistable

class GuildData(Denylistable):
    denylisted: bool
    guild_id: int | None
    can_create_problems_check: CheckForUserPassage
    can_create_quizzes_check: CheckForUserPassage
    mods_check: CheckForUserPassage
    denylist_reason: str
    denylist_expiry: float = 0.0
    def __init__(
        self,
        guild_id: int | None,
        denylisted: bool,
        can_create_problems_check: str | CheckForUserPassage,
        can_create_quizzes_check: str | CheckForUserPassage,
        mods_check: str | CheckForUserPassage,
        denylist_reason: str = "",
        denylist_expiry: float = 0.0
    ):
        """
        Do not instantiate this manually! The `py:class:MathProblemCache` will do it for you.
        Parameters
        ----------
        guild_id : int
            The ID of the guild that this `GuildData` is attached to.
        denylisted : bool
            Whether this guild is denylisted. If this is not found in the database , then it will be `False` by default
        can_create_quizzes_check : str
            This is a JSON representation of the `py:class:CheckForUserPassage` to check whether a user can create quizzes.
            Defaults to allowing everyone to create quizzes.
        can_create_problems_check: str
            This is a JSON representation of the `py:class:CheckForUserPassage`

            used to check whether users can create problems - defaulting to everyone!
        mods_check : str
            This is a JSON representation of the `py:class:CheckForUserPassage` used
            to check whether someone is a moderator and can do mod commands with the bot.
            Defaults to requiring administrator permissions.
        denylist_reason : str
            This is the reason why this guild is denylisted (if applicable)
        denylist_expiry : float
            the Unix time when this guild will become undenylisted (if applicable)
        an instance of py:class:MathProblemCache which is internally used for internal state (but it's not used in this current version)


        Raises
        ---------
        InvalidDictionaryInDatabaseException
            This exception would be raised if `can_create_quizzes_check`, `can_create_problems_check`, or `mods_check` could not be parsed into JSON
        """
        # self.cache = cache
        if not isinstance(guild_id, int) and guild_id is not None:
            raise TypeError(
                f"I expected `guild_id` to be an int, but I got a {guild_id.__class__.__name__} instead!"
            )
        self.guild_id = guild_id
        if not isinstance(denylisted, bool):
            raise TypeError(
                f"I expected `denylisted` to be a bool, but I got a(n) {denylisted.__class__.__name__} instead!"
            )
        self.denylisted = denylisted
        if isinstance(can_create_quizzes_check, str):
            try:
                self.can_create_problems_check = CheckForUserPassage.from_dict(
                    json.loads(can_create_problems_check)
                )
            except json.JSONDecodeError as exc:
                raise InvalidDictionaryInDatabaseException.from_invalid_data(
                    can_create_problems_check
                ) from exc
            except KeyError as exc:
                raise InvalidDictionaryInDatabaseException(
                    f"I was able to parse {can_create_problems_check} into a dictionary, but I couldn't find the key called {str(exc)}!"
                ) from exc
        else:
            self.can_create_quizzes_check = can_create_quizzes_check
        if isinstance(can_create_problems_check, str):
            try:
                self.can_create_quizzes_check = CheckForUserPassage.from_dict(
                    json.loads(can_create_quizzes_check)
                )
            except json.JSONDecodeError as exc:
                raise InvalidDictionaryInDatabaseException.from_invalid_data(
                    can_create_quizzes_check
                ) from exc
            except KeyError as exc:
                raise InvalidDictionaryInDatabaseException(
                    f"I was able to parse {can_create_quizzes_check} into a dictionary, but I couldn't find the key called {str(exc)}!"
                ) from exc
        else:
            self.can_create_problems_check = can_create_problems_check

        if isinstance(mods_check, str):
            try:
                self.mods_check = CheckForUserPassage.from_dict(json.loads(mods_check))
            except json.JSONDecodeError as exc:
                raise InvalidDictionaryInDatabaseException.from_invalid_data(
                    mods_check
                ) from exc
            except KeyError as exc:
                raise InvalidDictionaryInDatabaseException(
                    f"I was able to parse {mods_check} into a dictionary, but I couldn't find the key called {str(exc)}!"
                ) from exc
        else:
            self.mods_check = mods_check
        if not isinstance(denylist_expiry, float):
            raise TypeError("denylist_expiry is not a float")
        self.denylist_expiry=denylist_expiry
        if not isinstance(denylist_reason, str):
            raise TypeError("denylist_reason is not a str")
        self.denylist_reason = denylist_reason
    @classmethod
    def default(cls, guild_id: int):
        return GuildData(
            guild_id=guild_id,
            denylisted=False,
            can_create_quizzes_check=CheckForUserPassage(
                denylisted_users=[],
                allowlisted_users=[],
                roles_allowed=[guild_id],
                permissions_needed=[],
            ),
            can_create_problems_check=CheckForUserPassage(
                denylisted_users=[],
                allowlisted_users=[],
                roles_allowed=[guild_id],
                permissions_needed=["administrator"],
            ),
            mods_check=CheckForUserPassage(
                denylisted_users=[],
                allowlisted_users=[],
                roles_allowed=[],
                permissions_needed=["administrator"],
            ),
            denylist_reason="",
            denylist_expiry=float('-inf')
        )

    @classmethod
    def from_dict(cls, data: dict) -> "GuildData":
        return cls(
            denylisted=bool(data["denylisted"]),
            guild_id=data["guild_id"],
            can_create_problems_check=data["can_create_problems_check"],
            mods_check=data["mod_check"],
            can_create_quizzes_check=data["can_create_quizzes_check"],
            denylist_reason=data.get('denylist_reason', ""),
            denylist_expiry=data.get('denylist_expiry', float('-inf'))
        )

    def to_dict(self) -> dict:
        dict_to_return = {
            "denylisted": int(self.denylisted),
            "guild_id": self.guild_id,
            "can_create_problems_check": self.can_create_problems_check.to_dict(),
            "can_create_quizzes_check": self.can_create_quizzes_check.to_dict(),
            "mods_check": self.mods_check.to_dict(),
            "denylist_reason": self.denylist_reason,
            "denylist_expiry": self.denylist_expiry
        }

        return dict_to_return
