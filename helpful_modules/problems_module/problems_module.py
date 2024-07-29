"""You can distribute any version of the Software created and distributed *before* 23:17:55.00 July 28, 2024 GMT-4
under the GNU General Public License version 3 or at your option, any  later option.
But versions of the code created and/or distributed *on or after* that date must be distributed
under the GNU *Affero* General Public License, version 3, or, at your option, any later version.

The Discord Math Problem Bot Repo - Original Problems Module (now superceded by the problems_module folder, also licensed under AGPL)

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License
as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License along with this program.
If not, see <https://www.gnu.org/licenses/>.

Author: Samuel Guo (64931063+rf20008@users.noreply.github.com)"""
import asyncio
import json
import pickle
import sqlite3
import warnings
from copy import copy, deepcopy
from sqlite3 import *
from time import sleep
from typing import *

import aiosqlite
import dislash
import nextcord
import sqldict  # https://github.com/skylergrammer/sqldict/
from nextcord import *

from helpful_modules.dict_factory import dict_factory  # Attribution to stackoverflow

from .base_problem import BaseProblem
from .errors import *

"""The core of my bot (very necessary)"""
from .quizzes import *

main_cache = None


def get_main_cache():
    return main_cache


# This is a module containing MathProblem and MathProblemCache objects. (And exceptions as well!) This may be useful outside of this discord bot so feel free to use it :) Just follow the MIT+GNU license
# Exceptions


