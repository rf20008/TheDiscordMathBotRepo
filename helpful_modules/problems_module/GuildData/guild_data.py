import json

import disnake

from ..errors import InvalidDictionaryInDatabaseException
from .the_basic_check import CheckForUserPassage


class GuildData:
    blacklisted: bool
    guild_id: int | None
    can_create_problems_check: CheckForUserPassage
    can_create_quizzes_check: CheckForUserPassage
    mods_check: CheckForUserPassage



    def __init__(
        self,
        guild_id: int | None,
        blacklisted: bool,
        can_create_problems_check: str | CheckForUserPassage,
        can_create_quizzes_check: str | CheckForUserPassage,
        mods_check: str | CheckForUserPassage,
    ):
        """
        Do not instantiate this manually! The `py:class:MathProblemCache` will do it for you.
        Parameters
        ----------
        guild_id : int
            The ID of the guild that this `GuildData` is attached to.
        blacklisted : bool
            Whether this guild is blacklisted. If this is not found in the database , then it will be `False` by default
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
        if not isinstance(blacklisted, bool):
            raise TypeError(
                f"I expected `blacklisted` to be an int, but I got a {guild_id.__class__.__name__} instead!"
            )
        self.blacklisted = blacklisted
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
            self.can_create_problems_check=can_create_problems_check

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
            self.mods_check=mods_check

    @classmethod
    def default(cls, guild_id: int):
        return GuildData(
            guild_id=guild_id,
            blacklisted=False,
            can_create_quizzes_check=CheckForUserPassage(
                blacklisted_users=[],
                whitelisted_users=[],
                roles_allowed=[guild_id],
                permissions_needed=[]
            ),
            can_create_problems_check=CheckForUserPassage(
                blacklisted_users=[],
                whitelisted_users=[],
                roles_allowed=[guild_id],
                permissions_needed=["administrator"]
            ),
            mods_check=CheckForUserPassage(
                blacklisted_users=[],
                whitelisted_users=[],
                roles_allowed=[],
                permissions_needed=["administrator"]
            )

        )
    @classmethod
    def from_dict(cls, data: dict) -> "GuildData":
        return cls(
            blacklisted=bool(data["blacklisted"]),
            guild_id=data["guild_id"],
            can_create_problems_check=data["can_create_problems_check"],
            mods_check=data["mod_check"],
            can_create_quizzes_check=data["can_create_quizzes_check"],
        )

    def to_dict(self) -> dict:
        dict_to_return = {
            "blacklisted": int(self.blacklisted),
            "guild_id": self.guild_id,
            "can_create_problems_check": self.can_create_problems_check.to_dict(),
            "can_create_quizzes_check": self.can_create_quizzes_check.to_dict(),
            "mods_check": self.mods_check.to_dict(),
        }

        return dict_to_return
