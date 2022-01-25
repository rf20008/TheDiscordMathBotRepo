import asyncio
import copy

import aiosqlite
from ...dict_factory import dict_factory
from ..mysql_connector_with_stmt import mysql_connection
from ..GuildData.guild_data import GuildData
from ..mysql_connector_with_stmt import *
from .user_data_related_cache import UserDataRelatedCache
class GuildDataRelatedCache:
    def set_guild_data(self, data: GuildData):
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
                        str(data.mods_check.to_dict())
                    )
                ) # TODO: test
                await conn.commit()
        else:
            with self.get_a_connection() as connection:
                cursor = connection.cursor()
                cursor.execute(
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
                        str(data.mods_check.to_dict())
                    )
                )  # TODO: test this

    async def get_guild_data(self, guild_id: int, default: GuildData):
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
                    raise SQLException("There were too many rows with the same guild id in guild data")
        else:
            with self.get_a_connection() as connection:
                cursor = connection.cursor(dictionaries=True)

                await cursor.execute(
                    "SELECT * FROM guild_data WHERE guild_id = %s", (guild_id,)
                )
                results = list(cursor.fetchall())
                if len(results) == 0:
                    return default
                elif len(results) == 1:
                    return GuildData.from_dict(results[0])
                else:
                    raise SQLException("There were too many rows with the same guild id in guild data")




