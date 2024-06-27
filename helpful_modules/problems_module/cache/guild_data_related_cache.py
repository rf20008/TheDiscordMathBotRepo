import asyncio
import copy

import aiomysql
import aiosqlite
from aiomysql import DictCursor

from ...dict_factory import dict_factory
from ..errors import SQLException
from ..GuildData.guild_data import GuildData
from ..mysql_connector_with_stmt import *
from ..mysql_connector_with_stmt import mysql_connection
from .permissions_required_related_cache import PermissionsRequiredRelatedCache


class GuildDataRelatedCache(PermissionsRequiredRelatedCache):
    async def set_guild_data(self, data: GuildData):
        """Set the guild data given in the cache. The guild id will be inferred."""
        assert isinstance(data, GuildData)  # Basic type-checking

        if self.use_sqlite:
            async with aiosqlite.connect(self.db) as conn:
                cursor = await conn.cursor()
                await cursor.execute(
                    """INSERT INTO guild_data (guild_id, blacklisted, can_create_problems_check, can_create_quizzes_check, mod_check) 
                    VALUES (?,?,?,?,?) 
                    ON CONFLICT REPLACE 
                    guild_id = ?, blacklisted=?, can_create_problems_check = ?, can_create_quizzes_check = ?, mod_check = ?""",
                    (
                        data.guild_id,
                        int(data.blacklisted),
                        str(data.can_create_problems_check.to_dict()),
                        str(data.can_create_quizzes_check.to_dict()),
                        str(data.mods_check.to_dict()),
                        data.guild_id,
                        int(data.blacklisted),
                        str(data.can_create_problems_check.to_dict()),
                        str(data.can_create_quizzes_check.to_dict()),
                        str(data.mods_check.to_dict()),
                    ),
                )  # TODO: test
                await conn.commit()
        else:
            async with self.get_a_connection() as connection:
                cursor = await connection.cursor(DictCursor)
                await cursor.execute(
                    """INSERT INTO guild_data (guild_id, blacklisted, can_create_problems_check, can_create_quizzes_check, mod_check)
                    VALUES (%s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    guild_id=?, blacklisted=?, can_create_problems_check=?, can_create_quizzes_check=?, mod_check = ?""",
                    (
                        data.guild_id,
                        int(data.blacklisted),
                        str(data.can_create_problems_check.to_dict()),
                        str(data.can_create_quizzes_check.to_dict()),
                        str(data.mods_check.to_dict()),
                        data.guild_id,
                        int(data.blacklisted),
                        str(data.can_create_problems_check.to_dict()),
                        str(data.can_create_quizzes_check.to_dict()),
                        str(data.mods_check.to_dict()),
                    ),
                )  # TODO: test this

    async def get_guild_data(self, guild_id: int, default: GuildData | None = None):
        if default is None:
            default = GuildData.default(guild_id)
        assert isinstance(guild_id, int)
        assert isinstance(default, GuildData)

        if self.use_sqlite:
            async with aiosqlite.connect(self.db) as conn:
                conn.row_factory = dict_factory
                cursor = await conn.cursor()
                await cursor.execute(
                    "SELECT * FROM guild_data WHERE guild_id = ?", (guild_id,)
                )
                results = list(await cursor.fetchall())
                if len(results) == 0:
                    return default
                elif len(results) == 1:
                    return GuildData.from_dict(results[0])
                else:
                    raise SQLException(
                        "There were too many rows with the same guild id in guild data"
                    )
        else:
            async with self.get_a_connection() as connection:
                cursor = await connection.cursor(DictCursor)

                await cursor.execute(
                    "SELECT * FROM guild_data WHERE guild_id = %s", (guild_id,)
                )
                results = list(await cursor.fetchall())
                if len(results) == 0:
                    return default
                elif len(results) == 1:
                    return GuildData.from_dict(results[0])
                else:
                    raise SQLException(
                        "There were too many rows with the same guild id in guild data"
                    )

    async def initialize_sql_table(self) -> None:
        """Initialize SQL table for guild data."""
        await super().initialize_sql_table()
        if self.use_sqlite:
            async with aiosqlite.connect(self.db) as conn:
                cursor = await conn.cursor()
                await cursor.execute(
                    """CREATE TABLE IF NOT EXISTS guild_data (
                        guild_id INTEGER PRIMARY KEY,
                        blacklisted INTEGER,
                        can_create_problems_check TEXT,
                        can_create_quizzes_check TEXT,
                        mod_check TEXT
                    )"""
                )
                await conn.commit()
        else:
            async with self.get_a_connection() as connection:
                cursor = await connection.cursor(DictCursor)
                await cursor.execute(
                    """CREATE TABLE IF NOT EXISTS guild_data (
                        guild_id BIGINT PRIMARY KEY,
                        blacklisted BOOLEAN,
                        can_create_problems_check JSON,
                        can_create_quizzes_check JSON,
                        mod_check JSON
                    )"""
                )
                await connection.commit()
