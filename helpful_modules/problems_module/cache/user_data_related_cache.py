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
import logging
import sqlite3
import typing
import warnings
from copy import copy, deepcopy
from types import FunctionType
from typing import *

import aiosqlite
import disnake

from helpful_modules.dict_factory import dict_factory

from ..errors import *
from ..mysql_connector_with_stmt import mysql_connection
from ..user_data import UserData
from .quiz_related_cache import QuizRelatedCache

log = logging.getLogger(__name__)


class UserDataRelatedCache(QuizRelatedCache):
    def __str__(self):
        raise RuntimeError("I don't want to be string-ified")

    async def get_user_data(
        self, user_id: int, default: typing.Optional[UserData] | str = None
    ):
        log.debug(
            f"get_user_data method called. user_id: {user_id}, default: {default}"
        )
        assert isinstance(user_id, int)
        assert (
            isinstance(default, UserData) or default is None or isinstance(default, str)
        )
        if default is None:
            default = UserData.default(user_id=user_id)
            # To avoid mutable default arguments
        if self.use_sqlite:
            async with aiosqlite.connect(self.db_name) as conn:
                conn.row_factory = dict_factory
                cursor = await conn.cursor()
                await cursor.execute(
                    "SELECT * FROM user_data WHERE user_id = ?", (user_id,)
                )  # Select the data
                cursor_results = list(await cursor.fetchall())
                log.debug(f"Data selected (results: {cursor_results})")
                if len(cursor_results) == 0:
                    return default
                elif len(cursor_results) == 1:
                    dict_to_use = cursor_results[0]
                    dict_to_use["trusted"] = bool(dict_to_use["trusted"])
                    dict_to_use["denylisted"] = bool(dict_to_use["denylisted"])
                    dict_to_use["user_id"] = int(dict_to_use["user_id"])
                    log.debug("Data successfully returned!")
                    return UserData.from_dict(dict_to_use)
                else:
                    raise TooMuchUserDataException(
                        f"Too much user data; found {len(cursor_results)} results, but only 0 or 1 results are expected."
                        f"Results: {cursor_results}"
                    )
        else:
            with mysql_connection(
                host=self.mysql_db_ip,
                password=self.mysql_password,
                user=self.mysql_username,
                database=self.mysql_db_name,
            ) as connection:
                log.debug("Connected to MySQL")
                cursor = connection.cursor(dictionaries=True)
                cursor.execute(
                    "SELECT * FROM user_data WHERE user_id=%s",
                    (user_id,),  # TODO: fix placeholders
                )
                results = list(cursor.fetchall())
                if len(results) == 0:
                    return default
                elif len(results) == 1:
                    results[0]["user_id"] = results[0]["USER_ID"]
                    return UserData.from_dict(results[0])
                else:
                    try:
                        raise TooMuchUserDataException(
                            f"Too much user data; found {len(results)} results, but only 0 or 1 results are expected."
                        )
                    except NameError:
                        raise TooMuchUserDataException("Too much user data found!")

    async def set_user_data(self, user_id: int, new: UserData) -> None:
        """Set the user_data of a user."""
        assert isinstance(user_id, int)
        assert isinstance(new, UserData)
        if self.use_sqlite:
            async with aiosqlite.connect(self.db_name) as conn:
                log.debug("Connected to SQLite!")
                conn.row_factory = dict_factory
                denylisted_int = int(new.denylisted)
                trusted_int = int(new.trusted)
                cursor = await conn.cursor()
                await cursor.execute(
                    "INSERT OR REPLACE INTO user_data (user_id, denylisted, trusted, denylist_reason, denylist_expiry, verification_code_denylist) VALUES (?, ?, ?, ?, ?, ?)",
                    (user_id, denylisted_int, trusted_int, new.denylist_reason, new.denylist_expiry, new.verification_code_denylist),
                )
                await conn.commit()
                log.debug("Finished!")
        else:
            with mysql_connection(
                host=self.mysql_db_ip,
                password=self.mysql_password,
                user=self.mysql_username,
                database=self.mysql_db_name,
            ) as connection:
                log.debug("Connected to MySQL")
                cursor = connection.cursor(dictionaries=True)
                cursor.execute(
                    """INSERT OR REPLACE INTO user_data (user_id, denylisted, trusted, denylist_reason, denylist_expiry, verification_code_denylist) VALUES (%s, %s, %s, %s, %s, %s)""",
                    (user_id, new.trusted, new.denylisted, new.denylist_reason, new.denylist_expiry, new.verification_code_denylist),
                )
                connection.commit()
                log.debug("Finished!")
                return

    async def del_user_data(self, user_id: int):
        """Delete user data given the user id"""
        assert isinstance(user_id, int)
        if self.use_sqlite:
            async with aiosqlite.connect(self.db_name) as conn:
                cursor = await conn.cursor()
                await cursor.execute(
                    "DELETE FROM user_data WHERE user_id = ?", (user_id,)
                )
                await conn.commit()
        else:
            with mysql_connection(
                host=self.mysql_db_ip,
                password=self.mysql_password,
                user=self.mysql_username,
                database=self.mysql_db_name,
            ) as connection:
                cursor = connection.cursor(dictionaries=True)
                cursor.execute("DELETE FROM user_data WHERE user_id = %s", (user_id,))
                connection.commit()
                connection.close()

    async def initialize_sql_table(self) -> None:
        """Initialize SQL tables if they don't exist."""
        if self.use_sqlite:
            async with aiosqlite.connect(self.db_name) as conn:
                cursor = await conn.cursor()
                await cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS user_data (
                        user_id INTEGER PRIMARY KEY,
                        trusted INTEGER,
                        denylisted INTEGER,
                        denylist_reason TEXT,
                        denylist_expiry DOUBLE
                        verfication_code_denylist TEXT
                    )
                """
                )
                await conn.commit()
        else:
            with mysql_connection(
                host=self.mysql_db_ip,
                password=self.mysql_password,
                user=self.mysql_username,
                database=self.mysql_db_name,
            ) as connection:
                cursor = connection.cursor()
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS user_data (
                        user_id INT PRIMARY KEY,
                        trusted BOOLEAN,
                        denylisted BOOLEAN,
                        denylist_reason TEXT,
                        denylist_expiry DOUBLE,
                        verification_code_denylist TEXT
                    )
                """
                )
                connection.commit()
