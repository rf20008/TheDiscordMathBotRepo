"""
The Discord Math Problem Bot Repo - DictConvertible
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
import logging
import typing
from copy import copy, deepcopy
from typing import *
import pickle
from warnings import warn

import aiosqlite
from ..parse_problem import convert_row_to_problem
from helpful_modules.dict_factory import dict_factory
from ..appeal import Appeal, AppealViewInfo
from ..base_problem import BaseProblem
from ..errors import *
from ..mysql_connector_with_stmt import mysql_connection
from ..quizzes import Quiz, QuizProblem, QuizSolvingSession, QuizSubmission
from ..quizzes.quiz_description import QuizDescription
from .appeals_related_cache import AppealsRelatedCache
log = logging.getLogger(__name__)


class MiscRelatedCache(AppealsRelatedCache):
    async def update_cache(self: "MathProblemCache") -> None:
        """Method revamped! This method updates the cache of the guilds, the guild problems, and the cache of the global problems. Takes O(N) time"""
        warn(message="update_cache hangs", category=PMDeprecationWarning, stacklevel=-1)
        await self.get_all_problems()
        guild_problems = {}

        guild_ids = []
        quiz_problems_dict = {}
        quiz_sessions_dict = {}
        quiz_submissions_dict = {}
        if self.use_sqlite:
            async with aiosqlite.connect(self.db_name) as conn:
                conn.row_factory = dict_factory
                cursor = await conn.cursor()
                await cursor.execute("SELECT * FROM quizzes")
                for Row in await cursor.fetchall():
                    quiz_problem = QuizProblem.from_row(Row, cache=copy(self))
                    # Add the problem to the cache
                    try:
                        quiz_problems_dict[quiz_problem.id].append(quiz_problem)
                    except KeyError:
                        quiz_problems_dict[quiz_problem.id] = [quiz_problem]
                await cursor.execute("SELECT submissions from quiz_submissions")
                for Row in await cursor.fetchall():
                    submission = QuizSubmission.from_dict(
                        pickle.loads(Row["submission"]), cache=copy(self)
                    )
                    try:
                        quiz_submissions_dict[submission.quiz_id].append(submission)
                    except KeyError:
                        quiz_submissions_dict[submission.quiz_id] = [submission]
                await cursor.execute("SELECT * FROM quiz_submission_sessions")
                for _row in await cursor.fetchall():
                        session = QuizSolvingSession.from_sqlite_dict(_row, cache=self)
                        try:
                            quiz_sessions_dict[session.quiz_id].append(session)
                        except KeyError:
                            quiz_sessions_dict[session.quiz_id] = [session]

        else:
            with mysql_connection(
                host=self.mysql_db_ip,
                password=self.mysql_password,
                user=self.mysql_username,
                database=self.mysql_db_name,
            ) as connection:
                cursor = connection.cursor(dictionaries=True)
                cursor.execute("SELECT * FROM problems")  # Get all problems
                for row in cursor.fetchall():
                    problem = convert_row_to_problem(row, cache=copy(self))
                    if (
                        problem.guild_id not in guild_ids
                    ):  # Similar logic: Make sure it's there!
                        guild_ids.append(problem.guild_id)
                        guild_problems[problem.guild_id] = (
                            {}
                        )  # For quick, cached access?
                    try:
                        guild_problems[problem.guild_id][problem.id] = problem
                    except BaseException as e:
                        raise SQLException(
                            "An error occurred while assigning the problem..."
                        ) from e
                cursor.execute("SELECT * FROM quizzes")  # Get all quiz problems
                for row in cursor.fetchall():
                    quiz_problem = QuizProblem.from_row(
                        row, cache=copy(self)
                    )  # Turn the quiz problems into QuizProblem objects
                    try:
                        quiz_problems_dict[quiz_problem.id].append(
                            quiz_problem
                        )  # Add it to the quiz with the given id
                    except KeyError:
                        quiz_problems_dict[quiz_problem.id] = [
                            quiz_problem
                        ]  # New quiz!
                # Similar log for quiz submissions
                cursor.execute("SELECT submissions from quiz_submissions")
                for row in cursor.fetchall():
                    submission = QuizSubmission.from_dict(
                        pickle.loads(row["submission"]), cache=copy(self)
                    )
                    try:
                        quiz_submissions_dict[submission.quiz_id].append(submission)
                    except KeyError:
                        quiz_submissions_dict[submission.quiz_id] = [submission]
                cursor.execute("SELECT * FROM quiz_submission_sessions")
                for _row in cursor.fetchall():
                    session = QuizSolvingSession.from_sqlite_dict(_row, cache=self)
                    try:
                        quiz_sessions_dict[session.quiz_id].append(session)
                    except KeyError:
                        quiz_sessions_dict[session.quiz_id] = [session]
        try:
            global_problems = deepcopy(
                guild_problems[None]
            )  # Must deepcopy or weird warnings will occur
            # TODO: fix this so this doesn't lead to errors
        except KeyError:  # No global problems yet
            global_problems = {}
        # Don't deepcopy the problems
        self.guild_problems = guild_problems
        self.guild_ids = guild_ids
        self.global_problems = global_problems
        self.cached_sessions = quiz_sessions_dict
        self.cached_quizzes = []  # Could cause a race condition
        for _id in quiz_problems_dict.keys():
            has_submissions = _id in list(
                quiz_submissions_dict.keys()
            )  # There could be a quiz with problems but not submissions
            if has_submissions:
                self.cached_quizzes.append(
                    Quiz(
                        _id,
                        quiz_problems=quiz_problems_dict[_id],
                        submissions=quiz_submissions_dict[_id],
                        existing_sessions=(
                            [quiz_sessions_dict[quiz_id]]
                            if quiz_id in quiz_sessions_dict.keys()
                            else []
                        ),
                        authors=set(
                            (problem.author for problem in quiz_submissions_dict[_id])
                        ),
                    )
                )

            else:
                self.cached_quizzes.append(
                    Quiz(
                        _id,
                        quiz_problems=quiz_problems_dict[_id],
                        submissions=[],
                        existing_sessions=(
                            [quiz_sessions_dict[quiz_id]]
                            if quiz_id in quiz_sessions_dict.keys()
                            else []
                        ),
                        authors=set(
                            (problem.author for problem in quiz_submissions_dict[_id])
                        ),
                    )
                )
        self.cached_submissions = quiz_submissions_dict.values()
        self.cached_submissions_organized_by_dict = quiz_submissions_dict
    async def get_all_by_user_id(self, user_id: int) -> dict:
        return self.get_all_by_author_id(user_id)
    async def get_all_by_author_id(self, author_id: int) -> dict:
        """Return a dictionary containing everything that was created by the author"""
        assert isinstance(author_id, int)  # Make sure it is of type integer
        if self.use_sqlite:
            async with aiosqlite.connect(self.db_name) as conn:
                conn.row_factory = dict_factory
                cursor = await conn.cursor()  # Create a cursor
                # Get all quiz problems they made
                await cursor.execute(
                    "SELECT * FROM quizzes WHERE author = ?", (int(author_id),)
                )  # Get all problems made by the author
                quiz_problems_raw = [
                    dict_factory(cursor, row) for row in await cursor.fetchall()
                ]  # Get the results and convert it to a dictionary
                quiz_problems = [
                    QuizProblem.from_row(item, cache=copy(self))
                    for item in quiz_problems_raw
                ]  # Convert the rows into QuizProblems, because these will be easier to use than rows will (and it will also be more readable)

                # Get the submissions now
                await cursor.execute(
                    "SELECT submissions FROM quiz_submissions WHERE user_id = ?",
                    (author_id,),
                )  # Get the submissions
                # Convert them to QuizSubmissions!
                quiz_submissions = [
                    QuizSubmission.from_dict(pickle.loads(item[0]), cache=copy(self))
                    for item in await cursor.fetchall()
                ]  # For each item: load it from bytes into a dictionary and
                # convert the dictionary into a QuizSubmission! However, I should just pickle it directly.

                # Get the problems the author made that are not attached to a quiz
                await cursor.execute(
                    "SELECT * FROM problems WHERE author = ?", (author_id,)
                )
                problems = [
                    convert_row_to_problem(row) for row in await cursor.fetchall()
                ]
                await cursor.execute(
                    """SELECT * FROM quiz_submission_sessions WHERE user_id = ?""",
                    (author_id,),
                )

                sessions = [
                    QuizSolvingSession.from_sqlite_dict(cache=self, dict=item)
                    for item in await cursor.fetchall()
                ]
                await cursor.execute(
                    "SELECT * FROM quiz_description WHERE author = ?", (author_id,)
                )
                descriptions = [
                    QuizDescription.from_dict(data, cache=self)
                    for data in await cursor.fetchall()
                ]
                await cursor.execute("SELECT * FROM appeals WHERE user_id=?", (author_id,))
                appeals = [
                    Appeal.from_dict(data, cache=self)
                    for data in await cursor.fetchall()
                ]
                await cursor.execute("SELECT * from appeal_view_infos WHERE user_id=?", (author_id))
                appeal_view_infos = [AppealViewInfo.from_dict(data) for data in await cursor.fetchall()]
        else:
            with mysql_connection(
                host=self.mysql_db_ip,
                password=self.mysql_password,
                user=self.mysql_username,
                database=self.mysql_db_name,
            ) as connection:
                cursor = connection.cursor(dictionaries=True)
                cursor.execute(
                    "SELECT * FROM quizzes WHERE author = '%s'", (author_id,)
                )
                quiz_problems = [
                    QuizProblem.from_row(row, cache=copy(self))
                    for row in cursor.fetchall()
                ]
                cursor.execute(
                    "SELECT submissions FROM quiz_submissions WHERE user_id = '%s'",
                    (author_id,),
                )
                quiz_submissions = [
                    QuizSubmission.from_dict(submission, cache=copy(self))
                    for submission in [
                        pickle.loads(item["submissions"]) for item in cursor.fetchall()
                    ]
                ]
                cursor.execute(
                    "SELECT * FROM problems WHERE author = '%s'", (author_id,)
                )
                problems = [
                    BaseProblem.from_dict(item, cache=copy(self))
                    for item in cursor.fetchall()
                ]
                cursor.execute(
                    "SELECT * FROM quiz_submission_sessions WHERE author = %s",
                    (author_id,),
                )
                sessions = [
                    QuizSolvingSession.from_mysql_dict(cache=self, dict=item)
                    for item in cursor.fetchall()
                ]
                cursor.execute(
                    "SELECT * FROM quiz_description WHERE author = %s", (author_id,)
                )
                descriptions = [
                    QuizDescription.from_dict(cache=self, data=data)
                    for data in cursor.fetchall()
                ]
                await cursor.execute("SELECT * FROM appeals WHERE user_id=%s", (author_id,))
                appeals = [
                    Appeal.from_dict(data, cache=self)
                    for data in await cursor.fetchall()
                ]
                await cursor.execute("SELECT * from appeal_view_infos WHERE user_id=?", (author_id))
                appeal_view_infos = [AppealViewInfo.from_dict(data) for data in await cursor.fetchall()]

        return {
            "quiz_problems": quiz_problems,
            "quiz_submissions": quiz_submissions,
            "problems": problems,
            "sessions": sessions,
            "descriptions_created": descriptions,
            "appeals": appeals,
            "appeal_view_infos": appeal_view_infos
        }

    async def delete_all_by_user_id(self, user_id: int) -> None:
        """Delete all data stored under a given user id"""
        assert isinstance(user_id, int)
        await self.del_user_data(user_id)
        if self.use_sqlite:
            async with aiosqlite.connect(self.db) as conn:
                cursor = await conn.cursor()
                await cursor.execute(
                    "DELETE FROM problems WHERE author = ?", (user_id,)
                )  # Delete all problems submitted by the author
                await cursor.execute(
                    "DELETE FROM quizzes WHERE author = ?", (user_id,)
                )  # Delete all quiz problems submitted by the author
                await cursor.execute(
                    "DELETE FROM quiz_submissions WHERE user_id = ?", (user_id,)
                )  # Delete all quiz submissions created by the author
                await cursor.execute(
                    "DELETE FROM quiz_submission_sessions WHERE user_id = ?", (user_id,)
                )
                await cursor.execute(
                    "DELETE FROM quiz_description WHERE author= ?", (user_id,)
                )
                await cursor.execute("DELETE FROM appeals WHERE user_id=?", (user_id,))
                await cursor.execute("DELETE FROM appeal_view_infos WHERE user_id=?", (user_id,))
                await conn.commit()  # Otherwise, nothing happens and it rolls back!!
        else:
            with mysql_connection(
                host=self.mysql_db_ip,
                password=self.mysql_password,
                user=self.mysql_username,
                database=self.mysql_db_name,
            ) as connection:
                cursor = connection.cursor(dictionaries=True)
                cursor.execute("DELETE FROM problems WHERE author = '%s'", (user_id,))
                cursor.execute("DELETE FROM quizzes WHERE author = '%s'", (user_id,))
                cursor.execute(
                    "DELETE FROM quiz_submissions WHERE author = '%s'", (user_id,)
                )
                cursor.execute(
                    "DELETE FROM quiz_submission_sessions WHERE author = %s", (user_id,)
                )
                cursor.execute(
                    "DELETE FROM quiz_description WHERE author = %s", (user_id,)
                )
                await cursor.execute("DELETE FROM appeals WHERE user_id=%s", (user_id,))
                await cursor.execute("DELETE FROM appeal_view_infos WHERE user_id=?", (user_id,))
                connection.commit()

    async def delete_all_by_guild_id(self, guild_id: int) -> None:
        """Delete all data stored by a given guild. This deletes all problems & quizzes & quiz submissions under that guild!"""
        if guild_id is None:
            raise MathProblemsModuleException(
                "You are not allowed to delete global problems!"
            )
        assert isinstance(guild_id, int)
        if self.use_sqlite:
            async with aiosqlite.connect(self.db) as conn:
                cursor = await conn.cursor()
                await cursor.execute(
                    "DELETE FROM problems WHERE guild_id = ?", (guild_id,)
                )  # Delete all problems from the guild
                await cursor.execute(
                    "DELETE FROM quizzes WHERE guild_id = ?", (guild_id,)
                )  # Delete all quiz problems from the guild
                await cursor.execute(
                    "DELETE FROM quiz_submissions WHERE guild_id = ?", (guild_id,)
                )
                await cursor.execute(
                    "DELETE FROM quiz_submission_sessions WHERE guild_id = ?",
                    (guild_id,),
                )  # Delete all quiz submissions from the guild!
                await cursor.execute(
                    "DELETE FROM quiz_description WHERE guild_id = %s", (guild_id,)
                )
                await cursor.execute("DELETE FROM appeal_view_infos WHERE guild_id=?", (guild_id,))
                await conn.commit()  # Otherwise, nothing happens!
        else:
            with mysql_connection(
                host=self.mysql_db_ip,
                password=self.mysql_password,
                user=self.mysql_username,
                database=self.mysql_db_name,
            ) as connection:
                cursor = connection.cursor(dictionaries=True)
                cursor.execute(
                    "DELETE FROM problems WHERE guild_id = %s", (guild_id,)
                )  # Remove all guild problems from this guild
                cursor.execute(
                    "DELETE FROM quizzes WHERE guild_id = %s", (guild_id,)
                )  # Remove all quizzes from the guild
                cursor.execute(
                    "DELETE FROM quiz_submissions WHERE guild_id = %s", (guild_id,)
                )  # Remove all quiz submissions as well
                cursor.execute(
                    "DELETE FROM quiz_submission_sessions WHERE guild_id = %s",
                    (guild_id,),
                )
                cursor.execute(
                    "DELETE FROM quiz_description WHERE guild_id = %s", (guild_id,)
                )
                await cursor.execute("DELETE FROM appeal_view_infos WHERE guild_id=?", (guild_id,))
                # uh oh - we don't have a guild id
                connection.commit()

    def __bool__(self):
        """Return bool(self)"""
        return True

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

    async def initialize_sql_table(self):
        """Initialize my internal SQL tables. This does nothing if the internal SQL tables already exist!"""
        log.info("Initializing my internal SQL tables")
        await super().initialize_sql_table()
        if self.use_sqlite:
            async with aiosqlite.connect(self.db_name) as conn:
                cursor = await conn.cursor()
                await cursor.execute(
                    """CREATE TABLE IF NOT EXISTS problems (
                        guild_id INT,
                        problem_id INT,
                        question TEXT(2000) NOT NULL,
                        answers BLOB NOT NULL, 
                        author INT NOT NULL,
                        voters BLOB NOT NULL,
                        solvers BLOB NOT NULL,
                        extra_stuff TEXT(20000) NOT NULL
                        )"""
                )  # Blob types will be compiled with pickle.loads() and pickle.dumps() (they are lists)
                # author: int = user_id
                # Create table of problems
                log.debug("Created problems table")
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
                log.debug("Created quizzes table")
                await cursor.execute(
                    """CREATE TABLE IF NOT EXISTS quiz_submissions (
                    guild_id INT,
                    quiz_id INT NOT NULL,
                    user_id INT NOT NULL,
                    submissions BLOB NOT NULL
                    )"""
                )  # as dictionary
                # Used to store submissions!
                log.debug("Created submissions table")
                await cursor.execute(
                    """CREATE TABLE IF NOT EXISTS user_data (
                    USER_ID INT,
                    trusted INT NOT NULL,
                    denylisted INT NOT NULL)"""  # will use bool(val) because SQLite doesn't support booleans
                )
                await cursor.execute(
                    """CREATE TABLE IF NOT EXISTS quiz_submission_sessions (
                    quiz_id INT NOT NULL,
                    user_id INT NOT NULL,
                    is_finished INT,
                    start_time INT,
                    expire_time INT,
                    guild_id INT,
                    answers BLOB,
                    special_id VARCHAR,
                    attempt_num INT
                    )"""
                )  # Special_id is for avoiding the weird bug with 'and' not working in SQL statements
                await cursor.execute(
                    """CREATE TABLE IF NOT EXISTS quiz_description (
                                               description VARCHAR,
                                               quiz_id INT PRIMARY KEY,
                                               time_limit INT,
                                               intensity FLOAT,
                                               license VARCHAR,
                                               category VARCHAR,
                                               author INT,
                                               guild_id INT
                                               )
                                               """
                )
                await cursor.execute(
                    """CREATE TABLE IF NOT EXISTS guild_data (
                    denylisted INT,
                    guild_id INT PRIMARY KEY,
                    can_create_problems_check VARCHAR,
                    can_create_quizzes_check VARCHAR,
                    mod_check VARCHAR
                    )
                    """
                )
                # Maybe SQL won't understand enums... but that's ok :)
                log.debug("Created user_data table")
                await conn.commit()  # Otherwise, when this closes, the database just reverted!
                log.debug("Saved!")
        else:
            with mysql_connection(
                host=self.mysql_db_ip,
                password=self.mysql_password,
                user=self.mysql_username,
                database=self.mysql_db_name,
            ) as connection:
                cursor = connection.cursor(dictionaries=True)
                log.debug("Created cursor")
                cursor.execute(
                    """CREATE TABLE IF NOT EXISTS problems (
                        guild_id BIGINT,
                        problem_id BIGINT NOT NULL,
                        question TEXT(2000) NOT NULL,
                        answers BLOB NOT NULL, 
                        author BIGINT NOT NULL,
                        voters BLOB NOT NULL,
                        solvers BLOB NOT NULL,
                        extra_stuff TEXT(20000) NOT NULL
                        )"""
                )  # Blob types will be compiled with pickle.loads() and pickle.dumps() (they are lists)
                # author: int = user_id
                log.debug("Created problems table!")
                cursor.execute(
                    """CREATE TABLE IF NOT EXISTS quizzes (
                    guild_id BIGINT,
                    quiz_id BIGINT NOT NULL PRIMARY KEY,
                    problem_id BIGINT NOT NULL,
                    question TEXT(500) NOT NULL,
                    answer BLOB NOT NULL,
                    voters BLOB NOT NULL,
                    author BIGINT NOT NULL,
                    solvers BLOB NOT NULL
                )"""
                )
                log.debug("Created quizzes table")
                cursor.execute(
                    """CREATE TABLE IF NOT EXISTS quiz_submissions (
                    guild_id BIGINT,
                    quiz_id BIGINT NOT NULL,
                    user_id BIGINT NOT NULL,
                    submissions BLOB NOT NULL
                    )"""
                )  # as dictionary
                # Used to store submissions
                log.debug("Created submissions table")
                cursor.execute(
                    """CREATE TABLE IF NOT EXISTS user_data (
                    user_id INT,
                    trusted BOOLEAN DEFAULT false,
                    denylisted BOOLEAN DEFAULT false
                    )"""
                )
                cursor.execute(
                    """CREATE TABLE IF NOT EXISTS quiz_submission_sessions (
                    quiz_id INT NOT NULL,
                    user_id INT NOT NULL,
                    is_finished INT,
                    start_time INT,
                    expire_time INT,
                    guild_id INT,
                    answers BLOB,
                    special_id VARCHAR,
                    attempt_num INT
                    )"""
                )
                cursor.execute(
                    """CREATE TABLE IF NOT EXISTS quiz_description ("
                               description VARCHAR,
                               quiz_id INT PRIMARY KEY,
                               time_limit INT,
                               intensity FLOAT,
                               license VARCHAR,
                               category VARCHAR,
                               author INT,
                               guild_id INT,
                               )
                               """
                )
                cursor.execute(
                    """CREATE TABLE IF NOT EXISTS guild_data (
                    denylisted INT,
                    guild_id INT,
                    can_create_problems_check VARCHAR,
                    can_create_quizzes_check VARCHAR,
                    mod_check VARCHAR,
                    )
                    """
                )
                # TODO: test whether SQL can serialize enums
                # I don't know whether SQL can serialize enums
                log.debug("Created user data table")
                connection.commit()
                log.debug("Saved tables!")
