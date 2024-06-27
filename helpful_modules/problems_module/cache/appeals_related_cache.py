import aiosqlite
from aiomysql import DictCursor

from ...dict_factory import dict_factory
from ..appeal import Appeal
from .guild_data_related_cache import GuildDataRelatedCache


class AppealsRelatedCache(GuildDataRelatedCache):
    async def set_appeal_data(self, data: Appeal):
        assert isinstance(data, Appeal)  # Basic type-checking
        if self.use_sqlite:
            async with aiosqlite.connect(self.db) as conn:
                cursor = await conn.cursor()
                await cursor.execute(
                    """INSERT INTO appeals (special_id, appeal_str, appeal_num, user_id, timestamp,type) 
                    VALUES (?,?,?,?,?,?) 
                    ON CONFLICT REPLACE 
                    special_id=?, appeal_str=?, appeal_num=?, user_id=?, timestamp=?, type=?""",
                    (
                        data.special_id,
                        data.appeal_str,
                        data.appeal_num,
                        data.user_id,
                        data.timestamp,
                        data.type,
                        data.special_id,
                        data.appeal_str,
                        data.appeal_num,
                        data.user_id,
                        data.timestamp,
                        data.type,
                    ),
                )  # TODO: test
                await conn.commit()
        else:
            with self.get_a_connection() as connection:
                cursor = await connection.cursor(DictCursor)
                await cursor.execute(
                    """INSERT INTO appeals (special_id, appeal_str, appeal_num, user_id, timestamp,type) 
                    VALUES (%s,%s,%s,%s,%s,%s) 
                    ON DUPLICATE KEY UPDATE 
                    special_id=%s, appeal_str=%s, appeal_num=%s, user_id=%s, timestamp=%s, type=%s""",
                    (
                        data.special_id,
                        data.appeal_str,
                        data.appeal_num,
                        data.user_id,
                        data.timestamp,
                        data.type,
                        data.special_id,
                        data.appeal_str,
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
                if len(results) == 0:
                    return default
                elif len(results) == 1:
                    return Appeal.from_dict(results[0])
                else:
                    raise SQLException(
                        "There were too many rows with the same special id in the appeals table!"
                    )
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
async def initialize_sql_table(self) -> None:
    """Initialize SQL table for appeals."""
    await super().initialize_sql_table()
    if self.use_sqlite:
        async with aiosqlite.connect(self.db) as conn:
            cursor = await conn.cursor()
            await cursor.execute(
                """CREATE TABLE IF NOT EXISTS appeals (
                    special_id INTEGER PRIMARY KEY,
                    appeal_str TEXT,
                    appeal_num INTEGER,
                    user_id INTEGER,
                    timestamp INTEGER,
                    type TEXT
                )"""
            )
            await conn.commit()
    else:
        async with self.get_a_connection() as connection:
            cursor = await connection.cursor(DictCursor)
            await cursor.execute(
                """CREATE TABLE IF NOT EXISTS appeals (
                    special_id BIGINT PRIMARY KEY,
                    appeal_str TEXT,
                    appeal_num INT,
                    user_id BIGINT,
                    timestamp BIGINT,
                    type TEXT
                )"""
            )
            await connection.commit()