class MathProblemCache:
    "A class that stores math problems/quizzes :-)"

    def __init__(
        self,
        max_answer_length=100,
        max_question_limit=250,
        max_guild_problems=125,
        warnings_or_errors="warnings",
        db_name: str = "problems_module.db",
        name="1",
        update_cache_by_default_when_requesting=True,
        use_cached_problems: bool = False,
    ):
        "Create a new MathProblemCache. the arguments should be self-explanatory"
        # make_sql_table([], db_name = sql_dict_db_name)
        # make_sql_table([], db_name = "MathProblemCache1.db", table_name="kv_store")
        self.db_name = db_name
        if warnings_or_errors not in ["warnings", "errors"]:
            raise ValueError(
                f"warnings_or_errors is {warnings_or_errors}, not 'warnings' or 'errors'"
            )
        self.warnings = warnings_or_errors == "warnings"
        self.use_cached_problems = use_cached_problems
        self._max_answer = max_answer_length
        self._max_question = max_question_limit
        self._guild_limit = max_guild_problems
        asyncio.run(self.initialize_sql_table())
        self.update_cache_by_default_when_requesting = (
            update_cache_by_default_when_requesting
        )

    def _initialize_sql_dict(self):
        self._sql_dict = sqldict.SqlDict(
            name=f"MathProblemCache1.db", table_name="kv_store"
        )
        self.quizzes_sql_dict = sqldict.SqlDict(
            name="TheQuizStorer", table_name="quizzes_kv_store"
        )

    async def initialize_sql_table(self):
        async with aiosqlite.connect(self.db_name) as conn:
            cursor = await conn.cursor()
            await cursor.execute(
                """CREATE TABLE IF NOT EXISTS Problems (
                    guild_id INT,
                    problem_id INT,
                    question TEXT(2000) NOT NULL,
                    answers BLOB NOT NULL, 
                    author INT NOT NULL,
                    voters BLOB NOT NULL,
                    solvers BLOB NOT NULL
                    )"""
            )  # Blob types will be compliled with pickle.loads() and pickle.dumps() (they are lists)
            # author: int = user_id

            await cursor.execute(
                """CREATE TABLE IF NOT EXISTS quizzes (
                guild_id INT,
                quiz_id INT NOT NULL PRIMARY KEY,
                problem_id INT NOT NULL,
                question TEXT(500) NOT NULL,
                answer BLOB NOT NULL,
                voters BLOB NOT NULL,
                author INT NOT NULL,
                solvers INT NOT NULL
            )"""
            )
            # Used for quizzes
            # answer: Blob (a list)
            # voters: Blob (a list)
            # solvers: Blob (a list)
            # submissions: Blob (a dictionary)
            await cursor.execute(
                """CREATE TABLE IF NOT EXISTS quiz_submissions (
                guild_id INT,
                quiz_id INT NOT NULL,
                USER_ID INT NOT NULL,
                submissions BLOB NOT NULL
                )"""
            )  # as dictionary
            # Used to store submissions!

            await conn.commit()  # Otherwise, when this closes, the database just reverted!

    @property
    def max_answer_length(self):
        return self._max_answer

    @property
    def max_question_length(self):
        return self._max_question

    @property
    def max_guild_problems(self):
        return self._guild_limit

    def convert_to_dict(self):
        "A method that converts self to a dictionary (not used, will probably be removed soon)"
        e = {}
        self.update_cache()

        for guild_id in self.guild_ids:
            e[guild_id] = {}
            for Problem in self.guild_problems[guild_id]:
                e[guild_id][Problem.id] = Problem.to_dict()
        return e

    def convert_dict_to_math_problem(self, problem, use_from_dict=True):
        "Convert a dictionary into a math problem. It must be in the expected format. (Overriden by from_dict, but still used) Possibly not used due to SQL"
        if use_from_dict:
            return BaseProblem.from_dict(problem, cache=self)
        try:
            assert isinstance(problem, dict)
        except AssertionError:
            raise TypeError("problem is not actually a Dictionary")
        guild_id = problem["guild_id"]
        if guild_id == None:
            guild_id = None
        else:
            guild_id = int(guild_id)
        problem2 = self(
            question=problem["question"],
            answer=problem["answer"],
            id=int(problem["id"]),
            guild_id=guild_id,
            voters=problem["voters"],
            solvers=problem["solvers"],
            author=problem["author"],
        )
        return problem2

    async def update_cache(self):
        "Method revamped! This method updates the cache of the guilds, the guild problems, and the cache of the global problems. Takes O(N) time"
        guild_problems = {}
        guild_ids = []
        global_problems = {}

        async with aiosqlite.connect(self.db_name) as conn:
            conn.row_factory = dict_factory
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM problems")

            for row in cursor:
                Problem = BaseProblem.from_row(row, cache=copy(self))
                if (
                    Problem.guild_id not in guild_ids
                ):  # Similar logic: Make sure it's there!
                    guild_ids.append(Problem.guild_id)
                    guild_problems[Problem.guild_id] = {}  # For quick, cached access?
                try:
                    guild_problems[Problem.guild_id][Problem.id] = Problem
                except BaseException as e:
                    raise SQLException(
                        "Uh oh..... oh no..... uh..... please help! For some reason, the cache couldn't be updated"
                    ) from e

        try:
            global_problems = deepcopy(
                guild_problems[None]
            )  # contention deepcopying more :-)
        except KeyError as exc:  # No global problems yet
            global_problems = {}
        self.guild_problems = deepcopy(
            guild_problems
        )  # More deep-copying (so it refers to a different object)
        self.guild_ids = deepcopy(guild_ids)
        self.global_problems = deepcopy(global_problems)

    async def get_problem(self, guild_id: int, problem_id: int):
        "Gets the problem with this guild id and problem id"

        if not isinstance(guild_id, int):
            if self.warnings:
                warnings.warn("guild_id is not a integer!", category=RuntimeWarning)
            else:
                raise TypeError(
                    "guild_id isn't an integer and this will cause issues in SQL!"
                )
        if not isinstance(problem_id, int):
            if self.warnings:
                warnings.warn("problem_id is not a integer", category=RuntimeWarning)
            else:
                raise TypeError("problem_id is not a integer")
        if self.use_cached_problems:
            if self.update_cache_by_default_when_requesting:
                await self.update_cache()
            try:
                return self.guild_problems[guild_id][problem_id]
            except KeyError:
                raise ProblemNotFound(
                    "Problem not found in the cache! You may want to try again, but without caching!"
                )
        else:
            # Otherwise, use SQL to get the problem!
            async with aiosqlite.connect(self.db_name) as conn:
                try:
                    conn.row_factory = dict_factory  # Make sure the row_factory can be set to dict_factory
                except BaseException as exc:
                    # Not writeable?
                    try:
                        dict_factory  # Check for nameerror
                    except NameError as exc2:
                        raise MathProblemsModuleException(
                            "dict_factory could not be found"
                        ) from exc2
                    if isinstance(exc, AttributeError):  # Can't set attribute
                        pass
                    else:
                        raise  # Re-raise the exception
                cursor = conn.cursor()
                await cursor.execute(
                    "SELECT * from problems WHERE guild_id = ? AND problem_id = ?",
                    (guild_id, problem_id),
                )
                rows = await cursor.fetchall()
                if len(rows) == 0:
                    raise ProblemNotFound("Problem not found!")
                elif len(rows) > 1:
                    raise TooManyProblems(
                        f"{len(rows)} problems exist with the same guild_id and problem_id, not 1"
                    )
                await conn.commit()
                if isinstance(rows[0], sqlite3.Row):
                    row = dict_factory(cursor, rows[0])  #
                else:
                    row = rows[0]
                return BaseProblem.from_row(rows[0], cache=copy(self))

    async def get_guild_problems(self, Guild):
        """Gets the guild problems! Guild must be a Guild object. If you are trying to get global problems, use get_global_problems."""
        if self.update_cache_by_default_when_requesting:
            await self.update_cache()
        try:
            return self.guild_problems[Guild.id]
        except KeyError:
            return {}

    async def get_global_problems(self):
        "Returns global problems"
        if self.update_cache_by_default_when_requesting:
            await self.update_cache()
        return self.global_problems

    def add_empty_guild(self, Guild):
        "Adds an dictionary that is empty for the guild. Guild must be a nextcord.Guild object"
        warnings.warn("Deprecated method: add_empty_guild", DeprecationWarning)
        pass  # No longer needed
        # if not isinstance(Guild, nextcord.Guild):
        #    raise TypeError("Guild is not actually a Guild")
        # try:
        #    if self._dict[str(Guild.id)] != {}:
        #        raise GuildAlreadyExistsException
        # except KeyError:
        #    self._dict[str(Guild.id)] = {}
        #
        # self._dict[Guild.id] = {}

    async def add_problem(self, guild_id: int, problem_id: int, Problem: BaseProblem):
        "Adds a problem and returns the added MathProblem"
        # Preliminary checks -otherwise SQL bugs
        if not isinstance(guild_id, int):
            if self.warnings:
                warnings.warn(
                    "guild_id is not an integer.... this may cause an exception"
                )
            else:
                raise TypeError("guild_id is not a integer!")
        if not isinstance(problem_id, int):
            if self.warnings:
                warnings.warn(
                    "problem_id is not a integer.... this may cause an exception"
                )
            else:
                raise TypeError("problem_id is not a integer.")

        # Make sure the problem does not exist!
        try:
            if self.get_problem(guild_id, problem_id) is not None:
                raise MathProblemsModuleException(
                    "Problem already exists! Use update_problem instead"
                )
        except ProblemNotFound:  # an exception raised when the problem already exists!
            pass
        if (
            self.update_cache_by_default_when_requesting
        ):  # Used to determine whether it has reached the limit! Takes O(N) time
            self.update_cache()
        try:
            if (
                guild_id == None
            ):  # There is no limit for global problems (which could be exploited!)
                pass
            elif (
                len(self.guild_problems[guild_id]) >= self.max_guild_problems
            ):  # Make sure this doesn't go over the max guild problem limit (which is 150)
                raise TooManyProblems(
                    f"There are already {self.max_guild_problems} problems!"
                )
        except KeyError:
            pass
        if not isinstance(
            Problem, (BaseProblem)
        ):  # Make sure it's actually a Problem and not something else
            raise TypeError("Problem is not a valid MathProblem object.")
        # All the checks passed, hooray! Now let's add the problem.
        async with aiosqlite.connect(self.db_name) as conn:
            try:
                conn.row_factory = (
                    dict_factory  # Make sure the row_factory can be set to dict_factory
                )
            except BaseException as exc:
                # Not writeable?
                try:
                    dict_factory  # Check for nameerror
                except NameError as exc2:
                    raise MathProblemsModuleException(
                        "dict_factory could not be found"
                    ) from exc2
                if isinstance(exc, AttributeError):  # Can't set attribute
                    pass
                else:
                    raise  # Re-raise the exception
            cursor = conn.cursor()
            # We will raise if the problem already exists!
            await cursor.execute(
                """INSERT INTO problems (guild_id, problem_id, question, answer, voters, solvers, author)
            VALUES (?,?,?,?,?,?,?)""",
                (
                    int(Problem.guild_id),
                    int(Problem.id),
                    Problem.get_question(),
                    pickle.dumps(Problem.get_answers()),
                    pickle.dumps(Problem.get_voters()),
                    pickle.dumps(Problem.get_solvers()),
                    int(Problem.author),
                ),
            )

            await conn.commit()
        return Problem

    async def remove_problem(self, guild_id: int, problem_id: int) -> BaseProblem:
        "Removes a problem. Returns the deleted problem"
        Problem = self.get_problem(guild_id, problem_id)
        await self.remove_problem_without_returning(guild_id, problem_id)
        return Problem

    async def remove_problem_without_returning(self, guild_id, problem_id) -> None:
        "Remove a problem without returning! Saves time."
        if not isinstance(guild_id, int):
            if self.warnings:
                warnings.warn(
                    "guild_id is not a integer. There might be an error...", Warning
                )
            else:
                raise TypeError("guild_id is not a integer")
        if not isinstance(problem_id, int):
            if self.warnings:
                warnings.warn("problem_id isn't an integer")
            else:
                raise TypeError("problem_id isn't an integer!")
        async with aiosqlite.connect(self.db_name) as conn:
            try:
                conn.row_factory = (
                    dict_factory  # Make sure the row_factory can be set to dict_factory
                )
            except BaseException as exc:
                # Not writeable?
                try:
                    dict_factory  # Check for nameerror
                except NameError as exc2:
                    raise MathProblemsModuleException(
                        "dict_factory could not be found"
                    ) from exc2
                if isinstance(exc, AttributeError):  # Can't set attribute
                    pass
                else:
                    raise  # Re-raise the exception
            cursor = conn.cursor()
            await cursor.execute(
                "DELETE FROM problems WHERE guild_id = ? and problem_id = ?",
                (guild_id, problem_id),
            )  # The actual deletion
            try:
                del self.guild_problems[guild_id][problem_id]
            except KeyError:
                # It's already deleted!
                pass

            await conn.commit()

    async def remove_duplicate_problems(self):
        "Deletes duplicate problems. Takes O(N^2) time which is slow"
        async with aiosqlite.connect(self.db_name) as conn:
            cursor = conn.cursor()
            await cursor.execute("SELECT * FROM problems")
            all_problems = [
                BaseProblem.from_row(dict_factory(cursor, row))
                for row in deepcopy(await cursor.fetchall())
            ]
            await conn.commit()
        for problemA in range(len(all_problems)):
            for problemB in range(len(all_problems)):
                if problemA == problemB:  # Same index?
                    pass  # Don't do anything
                if all_problems[problemA] == all_problems[problemB]:
                    await self.remove_problem_without_returning(
                        all_problems[problemA].guild_id, all_problems[problemA].id
                    )  # Delete the problem

    async def get_guilds(
        self, bot: nextcord.ext.commands.Bot = None
    ) -> List[Union[int, Optional[nextcord.Guild]]]:
        "Get the guilds (due to using sql, it must return the guild id, bot is needed to return guilds. takes O(n) time"
        try:
            assert bot == None or isinstance(bot, nextcord.ext.commands.Bot)
        except:
            raise AssertionError("bot isn't a bot!")

        if self.update_cache_by_default_when_requesting:
            await self.update_cache()

        if bot is not None:
            self._guilds = []
            for guild_id in self.guild_ids:
                guild = bot.get_guild(guild_id)
                if guild is None:
                    if self.warnings:
                        warnings.warn("guild is None")
                    else:
                        raise RuntimeError(f"Guild not found (id: {guild_id}) :-(")
                else:
                    self._guilds.append(guild)
            return self._guilds

        return self.guild_ids

    async def add_quiz(self, quiz: Quiz) -> Quiz:
        "Add a quiz"
        assert isinstance(quiz, Quiz)
        try:
            self.get_quiz(quiz._id)
            raise MathProblemsModuleException(
                "Quiz already exists! Use update_quiz instead"
            )
        except QuizNotFound:
            pass
        async with aiosqlite.connect(self.db_name) as conn:
            try:
                conn.row_factory = (
                    dict_factory  # Make sure the row_factory can be set to dict_factory
                )
            except BaseException as exc:
                # Not writeable?
                try:
                    dict_factory  # Check for nameerror
                except NameError as exc2:
                    raise MathProblemsModuleException(
                        "dict_factory could not be found"
                    ) from exc2
                if isinstance(exc, AttributeError):  # Can't set attribute
                    pass
                else:
                    raise  # Re-raise the exception

            cursor = conn.cursor()
            for item in quiz:
                await cursor.execute(
                    """INSERT INTO quizzes (guild_id, quiz_id, problem_id, question, answer, voters, solvers, author)
                VALUES (?,?,?,?,?,?,?,?)""",
                    (
                        item.guild_id,
                        item.quiz_id,
                        item.problem_id,
                        item.question,
                        pickle.dumps(item.answers),
                        pickle.dumps(item.voters),
                        pickle.dumps(item.solvers),
                        item.author,
                    ),
                )
            for item in quiz.submissions:
                await cursor.execute(
                    """INSERT INTO quiz_submissions (guild_id, quiz_id, user_id, submissions)
                VALUES (?,?,?,?)""",
                    (
                        item.guild_id,
                        item.quiz_id,
                        item.user_id,
                        pickle.dumps(item.to_dict()),
                    ),
                )

            await conn.commit()

    def __str__(self):
        raise NotImplementedError

    async def get_quiz(self, quiz_id: int) -> Optional[Quiz]:
        "Get the quiz with the id specified. Returns None if not found"
        assert isinstance(quiz_id, int)
        async with aiosqlite.connect(self.db_name) as conn:
            try:
                conn.row_factory = (
                    dict_factory  # Make sure the row_factory can be set to dict_factory
                )
            except BaseException as exc:
                # Not writeable?
                try:
                    dict_factory  # Check for nameerror
                except NameError as exc2:
                    raise MathProblemsModuleException(
                        "dict_factory could not be found"
                    ) from exc2
                if isinstance(exc, AttributeError):  # Can't set attribute
                    pass
                else:
                    raise  # Re-raise the exception
            cursor = conn.cursor()
            await cursor.execute("SELECT * FROM quizzes WHERE quiz_id=?", (quiz_id,))
            problems = await cursor.fetchall()
            if len(problems) == 0:
                raise QuizNotFound(f"Quiz id {quiz_id} not found")

            await cursor.execute("SELECT * FROM quiz_submissions WHERE quiz_id = ?")
            submissions = await cursor.fetchall()
            submissions = [
                QuizSubmission.from_dict(pickle.loads(item)) for item in submissions
            ]
            problems = [
                QuizProblem.from_row(dict_factory(cursor, row)) for row in problems
            ]

            # Actual Quiz generation time
            quiz = Quiz(quiz_id, problems, submissions, cache=copy(self))
            return quiz

    async def update_problem(self, guild_id, problem_id, new: BaseProblem) -> None:
        "Update the problem stored with the given guild id and problem id"
        assert isinstance(guild_id, str)
        assert isinstance(problem_id, str)
        assert isinstance(new, BaseProblem) and not isinstance(new, QuizProblem)
        async with aiosqlite.connect(self.db_name) as conn:
            try:
                conn.row_factory = (
                    dict_factory  # Make sure the row_factory can be set to dict_factory
                )
            except BaseException as exc:
                # Not writeable?
                try:
                    dict_factory  # Check for nameerror
                except NameError as exc2:
                    raise MathProblemsModuleException(
                        "dict_factory could not be found"
                    ) from exc2
                if isinstance(exc, AttributeError):  # Can't set attribute
                    pass
                else:
                    raise  # Re-raise the exception
            cursor = conn.cursor()
            # We will raise if the problem already exists!
            await cursor.execute(
                """UPDATE problems 
            SET guild_id = ?, problem_id = ?, question = ?, answer = ?, voters = ?, solvers = ?, author = ?
            WHERE guild_id = ? AND problem_id = ?;""",
                (
                    int(new.guild_id),
                    int(new.id),
                    new.get_question(),
                    pickle.dumps(new.get_answers()),
                    pickle.dumps(new.get_voters()),
                    pickle.dumps(new.get_solvers()),
                    int(new.author),
                    int(new.guild_id),
                    int(new.id),
                ),
            )

    async def update_quiz(self, quiz_id, new) -> None:
        "Update the quiz with the id given"
        assert isinstance(quiz_id, str)
        assert isinstance(new, Quiz)
        assert new.id == quiz_id
        await self.delete_quiz(quiz_id)

        await self.add_quiz(Quiz)

    async def delete_quiz(self, quiz_id):
        "Delete a quiz!"
        async with aiosqlite.connect(self._sql_dict_db_name) as conn:
            cursor = conn.cursor()
            await cursor.execute(
                "DELETE FROM quizzes WHERE quiz_id = ?", (quiz_id,)
            )  # Delete the quiz's problems
            await cursor.execute(
                "DELETE FROM quiz_submissions WHERE quiz_id=?", (quiz_id)
            )  # Delete the submissions as well.
            await conn.commit()  # Commit


main_cache = MathProblemCache(
    max_answer_length=100,
    max_question_limit=250,
    max_guild_problems=125,
    warnings_or_errors="errors",
)
