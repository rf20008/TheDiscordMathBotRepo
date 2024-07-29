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

import typing
from collections import namedtuple as NamedTuple
from types import FunctionType
from typing import *

import orjson
from mpmath import *

from ..cache.final_cache import MathProblemCache
from ..errors import *

T = typing.TypeVar("T")


class ConverterData(NamedTuple):
    """ConverterData class

    This class is used to denote using custom classes in MySQL using the GeneralizedTable function.

    Attributes
    ---------

    type: The type that this is wrapping
    converter: A converter than converts the type given to a string
    deconverter: A converter that converts a well-formed string to the type expected.

    Let the type being wrapped T. Let X be any object of type T.
    It is expected that deconverter(converter(X)) == X for all X of type T.
    Additionally we expect converter(deconverter(X)) == X for all X of type T.
    """

    type: T
    converter: typing.Callable[[T], str]
    deconverter: typing.Callable[[str], T]


TYPE_TO_SQLITE_TYPE = {
    int: "BIGINT",
    str: "MEDIUMTEXT(10000000)",
    float: "DOUBLE(53)",
    bytes: "BIGBLOB",
    dict: ConverterData(
        dict,
        converter=orjson.dump,
        deconverter=orjson.load,
    ),
    mpf: ConverterData(mpf, converter=mpf, deconverter=lambda a: str(a)),
}

Converter = typing.Callable[[T], str]
DeConverter = typing.Callable[[str], T]


def addextratype(type_used: T, converter: Converter, deconverter: DeConverter) -> None:
    TYPE_TO_SQLITE_TYPE[T] = ConverterData(type_used, converter, deconverter)


UNUSABLE_NAMES = {
    "problems",
    "quiz_problems",
    "quiz_submissions",
    "quizzes",
    "user_data",
    "quiz_submission_sessions",
    "guild_data",
    "quiz_description",
}


class GeneralizedTable:
    """A table that can be used for general purposes and can be used
    cache: the cache used
    table_name: The table name
    name_to_type_mapping: a mapping from column names to type
    primary_key: the primary key"""

    cache: MathProblemCache
    table_name: str
    name_to_type_mapping: Mapping[str, type]
    primary_key: str

    @property
    def column_names(self):
        return self.name_to_type_mapping.keys()

    def validate(self):
        if primary_key not in self.column_names():
            raise MathProblemsModuleException(
                "Not valid! The primary key has been removed!"
            )

    def __init__(
        self,
        cache: MathProblemCache,
        table_name: str,
        name_to_type_mapping: Mapping[str, type],
        primary_key: str,
    ):
        if primary_key not in name_to_type_mapping.keys():
            raise MathProblemsModuleException(
                "You cannot use this as a primary key since it is not a column name"
            )
        self.cache = cache
        if table_name in UNUSABLE_NAMES:
            raise MathProblemsModuleException("You cannot use this table name")
        self.table_name = table_name
        self.name_to_type_mapping = name_to_type_mapping

    async def create_my_table(self):
        """
        |coro|
        Make a table for myself. Warning: DO NOT LET THE USER CONTROL THE TABLE NAME OR THE COLUMN NAMES (to prevent SQL injection!)
        This function does not return anything.
        This may throw a MathProblemsModuleException if the column name is invalid.
        """
        if self.cache.use_sqlite:
            sql_query = "CREATE TABLE IF NOT EXISTS "
            sql_query += self.table_name
            sql_query += "("
            for column_type, column_name in self.name_to_type_mapping:
                # Verify the column type
                if not isinstance(column_type, (str, dict)):
                    raise MathProblemsModuleException("The column type is invalid!")
                if isinstance(column_type, str):
                    sql_query += column_name + " " + column_type
                else:
                    sql_query += (
                        column_name + " MEDIUMTEXT(1000000)"
                    )  # 10,000,000 characters of space
                if column_name == primary_key:
                    sql_query += "PRIMARY KEY"
                sql_query += ","
            sql_query = sql_query[:-1]
            sql_query += ");"
            await self.cache.run_sql(sql_query)
        else:
            sql_query = f"CREATE TABLE IF NOT EXISTS" + self.table_name + "("
            for column_type, column_name in self.name_to_type_mapping:
                # Verify the column type
                if not isinstance(column_type, (str, dict)):
                    raise MathProblemsModuleException("The column type is invalid!")
                if isinstance(column_type, str):
                    sql_query += column_name + " " + column_type
                else:
                    sql_query += (
                        column_name + " MEDIUMTEXT(1000000)"
                    )  # 10,000,000 characters of space
                if column_name == primary_key:
                    sql_query += "PRIMARY KEY"
                sql_query += ","
            sql_query = sql_query[:-1]
            sql_query += ");"
            await self.cache.run_sql(sql_query)
        return None

    async def set_items(self, column_name_map: Dict[str, object]):
        """Set the items in the sql query to what is given. Over here it is okay if the user controls part of the data being sent, but not the column names.
        This is O(NC+Q) where C is the number of column names and N is the size of the dictionary given and Q is the time it takes to execute the query
        Warning: If the table is not initialized, this will not actually change the database!
        """
        sql_query = ""
        for key, _ in column_name_map.items():
            if key not in self.column_names:
                raise MathProblemsModuleException(
                    f"The column {key} does not exist in the database."
                )
        if self.cache.use_sqlite:
            sql_query = "REPLACE INTO " + self.table_name + "VALUES ("
            for key, _ in column_name_map.items():
                sql_query += key + ","
            sql_query = sql_query[:-1]
            for key, val in column_name_map.items():
                obj_sql_type = TYPE_TO_SQLITE_TYPE[type(val)]
                placeholders = ()
                if isinstance(obj_sql_type, str):
                    placeholders += str(val) + ","
                else:
                    placeholders += obj_sql_type.converter(val) + ","
            sql_query += ");"

            await self.cache.run_sql(sql_query, placeholders)
            return None
        else:
            sql_query = "REPLACE INTO " + self.table_name + "\n SET "
            placeholders = ()
            for column_name, value in column_name_map.items():
                sql_query += column_name + " "
                obj_sql_type = TYPE_TO_SQLITE_TYPE[type(val)]
                sql_query += "%s,"
                if isinstance(obj_sql_type, str):
                    placeholders += str(val)
                else:
                    placeholders += obj_sql_type.converter(val) + ","

            sql_query = sql_query[:-1]
            sql_query += ";"
            await self.cache.run_sql(sql_query, placeholders)

    async def get_obj(self, key: str) -> dict:
        """Get the object at the given key (when the given key is the value of the key)"""
        self.validate()
        if self.use_sqlite:
            return await self.cache.run_sql(
                f"""SELECT * FROM {self.table_name} WHERE {self.primary_key} = ?""",
                placeholders=(key),
            )
        else:
            return await self.cache.run_sql(
                f"""SELECT * FROM {self.table_name} WHERE {self.primary_key} = %s""",
                placeholders=(key),
            )
