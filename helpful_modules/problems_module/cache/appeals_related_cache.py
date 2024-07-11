import typing

import aiosqlite
import orjson
from aiomysql import DictCursor

from ...dict_factory import dict_factory
from ..appeal import Appeal, AppealViewInfo
from ..errors import (
    AppealViewInfoNotFound,
    FormatException,
    InvalidDictionaryInDatabaseException,
    SQLException,
)
from ..mysqlcontextmanager import mysql_connection
from .guild_data_related_cache import GuildDataRelatedCache


class AppealsRelatedCache(GuildDataRelatedCache):
    async def set_appeal_data(self, data: Appeal):
        assert isinstance(data, Appeal)  # Basic type-checking
        if self.use_sqlite:
            async with aiosqlite.connect(self.db) as conn:
                cursor = await conn.cursor()
                await cursor.execute(
                    """INSERT OR REPLACE INTO appeals (special_id, appeal_msg, appeal_num, user_id, timestamp,type) 
                    VALUES (?,?,?,?,?,?) 
                    """,
                    (
                        data.special_id,
                        data.appeal_msg,
                        data.appeal_num,
                        data.user_id,
                        data.timestamp,
                        int(data.type),
                    ),
                )  # TODO: test
                await conn.commit()
        else:
            with self.get_a_connection() as connection:
                cursor = await connection.cursor(DictCursor)
                await cursor.execute(
                    """INSERT INTO appeals (special_id, appeal_msg appeal_num, user_id, timestamp,type) 
                    VALUES (%s,%s,%s,%s,%s,%s) 
                    ON DUPLICATE KEY UPDATE 
                    special_id=%s, appeal_msg=%s, appeal_num=%s, user_id=%s, timestamp=%s, type=%s""",
                    (
                        data.special_id,
                        data.appeal_msg,
                        data.appeal_num,
                        data.user_id,
                        data.timestamp,
                        data.type,
                        data.special_id,
                        data.appeal_msg,
                        data.appeal_num,
                        data.user_id,
                        data.timestamp,
                        data.type,
                    ),
                )  # TODO: test

    async def get_appeal(self, special_id: int, default: Appeal) -> Appeal:
        assert isinstance(special_id, int)
        assert isinstance(default, Appeal)

        if self.use_sqlite:
            async with aiosqlite.connect(self.db) as conn:
                conn.row_factory = dict_factory
                cursor = await conn.cursor()
                await cursor.execute(
                    "SELECT * FROM appeals WHERE special_id = ?", (special_id,)
                )
                results = list(await cursor.fetchall())

        else:
            async with self.get_a_connection() as connection:
                cursor = await connection.cursor(DictCursor)

                await cursor.execute(
                    "SELECT * FROM appeals WHERE special_id = %s", (special_id,)
                )
                results = list(await cursor.fetchall())
        if len(results) == 0:
            return default
        elif len(results) == 1:
            return Appeal.from_dict(results[0])
        else:
            raise SQLException(
                "There were too many rows with the same special id in the appeals table!"
            )
    async def get_all_appeals(self):
        if self.use_sqlite:
            async with aiosqlite.connect(self.db) as conn:
                conn.row_factory = dict_factory
                cursor = await conn.cursor()
                await cursor.execute(
                    "SELECT * FROM appeals"
                )
                results = list(await cursor.fetchall())

        else:
            async with self.get_a_connection() as connection:
                cursor = await connection.cursor(DictCursor)

                await cursor.execute(
                    "SELECT * FROM appeals"
                )
                results = list(await cursor.fetchall())

        return [Appeal.from_dict(appeal) for appeal in results]

    async def initialize_sql_table(self) -> None:
        """Initialize SQL table for appeals."""
        await super().initialize_sql_table()
        if self.use_sqlite:
            async with aiosqlite.connect(self.db) as conn:
                cursor = await conn.cursor()
                await cursor.execute(
                    """CREATE TABLE IF NOT EXISTS appeals (
                        special_id INTEGER PRIMARY KEY,
                        appeal_msg TEXT,
                        appeal_num INTEGER,
                        user_id INTEGER,
                        timestamp INTEGER,
                        type INTEGER
                    );"""
                )
                await conn.commit()
                await cursor.execute(
                    """CREATE TABLE IF NOT EXISTS appeal_view_info (
                        message_id INTEGER PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        guild_id INTEGER,
                        done TEXT,
                        pages TEXT,
                        appeal_type INTEGER
                        ); 
                    """
                )
        else:
            async with self.get_a_connection() as connection:
                cursor = await connection.cursor(DictCursor)
                await cursor.execute(
                    """CREATE TABLE IF NOT EXISTS appeals (
                        special_id BIGINT PRIMARY KEY,
                        appeal_msg TEXT,
                        appeal_num INT,
                        user_id BIGINT,
                        timestamp BIGINT,
                        type INTEGER
                    );"""
                )
                await cursor.execute(
                    """CREATE TABLE IF NOT EXISTS appeal_view_info (
                        message_id INTEGER PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        guild_id INTEGER,
                        done TEXT,
                        pages TEXT,
                        appeal_type INTEGER,
                        ); 
                    """
                )
                await connection.commit()

    async def get_appeal_view_info(self, message_id: int) -> AppealViewInfo:
        """
        Retrieve the appeal view information associated with a specified message ID.

        Args:
        - message_id (int): The unique identifier of the message whose appeal view information is sought.

        Returns:
        - AppealViewInfo: An instance representing the appeal view information retrieved from the database.

        Raises:
        - TypeError: If message_id is not an integer.
        - AppealViewInfoNotFound: If no appeal view information is found for the specified message_id.
        - SQLException: If multiple entries for the same message_id are found in the database.

        """

        if not isinstance(message_id, int):
            raise TypeError("Message ID is not an integer")
        if self.use_sqlite:
            async with aiosqlite.connect(self.db) as conn:
                conn.row_factory = dict_factory
                cursor = await conn.cursor()
                await cursor.execute(
                    "SELECT * from appeal_view_info WHERE message_id=?", (message_id,)
                )
                results = await cursor.fetchall()
        else:
            async with self.get_a_connection() as connection:
                cursor = await connection.cursor(DictCursor)

                await cursor.execute(
                    "SELECT * FROM appeal_view_info WHERE message_id=?", (message_id,)
                )
                results = list(await cursor.fetchall())
        if len(results) == 0:
            raise AppealViewInfoNotFound(
                f"Information about a view with message id {message_id} is not found"
            )
        elif len(results) == 1:
            return AppealViewInfo.from_dict(results[0])
        else:
            raise SQLException(
                f"Too many ({len(results)} of them) appeal view infos exist with message id {message_id}"
            )
    async def del_appeal_view_info(self, message_id: int):
        if not isinstance(message_id, int):
            raise TypeError("Message ID is not an integer")
        if self.use_sqlite:
            async with aiosqlite.connect(self.db) as conn:
                cursor = await conn.cursor()
                await cursor.execute("DELETE FROM appeal_view_info WHERE message_id=?", (message_id,))
                await conn.commit()
        else:
            async with mysql_connection(
                    host=self.mysql_db_ip,
                    password=self.mysql_password,
                    user=self.mysql_username,
                    database=self.mysql_db_name,
            ) as conn:
                cursor = await conn.cursor()
                await cursor.execute("DELETE FROM appeal_view_info WHERE message_id=%s", (message_id,))
                await conn.commit()

    async def set_appeal_view_info(self, view_info: AppealViewInfo):
        if not isinstance(view_info, AppealViewInfo):
            raise TypeError(
                f"view_info is not an AppealViewInfo, but a(n) {view_info.__class__.__name__}"
            )
        if self.use_sqlite:
            async with aiosqlite.connect(self.db) as conn:
                cursor = await conn.cursor()
                await cursor.execute(
                    """INSERT INTO appeal_view_info (message_id, user_id, guild_id, done, pages, appeal_type) VALUES (?,?,?,?,?,?) 
                    ON CONFLICT (message_id) DO UPDATE SET message_id=?, user_id=?, guild_id=?, done=?,pages=?, appeal_type=?""",
                    (
                        view_info.message_id,
                        view_info.user_id,
                        view_info.guild_id,
                        view_info.done,
                        int(view_info.appeal_type),
                        orjson.dumps(view_info.pages),
                        view_info.message_id,
                        view_info.user_id,
                        view_info.guild_id,
                        view_info.done,
                        orjson.dumps(view_info.pages),
                        int(view_info.appeal_type)
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
                cursor = conn.cursor()
                cursor.execute(
                    """INSERT INTO appeal_view_info (message_id, user_id, guild_id, done,pages, appeal_type) VALUES (?,?,?,?,?,?) 
                    ON DUPLICATE KEY UPDATE message_id=?, user_id=?, guild_id=?, done=?,pages=?, appeal_type=?""",
                    (
                        view_info.message_id,
                        view_info.user_id,
                        view_info.guild_id,
                        view_info.done,
                        orjson.dumps(view_info.pages),
                        int(view_info.appeal_type),
                        view_info.message_id,
                        view_info.user_id,
                        view_info.guild_id,
                        view_info.done,
                        orjson.dumps(view_info.pages),
                        int(view_info.appeal_type),
                    ),
                )
                conn.commit()

    async def get_all_appeal_view_infos(self) -> typing.Sequence[AppealViewInfo]:
        if self.use_sqlite:
            async with aiosqlite.connect(self.db) as conn:
                conn.row_factory = dict_factory
                cursor = await conn.cursor()
                await cursor.execute("SELECT * from appeal_view_info")
                results = await cursor.fetchall()
        else:
            async with self.get_a_connection() as connection:
                cursor = await connection.cursor(DictCursor)

                await cursor.execute("SELECT * FROM appeal_view_info")
                results = list(await cursor.fetchall())
        if len(results) == 0:
            raise AppealViewInfoNotFound("There are no appeal view infos")
        errors = []
        for result in results:
            try:
                yield AppealViewInfo.from_dict(result)
            except orjson.JSONDecodeError as jde:
                err = InvalidDictionaryInDatabaseException.from_invalid_data(result)
                err.__cause__ = jde
                errors.append(jde)
            except KeyError as err:
                nerr = FormatException(
                    f"I expected a valid AppealViewInfoObject, but got the object {result}"
                )
                nerr.__cause__ = err
                errors.append(nerr)
        if errors:
            raise BaseExceptionGroup("Formatting exceptions occured!", errors)
