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

import aiomysql
import aiosqlite
import orjson

from ..errors import SQLException, VerificationCodeInfoNotFound
from ..mysqlcontextmanager import mysql_connection
from ..verification_code_info import VerificationCodeInfo
from .appeals_related_cache import AppealsRelatedCache
from ...dict_factory import dict_factory

class VerificationCodesRelatedCache(AppealsRelatedCache):

    async def initialize_sql_table(self) -> None:
        await super().initialize_sql_table()
        await self.run_sql(
            """CREATE TABLE IF NOT EXISTS verification_code_infos(
            user_id INT PRIMARY KEY,
            hashed_verification_code BLOB,
            salt BLOB,
            expiry DOUBLE,
            created_at DOUBLE
            
        )""")

    async def set_verification_code_info(self, code_info: VerificationCodeInfo):
        if not isinstance(code_info, VerificationCodeInfo):
            raise TypeError(
                f"code_info is not a VerificationCodeInfo, but an instance of {code_info.__class__.__name__}"
            )

        if self.use_sqlite:
            async with aiosqlite.connect(self.db) as conn:
                cursor = await conn.cursor()
                await cursor.execute(
                    "INSERT OR REPLACE INTO verification_code_infos (user_id, hashed_verification_code, salt, expiry, created_at) VALUES (?, ?, ?, ?, ?)",
                    (
                        code_info.user_id,
                        code_info.hashed_verification_code,
                        code_info.salt,
                        code_info.expiry,
                        code_info.created_at,
                    ),
                )
                await conn.commit()
        else:
            async with mysql_connection(
                host=self.mysql_db_ip,
                password=self.mysql_password,
                user=self.mysql_username,
                database=self.mysql_db_name,
            ) as conn:
                cursor = await conn.cursor()
                await cursor.execute(
                    """INSERT INTO verification_code_infos (user_id, hashed_verification_code, salt, expiry, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    hashed_verification_code=VALUES(hashed_verification_code),
                    salt=VALUES(salt),
                    expiry=VALUES(expiry),
                    created_at=VALUES(created_at)""",
                    (
                        code_info.user_id,
                        code_info.hashed_verification_code,
                        code_info.salt,
                        code_info.expiry,
                        code_info.created_at,
                    ),
                )
                await conn.commit()

    async def get_verification_code_info(self, user_id: int):
        if not isinstance(user_id, int):
            raise TypeError(
                f"user_id is not an int, but an instance of {user_id.__class__.__name__} and is {user_id}"
            )
        if self.use_sqlite:
            async with aiosqlite.connect(self.db) as conn:
                conn.row_factory = dict_factory
                cursor = await conn.cursor()
                await cursor.execute(
                    "SELECT * FROM verification_code_infos WHERE user_id = ?",
                    (user_id,),
                )
                results = list(await cursor.fetchall())
        else:
            async with mysql_connection(
                host=self.mysql_db_ip,
                password=self.mysql_password,
                user=self.mysql_username,
                database=self.mysql_db_name,
            ) as conn:
                cursor = await conn.cursor(aiomysql.DictCursor)
                await cursor.execute(
                    "SELECT * from verification_code_infos WHERE user_id=%s", (user_id,)
                )
                results = list(await cursor.fetchall())
        if len(results) == 0:
            raise VerificationCodeInfoNotFound(
                f"The user with id {user_id} has no verification code info"
            )
        elif len(results) == 1:

            return VerificationCodeInfo(
                user_id=results[0]["user_id"],
                hashed_verification_code=results[0]["hashed_verification_code"],
                salt=results[0]["salt"],
                expiry=results[0]["expiry"],
                created_at=results[0]["created_at"],
            )
        else:
            raise SQLException(
                f"The user with id {user_id} has {len(results)} verification code infos; only 1 is expected"
            )
    async def delete_verification_code_info(self, user_id: int):
        if not isinstance(user_id, int):
            raise TypeError(
                f"user_id is not an int, but an instance of {user_id.__class__.__name__} and is {user_id}"
            )
        if self.use_sqlite:
            async with aiosqlite.connect(self.db) as conn:
                cursor = await conn.cursor()
                await cursor.execute("DELETE FROM verification_code_infos WHERE user_id = ?", (user_id,))
                await conn.commit()
        else:
            async with mysql_connection(
                    host=self.mysql_db_ip,
                    password=self.mysql_password,
                    user=self.mysql_username,
                    database=self.mysql_db_name,
            ) as conn:
                cursor = await conn.cursor()
                await cursor.execute("DELETE FROM verification_code_infos WHERE user_id = %s", (user_id,))
                await conn.commit()
