"""
This file is part of The Discord Math Problem Bot Repo

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

import asyncio
import logging
import pickle
import sqlite3
import typing
import warnings
from copy import copy, deepcopy
from types import FunctionType
from typing import *

import aiosqlite
import disnake

from helpful_modules.dict_factory import dict_factory

from ..base_problem import BaseProblem
from ..errors import *
from ..mysql_connector_with_stmt import mysql_connection
from ..parse_problem import convert_dict_to_problem, convert_row_to_problem
from ..quizzes import QuizProblem

log = logging.getLogger(__name__)


# TODO: make a function that takes into account the 3 types of problems, and make a function that given a problem dictionary, converts the problem to the right type
class ProblemsRelatedCache:
    def __init__(
        self,
        *,
        mysql_username: str,
        mysql_password: str,
        mysql_db_ip: str,
        mysql_db_name: str,
        use_sqlite: bool = False,
        max_answer_length: int = 100,
        max_question_limit: int = 250,
        max_guild_problems: int = 125,
        max_answers_per_problem: int = 25,
        max_problems_per_quiz: int = 50,
        max_quizzes_per_guild: int = 50,
        warnings_or_errors: Union[Literal["warnings"], Literal["errors"]] = "warnings",
        db_name: str = "problems_module.db",
        update_cache_by_default_when_requesting: bool = True,
        use_cached_problems: bool = False,
    ):
        """Create a new MathProblemCache. The arguments should be self-explanatory.
        Many methods are async!"""
        self.cached_submissions_organized_by_dict = None
        log.info("Initializing the MathProblemCache object.")
        # make_sql_table([], db_name = sql_dict_db_name)
        # make_sql_table([], db_name = "MathProblemCache1.db", table_name="kv_store")
        if use_sqlite:
            warnings.warn("Sqlite has been deprecated. Use MySQL instead.")
        self.db_name = db_name
        self.db = db_name
        if warnings_or_errors not in ["warnings", "errors"]:
            log.critical("Uh oh; warnings_or_errors is bad")
            raise ValueError(
                f"warnings_or_errors is {warnings_or_errors}, not 'warnings' or 'errors'"
            )
        self.warnings = (
            warnings_or_errors == "warnings"
        )  # Whether to raise TypeErrors or warn
        if max_answers_per_problem < 1:
            raise ValueError("max_answers_per_problem must be at least 1!")
        self._max_answers_per_problem = max_answers_per_problem
        self.use_sqlite = use_sqlite
        self.use_cached_problems = use_cached_problems
        self._max_answer_length = max_answer_length
        self._max_question_length = max_question_limit
        self._max_guild_limit = max_guild_problems
        self.mysql_username = mysql_username
        self.max_quizzes_per_guild = max_quizzes_per_guild
        self.max_problems_per_quiz = max_problems_per_quiz
        self.mysql_password = mysql_password
        self.mysql_db_ip = mysql_db_ip
        self.mysql_db_name = mysql_db_name
        asyncio.run(
            self.initialize_sql_table()
        )  # Initialize the SQL tables (but asyncio.run() has to be used because __init__ cannot be async)
        self.update_cache_by_default_when_requesting = (
            update_cache_by_default_when_requesting
        )
        self.guild_ids = set()
        self.cached_submissions = []
        self.cached_quizzes = []
        self.guild_problems = dict()
        self._guilds: typing.List[disnake.Guild] = []
        # asyncio.run(self.update_cache())
        self.cached_sessions = {}

    async def bgsave(
        self,
        schedule: bool = True,
        path: str = None,
        wait: bool = False,
        raise_on_error: bool = False,
        replace: bool = False,
    ):
        """
        Perform a background save operation.

        This method is specific to Redis caches and is not supported for SQL caches.
        Attempting to call this method on a SQL cache will raise a BGSaveNotSupportedOnSQLException.

        Parameters:
        - schedule: An argument representing the schedule for the background save operation.
        - path (str): The path to save the data to.
        - wait (bool): Whether to wait for the operation to complete.
        - raise_on_error (bool): Whether to raise an error if the operation encounters an error.
        - replace (bool): Whether to replace existing data at the specified path.

        Raises:
        - BGSaveNotSupportedOnSQLException: If the cache is a SQL cache and does not support background save operations.
        """
        raise BGSaveNotSupportedOnSQLException("Only Redis caches can do bgsave")

    async def convert_to_dict(self) -> dict:
        """A method that converts self to a dictionary (not used, will probably be removed soon)"""
        e = {}
        await self.update_cache()

        for guild_id in self.guild_ids:
            e[guild_id] = {}
            for Problem in self.guild_problems[guild_id]:
                e[guild_id][Problem.id] = Problem.to_dict()
        return e

        # TODO: finish logging

    def convert_dict_to_math_problem(self, problem: dict, use_from_dict: bool = True):
        """Convert a dictionary into a math problem. It must be in the expected format. (Overridden by from_dict, but still used) Possibly not used due to SQL."""
        if use_from_dict:

            return problem.to_dict()
        try:
            assert isinstance(problem, dict)
        except AssertionError:
            raise TypeError("problem is not actually a Dictionary")
        guild_id = problem["guild_id"]
        if guild_id is not None:
            guild_id = int(guild_id)
        problem2 = BaseProblem(  # Create the problem
            question=problem["question"],
            answer=problem["answer"],
            id=int(problem["id"]),
            guild_id=guild_id,
            voters=problem["voters"],
            solvers=problem["solvers"],
            author=problem["author"],
            cache=self,
        )
        return problem2

    async def get_problem(
        self, guild_id: typing.Optional[int], problem_id: int
    ) -> BaseProblem:
        """Gets the problem with this guild id and problem id. If the problem is not found, a ProblemNotFound exception will be raised."""
        # This isn't working
        # Possible causes:
        # The item is of the wrong type
        # Wrong database/table / a SQL feature that I didn't know about
        # Searching by NULL
        log.debug(
            f"Type of guild_id & problem_id: guild_id: {type(guild_id)} {guild_id}, problem_id: {type(problem_id)} {problem_id}"
        )
        assert isinstance(guild_id, int) or guild_id is None
        # The problem: where doesn't work with an 'and' clause
        if not isinstance(problem_id, int):
            if self.warnings:
                warnings.warn("problem_id is not a integer", category=RuntimeWarning)
            else:
                raise TypeError("problem_id is not a integer")
        if self.use_cached_problems:
            if self.update_cache_by_default_when_requesting:
                await self.update_cache()  # Make sure the cache is up-to-date
            try:
                return self.guild_problems[guild_id][
                    problem_id
                ]  # Get the cached problem!
            except KeyError:
                try:
                    return self.global_problems[problem_id]  # global problem?
                except KeyError:
                    raise ProblemNotFound(
                        "Problem not found in the cache! You may want to try again, but without caching!"
                    )
        else:
            # Otherwise, use SQL to get the problem!
            if self.use_sqlite:
                async with aiosqlite.connect(self.db_name) as conn:
                    try:
                        conn.row_factory = dict_factory  # Make sure the row_factory can be set to dict_factory
                    except Exception as e:
                        raise MathProblemsModuleException(f"Oh no{'!' * 30}") from e
                    # Theory: the sql statement is not the problem
                    cursor = await conn.cursor()
                    log.debug(
                        f"Getting the problem with guild id {guild_id} and problem_id {problem_id} (types: {type(guild_id)}, {type(problem_id)})"
                    )
                    log.debug("Expected SQL statement:")
                    log.warning(
                        f"""SELECT * FROM problems
    WHERE problem_id = {problem_id})"""
                    )
                    # The problem is most likely not the SQL statement!
                    r = await cursor.execute(
                        """SELECT * FROM problems WHERE problem_id = ?""",
                        # Not sure if making "from" uppercase will change anything (but it selects the problem from the database)
                        (problem_id,),
                    )
                    log.debug(str(r))
                    rows = list(await cursor.fetchall())
                    log.debug(f"{len(rows)} problems found")
                    if len(rows) == 0:
                        raise ProblemNotFound("Problem not found!")
                    elif len(rows) > 1:
                        log.critical("Uh oh; too many problems!")
                        raise TooManyProblems(
                            f"{len(rows)} problems exist with the same guild_id and problem_id, not 1"
                        )
                    await conn.commit()
                    if isinstance(rows[0], sqlite3.Row):
                        row = dict_factory(cursor, rows[0])  #
                    else:
                        row = rows[0]
                    return convert_dict_to_problem(row, cache=copy(self))
            else:
                with mysql_connection(
                    host=self.mysql_db_ip,
                    password=self.mysql_password,
                    user=self.mysql_username,
                    database=self.mysql_db_name,
                ) as connection:
                    cursor = connection.cursor(dictionaries=True)
                    cursor.execute(
                        "SELECT * from problems WHERE problem_id = %s", (problem_id,)
                    )  # Get the problem
                    rows = cursor.fetchall()
                    if len(rows) == 0:
                        raise ProblemNotFound("Problem not found!")
                    elif len(rows) > 1:
                        raise TooManyProblems(
                            "Uh oh... 2 problems exist with the same guild id and the same problem id"
                        )
                    return convert_row_to_problem(cache=copy(self), row=rows[0])

    async def cache_all_problems(self):
        self.guild_ids = set()
        self.guild_problems = {}
        if self.use_sqlite:
            async with aiosqlite.connect(self.db_name) as conn:
                conn.row_factory = dict_factory
                cursor = await conn.cursor()
                await cursor.execute("SELECT * FROM problems")  # Get all problems
                for row in await cursor.fetchall():  # For each problem:
                    if not isinstance(row, dict):

                        problem = convert_row_to_problem(
                            pickle.loads(row), cache=copy(self)
                        )  # Convert the problems to problem objects
                    else:
                        problem = convert_row_to_problem(row=row, cache=None)
                    if (
                        problem.guild_id not in self.guild_ids
                    ):  # Similar logic: Make sure it's there!
                        self.guild_ids.add(problem.guild_id)
                        self.guild_problems[problem.guild_id] = (
                            {}
                        )  # For quick, cached access?
                    try:
                        self.guild_problems[problem.guild_id][problem.id] = problem
                    except BaseException as e:
                        raise SQLException(
                            "The cache could not be updated because assigning the problem failed!"
                        ) from e
            return

        with mysql_connection(
            host=self.mysql_db_ip,
            password=self.mysql_password,
            user=self.mysql_username,
            database=self.mysql_db_name,
        ) as connection:
            cursor = connection.cursor(dictionaries=True)
            cursor.execute("SELECT * FROM problems")  # Get all problems
            for row in cursor.fetchall():
                problem = convert_row_to_problem(row, cache=None)
                if (
                    problem.guild_id not in self.guild_ids
                ):  # Similar logic: Make sure it's there!
                    self.guild_ids.add(problem.guild_id)
                    self.guild_problems[problem.guild_id] = (
                        {}
                    )  # For quick, cached access?
                try:
                    self.guild_problems[problem.guild_id][problem.id] = problem
                except BaseException as e:
                    raise SQLException(
                        "An error occurred while assigning the problem..."
                    ) from e

    @property
    def global_problems(self):
        return self.guild_problems.get(None, {})

    @global_problems.setter
    def global_problems(self, value):
        self.guild_problems[None] = value

    async def get_all_problems(self, replace_cache: bool = False):
        if replace_cache:
            await self.cache_all_problems()
        return self.guild_problems

    async def get_guild_problems(
        self, guild: disnake.Guild, replace_cache: bool = False
    ) -> typing.Dict[int, BaseProblem]:
        """Gets the guild problems! Guild must be a Guild object. If you are trying to get global problems, use get_global_problems."""
        assert isinstance(guild, disnake.Guild)
        if replace_cache:
            await self.cache_all_problems()
        try:
            return self.guild_problems[guild.id]
        except KeyError:
            return {}

    async def get_problems_by_guild_id(
        self, guild_id: int, replace_cache: bool = False
    ) -> typing.Dict[int, BaseProblem]:
        if not isinstance(guild_id, int) and guild_id is not None:
            raise AssertionError

        if guild_id is None:
            return await self.get_global_problems()
        if replace_cache:
            await self.cache_all_problems()
        try:
            return self.guild_problems[guild_id]
        except KeyError:
            return {}

    async def get_problems_by_func(
        self: "MathProblemCache",
        func: FunctionType = lambda problem: False,
        replace_cache: bool = False,
        args: typing.Optional[typing.Union[tuple, list]] = None,
        kwargs: Optional[dict] = None,
    ) -> typing.List[BaseProblem]:
        """Returns the list of all problems that match the given function. args and kwargs are extra parameters to give to the function"""
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}
        if replace_cache:
            await self.cache_all_problems()
        guild_problems = []
        for item in self.guild_problems.values():
            guild_problems.extend(
                item.values()
            )  # This could be a list comprehension (but it creates the list of guild problems)
        global_problems_that_meet_the_criteria = [
            problem
            for problem in self.global_problems.values()
            if func(problem, *args, **kwargs)  # type: ignore
        ]
        guild_problems_that_meet_the_criteria = [
            problem for problem in guild_problems if func(problem, *args, **kwargs)  # type: ignore
        ]
        problems_that_meet_the_criteria = global_problems_that_meet_the_criteria
        problems_that_meet_the_criteria.extend(guild_problems_that_meet_the_criteria)
        return problems_that_meet_the_criteria

    async def get_global_problems(
        self: "MathProblemCache", replace_cache: bool = False
    ) -> typing.List[BaseProblem]:
        """Returns global problems"""
        if replace_cache:
            await self.cache_all_problems()
        return self.global_problems

    def add_empty_guild(self, guild) -> typing.NoReturn:
        """Adds a dictionary that is empty for the guild. Guild must be a disnake.Guild object"""
        raise MathProblemsModuleException(
            "This method has been removed and you should not use it! It doesn't have a purpose anyway!"
        )
        # No longer needed
        # if not isinstance(Guild, disnake.Guild):
        #    raise TypeError("Guild is not actually a Guild")
        # try:
        #    if self._dict[str(Guild.id)] != {}:
        #        raise GuildAlreadyExistsException
        # except KeyError:
        #    self._dict[str(Guild.id)] = {}
        #
        # self._dict[Guild.id] = {}

    async def add_problem(
        self, problem_id: int, problem: BaseProblem
    ) -> Optional[BaseProblem]:
        """Adds a problem and returns the added MathProblem"""
        # Preliminary checks -otherwise SQL bugs
        guild_id = problem.guild_id
        if not isinstance(problem_id, int):
            if self.warnings:
                warnings.warn(
                    "problem_id is not a integer.... this may cause an exception"
                )
            else:
                raise TypeError("problem_id is not a integer.")

        # Make sure the problem does not exist!

        try:
            if (await self.get_problem(None, problem_id)) is not None:
                raise MathProblemsModuleException(
                    "Problem already exists! Use update_problem instead"
                )
        except ProblemNotFound:
            # an exception raised when the problem does not exist! That means we're good to add the problem!
            pass

        if self.update_cache_by_default_when_requesting:
            # Used to determine whether it has reached the limit! Takes O(N) time
            await self.update_cache()
        try:
            if guild_id is None:
                # There is no limit for global problems (which could be exploited!)
                pass
            elif (
                len(self.guild_problems[guild_id]) >= self.max_guild_problems
            ):  # Make sure this doesn't go over the max guild problem limit (which is 150)
                raise TooManyProblems(
                    f"There are already {self.max_guild_problems} problems!"
                )
        except KeyError:  # New guild creating first problem
            pass
        if not isinstance(
            problem, BaseProblem
        ):  # Make sure it's actually a Problem and not something else
            raise TypeError("Problem is not a valid Problem object.")
        # All the checks passed, hooray! Now let's add the problem.
        if self.use_sqlite:
            async with aiosqlite.connect(self.db_name) as conn:
                try:
                    conn.row_factory = dict_factory  # Make sure the row_factory can be set to dict_factory
                except BaseException as exc:
                    # Not writeable?
                    if isinstance(exc, AttributeError):  # Can't set attribute
                        pass
                    else:
                        raise  # Re-raise the exception
                cursor = await conn.cursor()
                # We will raise if the problem already exists!
                await cursor.execute(
                    """INSERT INTO problems (guild_id, problem_id, question, answers, voters, solvers, author, extra_stuff)
                VALUES (?,?,?,?,?,?,?,?); COMMIT;""",
                    (
                        problem.guild_id,  # We expect the problem's guild id to be either an integer or None
                        int(problem.id),
                        problem.get_question(),
                        pickle.dumps(problem.answers),
                        pickle.dumps(problem.get_voters()),
                        pickle.dumps(problem.get_solvers()),
                        int(problem.author),
                        str(problem.get_extra_stuff()),
                    ),
                )

                await conn.commit()
            return problem
        else:
            async with mysql_connection(
                host=self.mysql_db_ip,
                password=self.mysql_password,
                user=self.mysql_username,
                database=self.mysql_db_name,
            ) as connection:
                cursor = await connection.cursor(dictionaries=True)
                await cursor.execute(
                    """INSERT INTO problems (guild_id, problem_id, question, answer, voters, solvers, author, extra_stuff)
                VALUES (%s,%s,%s,%b,%b,%b,%s, %s)""",
                    (
                        int(problem.guild_id),
                        int(problem.id),
                        problem.get_question(),
                        pickle.dumps(problem.answers),
                        pickle.dumps(problem.get_voters()),
                        pickle.dumps(problem.get_solvers()),
                        int(problem.author),
                        str(problem.get_extra_stuff()),
                    ),
                )

    async def remove_problem(
        self, guild_id: typing.Optional[int], problem_id: int
    ) -> BaseProblem:
        """Removes a problem. Returns the deleted problem"""
        Problem = await self.get_problem(guild_id, problem_id)
        await self.remove_problem_without_returning(guild_id, problem_id)
        return Problem

    async def remove_problem_without_returning(
        self,
        guild_id: typing.Optional[int],
        problem_id: int,
    ) -> None:
        """Remove a problem without returning! Saves time."""
        assert isinstance(guild_id, int) or guild_id is None
        if not isinstance(problem_id, int):
            if self.warnings:
                warnings.warn("problem_id isn't an integer")
            else:
                raise TypeError("problem_id isn't an integer!")
        if self.use_sqlite:
            async with aiosqlite.connect(self.db_name) as conn:
                try:
                    conn.row_factory = dict_factory  # Make sure the row_factory can be set to dict_factory
                except BaseException as exc:
                    # Not writeable?
                    try:
                        dict_factory  # Check for name error
                    except NameError as exc2:
                        raise MathProblemsModuleException(
                            "dict_factory could not be found"
                        ) from exc2
                    if isinstance(exc, AttributeError):  # Can't set attribute
                        raise SQLException("Uh oh")
                    else:
                        raise  # Re-raise the exception
                cursor = await conn.cursor()
                await cursor.execute(
                    "DELETE FROM problems WHERE problem_id = ?",
                    (problem_id,),
                )  # The actual deletion
                try:
                    del self.guild_problems[guild_id][
                        problem_id
                    ]  # Delete from the cache
                    await self.update_cache()
                except KeyError:
                    # It's already deleted!
                    pass

                await conn.commit()

        else:
            with mysql_connection(
                host=self.mysql_db_ip,
                password=self.mysql_password,
                user=self.mysql_username,
                database=self.mysql_db_name,
            ) as connection:
                cursor = connection.cursor(dictionaries=True)
                cursor.execute(
                    "DELETE FROM problems WHERE problem_id = %s",
                    (problem_id,),
                )  # The actual deletion
                connection.commit()
                try:
                    del self.guild_problems[guild_id][
                        problem_id
                    ]  # Delete from the cache
                    await self.update_cache()
                except KeyError:
                    pass

    async def remove_duplicate_problems(self) -> None:
        """Deletes duplicate problems. Takes O(N^2) time which is slow"""
        if self.use_sqlite:
            async with aiosqlite.connect(
                self.db_name
            ) as conn:  # Fetch the list of problems
                cursor = await conn.cursor()
                await cursor.execute("SELECT * FROM problems")
                all_problems = [
                    BaseProblem.from_row(dict_factory(cursor, row))
                    for row in deepcopy(await cursor.fetchall())
                ]
                await conn.commit()
        else:
            with mysql_connection(
                host=self.mysql_db_ip,
                password=self.mysql_password,
                user=self.mysql_username,
                database=self.mysql_db_name,
            ) as connection:
                cursor = connection.cursor(dictionaries=True)
                await cursor.execute("SELECT * FROM Problems")
                all_problems = [
                    BaseProblem.from_row(row, cache=copy(self))
                    for row in cursor.fetchall()
                ]
        for problemA in range(len(all_problems)):
            for problemB in range(len(all_problems)):
                if problemA == problemB:  # Same index?
                    pass  # Don't do anything
                if all_problems[problemA] == all_problems[problemB]:
                    await self.remove_problem_without_returning(
                        guild_id=problemB.guild_id, problem_id=[problemA].id
                    )  # Delete the problem

    async def get_guilds(
        self, bot: disnake.ext.commands.Bot = None
    ) -> List[Union[int, Optional[disnake.Guild]]]:
        """Get the guilds (due to using sql, it must return the guild id, bot is needed to return guilds. takes O(n) time)"""
        try:
            assert bot is None or isinstance(bot, disnake.ext.commands.Bot)
        except AssertionError:
            raise AssertionError("bot isn't a bot!")

        if self.update_cache_by_default_when_requesting:
            await self.update_cache()

        if bot is not None:
            self._guilds = []
            for guild_id in self.guild_ids:
                guild = bot.get_guild(guild_id)  # Get the guild
                if guild is None:  # Guild not found
                    if self.warnings:
                        warnings.warn("guild is None")  # Warn?
                    else:
                        raise RuntimeError(
                            f"Guild not found (id: {guild_id}) :-("
                        )  # Or error
                else:
                    self._guilds.append(guild)
            return self._guilds

        return self.guild_ids

    async def update_problem(self, problem_id: int, new: BaseProblem) -> None:
        """Update the problem stored with the given guild id and problem id. This replaces the problem with the new problem"""
        assert isinstance(problem_id, int)
        assert isinstance(new, BaseProblem) and not isinstance(new, QuizProblem)
        if self.use_sqlite:
            async with aiosqlite.connect(self.db_name) as conn:
                try:
                    conn.row_factory = dict_factory  # Make sure the row_factory can be set to dict_factory
                except BaseException as exc:
                    # Not writeable?
                    raise SQLException(
                        "The row factory can't be set to dict_factory"
                    ) from exc
                cursor = await conn.cursor()
                # We will raise if the problem already exists!
                await cursor.execute(
                    """UPDATE problems 
                    SET guild_id = ?, problem_id = ?, question = ?, answers = ?, voters = ?, solvers = ?, author = ?, extra_stuff = ?
                    WHERE problem_id = ?;""",
                    (
                        new.guild_id,
                        int(new.id),
                        new.question,
                        pickle.dumps(new.answers),
                        pickle.dumps(new.voters),
                        pickle.dumps(new.solvers),
                        int(new.author),
                        str(new.get_extra_stuff()),
                        int(problem_id),
                    ),
                )
                await conn.commit()
                await cursor.close()
                # await conn.close()
        else:
            with mysql_connection(
                host=self.mysql_db_ip,
                password=self.mysql_password,
                user=self.mysql_username,
                database=self.mysql_db_name,
            ) as connection:
                cursor = connection.cursor(dictionaries=True)
                cursor.execute(
                    """UPDATE problems 
                    SET guild_id = '%s', problem_id = '%s', question = %s, answer = %s, voters = %s, solvers = %s, author = '%s', extra_stuff = '%s'
                    WHERE problem_id = '%s'""",
                    (
                        int(new.guild_id),
                        int(new.id),
                        new.question,
                        pickle.dumps(new.answers),
                        pickle.dumps(new.voters),
                        pickle.dumps(new.solvers),
                        int(new.author),
                        str(new.get_extra_stuff()),
                        problem_id,
                    ),
                )
                connection.commit()

    @property
    def max_question_length(self):
        return self._max_question_length

    @property
    def max_guild_problems(self):
        return self._max_guild_limit

    @property
    def max_answers_per_problem(self):
        return self._max_answers_per_problem

    @property
    def max_answer_length(self):
        return self._max_answer_length

    async def initialize_sql_table(self):
        """Initialize the SQL tables if they don't already exist"""
        if self.use_sqlite:
            async with aiosqlite.connect(self.db_name) as conn:
                cursor = await conn.cursor()
                await cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS problems (
                        id INTEGER PRIMARY KEY,
                        guild_id INTEGER,
                        problem_id INTEGER,
                        question TEXT,
                        answers BLOB,
                        voters BLOB,
                        solvers BLOB,
                        author INTEGER,
                        extra_stuff TEXT
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
                cursor = connection.cursor(dictionaries=True)
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS problems (
                        id INT PRIMARY KEY,
                        guild_id INT,
                        problem_id INT,
                        question TEXT,
                        answers LONGBLOB,
                        voters LONGBLOB,
                        solvers LONGBLOB,
                        author INT,
                        extra_stuff TEXT
                    )
                    """
                )
                connection.commit()

    async def run_sql(
        self, sql: str, placeholders: typing.Optional[typing.List[Any]] = None
    ) -> dict:
        """Run arbitrary SQL. Only used in /sql"""
        assert isinstance(sql, str)
        assert isinstance(placeholders, list) or placeholders is None
        if placeholders is None:
            placeholders = []
        if self.use_sqlite:
            async with aiosqlite.connect(self.db_name) as conn:
                conn.row_factory = dict_factory
                cursor = await conn.cursor()
                await cursor.execute(sql, placeholders)
                await conn.commit()
                return await cursor.fetchall()
        else:
            with mysql_connection(
                host=self.mysql_db_ip,
                password=self.mysql_password,
                user=self.mysql_username,
                database=self.mysql_db_name,
            ) as connection:
                cursor = connection.cursor(dictionaries=True)
                cursor.execute(sql, placeholders)
                connection.commit()
                return cursor.fetchall()
