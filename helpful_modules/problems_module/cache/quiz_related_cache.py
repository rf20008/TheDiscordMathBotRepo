import logging
import pickle
import typing
from copy import copy
from typing import *

import aiosqlite

from helpful_modules.dict_factory import dict_factory

from ..errors import *
from ..mysql_connector_with_stmt import *
from ..quizzes import Quiz, QuizProblem, QuizSolvingSession, QuizSubmission
from ..quizzes.quiz_description import QuizDescription
from .problems_related_cache import ProblemsRelatedCache

log = logging.getLogger(__name__)


class QuizRelatedCache(ProblemsRelatedCache):
    """An extension of ProblemsRelatedCache that contains"""

    async def get_quiz_sessions(self, quiz_id: int) -> List[QuizSolvingSession]:
        """Get the quiz sessions for a quiz"""
        assert isinstance(quiz_id, int)
        if self.use_sqlite:
            async with aiosqlite.connect(self.db) as conn:
                conn.row_factory = dict_factory
                cursor = await conn.cursor()
                await cursor.execute("SELECT * WHERE quiz_id = ?", (quiz_id,))
                # For each row retrieved: use from_sqlite_dict to turn into a QuizSolvingSession and return it
                return [
                    QuizSolvingSession.from_sqlite_dict(item)
                    for item in await cursor.fetchall()
                ]
        else:
            with mysql_connection(
                host=self.mysql_db_ip,
                password=self.mysql_password,
                user=self.mysql_username,
                database=self.mysql_db_name,
            ) as connection:
                cursor = connection.cursor(dictionaries=True)
                cursor.execute(
                    "SELECT * FROM quiz_submission_sessions WHERE quiz_id = %s",
                    (quiz_id,),
                )
                # For each row retrieved: turn it into a QuizSolvingSession using from_mysql_dict and return the result
                return [
                    QuizSolvingSession.from_mysql_dict(item)
                    for item in cursor.fetchall()
                ]

    async def add_quiz_session(self, session: QuizSolvingSession):
        """Add a QuizSession to the SQL database"""
        assert isinstance(session, QuizSolvingSession)
        try:
            await self.get_quiz_submission_by_special_id(session.special_id)
            raise MathProblemsModuleException("Quiz session already exists")
        except QuizSessionNotFoundException:
            pass

        if self.use_sqlite:
            async with aiosqlite.connect(self.db_name) as conn:
                conn.row_factory = dict_factory
                cursor = await conn.cursor()
                await cursor.execute(
                    """INSERT INTO quiz_submission_sessions (user_id, quiz_id, guild_id, is_finished, answers, start_time, expire_time, special_id, attempt_num)
                    VALUES (?,?,?,?,?,?,?,?)""",
                    (
                        session.user_id,
                        session.quiz_id,
                        session.guild_id,
                        int(session.is_finished),
                        pickle.dumps(session.answers),
                        session.start_time,
                        session.expire_time,
                        session.special_id,
                        session.attempt_num,
                    ),
                )
                await conn.commit()
                return
        else:
            with mysql_connection(
                host=self.mysql_db_ip,
                password=self.mysql_password,
                user=self.mysql_username,
                database=self.mysql_db_name,
            ) as connection:
                cursor = connection.cursor(dictionaries=True)
                cursor.execute(
                    """INSERT INTO quiz_submission_sessions (user_id, quiz_id, guild_id, is_finished, answers, start_time, expire_time, special_id, attempt_num)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (
                        session.user_id,
                        session.quiz_id,
                        session.guild_id,
                        int(session.is_finished),
                        pickle.dumps(
                            session.answers
                        ),  # TODO: don't use pickle (because RCE)
                        session.start_time,
                        session.expire_time,
                        session.special_id,
                        session.attempt_num,
                    ),
                )
                connection.commit()

    async def update_quiz_session(self, special_id: int, session: QuizSolvingSession):
        """Update the quiz session given the special id"""
        assert isinstance(special_id, int)
        assert isinstance(session, QuizSolvingSession)
        try:
            await self.get_quiz_submission_by_special_id(special_id)
        except QuizSessionNotFoundException as quiz_session_not_found_exception:
            raise QuizSessionNotFoundException(
                "Quiz session not found - use add_quiz_session instead"
            ) from quiz_session_not_found_exception

        if self.use_sqlite:
            async with aiosqlite.connect(self.db_name) as conn:
                conn.row_factory = dict_factory
                cursor = await conn.cursor()
                await cursor.execute(
                    """UPDATE quiz_submission_sessions 
                    SET guild_id = ?, quiz_id = ?, user_id = ?, answers = ?, start_time = ?, expire_time = ?, is_finished = ?, special_id = ?, attempt_num = ?
                    WHERE special_id = ?""",
                    (
                        session.guild_id,
                        session.quiz_id,
                        session.user_id,
                        pickle.dumps(session.answers),
                        session.start_time,
                        session.expire_time,
                        int(session.is_finished),
                        session.special_id,
                        session.attempt_num,
                        session.special_id,
                    ),
                )
                await conn.commit()
                return
        else:
            with mysql_connection(
                host=self.mysql_db_ip,
                password=self.mysql_password,
                user=self.mysql_username,
                database=self.mysql_db_name,
            ) as connection:
                cursor = connection.cursor(dictionaries=True)
                cursor.execute(  # Connect to SQL and actually change it
                    """UPDATE quiz_submission_sessions 
                    SET guild_id = %s, quiz_id = %s, user_id = %s, answers = %s, start_time = %s, expire_time = %s, is_finished = %s, special_id = %s, attempt_num = %s
                    WHERE special_id = %s""",
                    (
                        session.guild_id,
                        session.quiz_id,
                        session.user_id,
                        pickle.dumps(session.answers),
                        session.start_time,
                        session.expire_time,
                        int(session.is_finished),
                        session.special_id,
                        session.attempt_num,
                        session.special_id,
                    ),
                )
                connection.commit()
                return

    async def delete_quiz_session(self, special_id: int):
        """DELETE a quiz session!"""
        assert isinstance(special_id, int)  # basic type-checking

        if self.use_sqlite:
            async with aiosqlite.connect(self.db_name) as conn:
                cursor = await conn.cursor()
                await cursor.execute(
                    "DELETE FROM quiz_submission_sessions WHERE special_id = ?",
                    (special_id,),
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
                    "DELETE FROM quiz_submission_session WHERE special_id=%s",
                    (special_id,),
                )
                connection.commit()

    async def get_quiz_session_by_special_id(
        self, special_id: int
    ) -> QuizSolvingSession:
        """Get a quiz submission by its special id"""
        assert isinstance(special_id, int)  # Basic type-checking

        if self.use_sqlite:
            async with aiosqlite.connect(self.db_name) as conn:
                cursor = await conn.cursor()
                await cursor.execute(
                    "SELECT * FROM quiz_submission_sessions WHERE special_id = ?",
                    (special_id,),
                )
                potential_sessions = list(await cursor.fetchall())
                if len(potential_sessions) < 1:
                    raise QuizSessionNotFoundException(
                        "There aren't any quiz sessions found with this special id"
                    )
                elif len(potential_sessions) > 1:
                    raise MathProblemsModuleException(
                        "There are too many quiz sessions with this special id"
                    )
                else:
                    return QuizSolvingSession.from_sqlite_dict(potential_sessions[0])
        else:
            with mysql_connection(
                host=self.mysql_db_ip,
                password=self.mysql_password,
                user=self.mysql_username,
                database=self.mysql_db_name,
            ) as connection:
                cursor = connection.cursor(dictionaries=True)
                cursor.execute(
                    "SELECT * FROM quiz_submission_sessions WHERE special_id = %s",
                    (special_id,),
                )
                potential_sessions = list(cursor.fetchall())
                if len(potential_sessions) < 1:
                    raise QuizSessionNotFoundException(
                        "There aren't any quiz sessions found with this special id"
                    )
                elif len(potential_sessions) > 1:
                    raise MathProblemsModuleException(
                        "There are too many quiz sessions with this special id"
                    )
                else:
                    return QuizSolvingSession.from_mysql_dict(
                        potential_sessions[0], cache=self
                    )

    async def add_quiz(self, quiz: Quiz) -> Quiz:
        """Add a quiz"""
        assert isinstance(quiz, Quiz)
        if not quiz.empty:
            num_already_existing_quizzes = await self.get_quizzes_by_func(
                func=lambda _quiz: not _quiz.empty and _quiz.guild_id == quiz.guild_id  # type: ignore
            )
            if len(num_already_existing_quizzes) >= self.cache.max_quizzes_per_guild:
                raise TooManyQuizzesException(len(num_already_existing_quizzes) + 1)
        try:
            await self.get_quiz(quiz.id)
            raise MathProblemsModuleException(
                "Quiz already exists! Use update_quiz instead"
            )
        except QuizNotFound:
            pass
        if self.use_sqlite:
            async with aiosqlite.connect(self.db_name) as conn:
                try:
                    conn.row_factory = dict_factory  # Make sure the row_factory can be set to dict_factory
                except BaseException as exc:
                    # Not writeable?
                    try:
                        dict_factory()  # Check for name error
                    except NameError as exc2:
                        raise MathProblemsModuleException(
                            "dict_factory could not be found"
                        ) from exc2
                    if isinstance(exc, AttributeError):  # Can't set attribute
                        pass
                    else:
                        raise  # Re-raise the exception

                cursor = await conn.cursor()
                for item in quiz.problems:
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
        else:
            with mysql_connection(
                host=self.mysql_db_ip,
                password=self.mysql_password,
                user=self.mysql_username,
                database=self.mysql_db_name,
            ) as connection:
                cursor = connection.cursor(dictionaries=True)
                for item in quiz.problems:
                    cursor.execute(
                        """INSERT INTO quizzes (guild_id, quiz_id, problem_id, question, answer, voters, solvers, author)
                    VALUES ('%s','%s','%s',%s,%s,%s,%s,'%s')""",
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
                    cursor.execute(
                        """INSERT INTO quiz_submissions (guild_id, quiz_id, user_id, submissions)
                    VALUES ('%s','%s','%s',%s)""",
                        (
                            item.guild_id,
                            item.quiz_id,
                            item.user_id,
                            pickle.dumps(item.to_dict()),
                        ),
                    )
        return quiz

    def __str__(self):
        raise NotImplementedError

    async def get_quiz(self, quiz_id: int) -> Optional[Quiz]:
        """Get the quiz with the id specified. Returns None if not found"""
        assert isinstance(quiz_id, int)
        if self.use_sqlite:
            async with aiosqlite.connect(self.db_name) as conn:
                try:
                    conn.row_factory = dict_factory  # Make sure the row_factory can be set to dict_factory
                except BaseException as exc:
                    # Not writeable?
                    try:
                        dict_factory()  # Check for name error
                    except NameError as exc2:
                        raise MathProblemsModuleException(
                            "dict_factory could not be found"
                        ) from exc2
                    if isinstance(exc, AttributeError):  # Can't set attribute
                        pass
                    else:
                        raise  # Re-raise the exception
                cursor = await conn.cursor()
                await cursor.execute(
                    "SELECT * FROM quizzes WHERE quiz_id=?", (quiz_id,)
                )
                problems = list(await cursor.fetchall())
                if len(problems) == 0:
                    raise QuizNotFound(f"Quiz id {quiz_id} not found")

                await cursor.execute(
                    "SELECT submissions FROM quiz_submissions WHERE quiz_id = ?"
                )
                submissions = await cursor.fetchall()
                submissions = [
                    QuizSubmission.from_dict(pickle.loads(item[0]), cache=copy(self))
                    for item in submissions
                ]
                problems = [
                    QuizProblem.from_row(dict_factory(cursor, row), cache=copy(self))
                    for row in problems
                ]
        else:
            with mysql_connection(
                host=self.mysql_db_ip,
                password=self.mysql_password,
                user=self.mysql_username,
                database=self.mysql_db_name,
            ) as connection:
                cursor = connection.cursor(dictionaries=True)
                cursor.execute("SELECT * FROM quizzes WHERE quiz_id = '%s'", (quiz_id,))
                problems = [
                    QuizProblem.from_row(row, copy(self)) for row in cursor.fetchall()
                ]
                cursor.execute(
                    "SELECT * FROM submissions WHERE quiz_id = '%s'", (quiz_id,)
                )
                submissions = [
                    QuizSubmission.from_dict(pickle.loads(row[0]), cache=copy(self))
                    for row in cursor.fetchall()
                ]
        authors = set((problem.author for problem in problems))
        sessions = await self.get_quiz_sessions(quiz_id)
        description = await self.get_quiz_description(quiz_id)
        quiz = Quiz(
            quiz_id,
            problems,
            submissions,
            cache=self,
            authors=authors,  # type: ignore
            existing_sessions=sessions,
            description=description,
        )
        return quiz

    async def update_quiz(self, quiz_id: int, new: Quiz) -> None:
        """Update the quiz with the id given"""
        # Because quizzes consist of multiple rows, it would be hard/impossible to replace each row one at a time
        assert isinstance(quiz_id, int)
        assert isinstance(new, Quiz)
        assert new.id == quiz_id
        await self.delete_quiz(quiz_id)

        await self.add_quiz(new)

    async def delete_quiz(self, quiz_id: int):
        """Delete a quiz!"""
        if self.use_sqlite:
            async with aiosqlite.connect(self.db_name) as conn:
                cursor = await conn.cursor()
                await cursor.execute(
                    "DELETE FROM quizzes WHERE quiz_id = ?", (quiz_id,)
                )  # Delete the quiz's problems
                await cursor.execute(
                    "DELETE FROM quiz_submissions WHERE quiz_id=?", (quiz_id,)
                )  # Delete the submissions as well.
                await cursor.execute(
                    "DELETE FROM quiz_submission_sessions WHERE quiz_id = ?", (quiz_id,)
                )  # Delete the sessions associated with it
                await cursor.execute(
                    "DELETE from quiz_description WHERE quiz_id = ?", (quiz_id,)
                )
                await conn.commit()  # Commit
        else:
            with mysql_connection(
                host=self.mysql_db_ip,
                password=self.mysql_password,
                user=self.mysql_username,
                database=self.mysql_db_name,
            ) as connection:
                cursor = connection.cursor(dictionaries=True)
                cursor.execute(
                    "DELETE FROM quizzes WHERE quiz_id = '?'", (quiz_id,)
                )  # Delete the quiz's problems
                cursor.execute(
                    "DELETE FROM quiz_submissions WHERE quiz_id='?'", (quiz_id,)
                )  # Delete the submissions as well.
                cursor.execute(
                    "DELETE FROM quiz_submission_sessions WHERE quiz_id = ?", (quiz_id,)
                )  # Delete the sessions associated with it
                connection.commit()

    async def get_quiz_description(self, quiz_id: int) -> QuizDescription:
        """Get a quiz description from a quiz id"""
        assert isinstance(quiz_id, int)
        if self.use_sqlite:
            async with aiosqlite.connect(self.db_name) as conn:
                conn.row_factory = dict_factory
                cursor = await conn.cursor()
                await cursor.execute(
                    "SELECT * FROM quiz_description WHERE quiz_id = ?", (quiz_id,)
                )
                possible_quiz_descriptions = await cursor.fetchall()
                if len(possible_quiz_descriptions) == 0:
                    raise QuizDescriptionNotFoundException("Quiz description not found")
                elif len(possible_quiz_descriptions) > 1:
                    raise MathProblemsModuleException(
                        "There are too many quiz descriptions with the same id!"
                    )
                return QuizDescription.from_dict(
                    possible_quiz_descriptions[0], cache=self
                )
        else:
            with mysql_connection(
                host=self.mysql_db_ip,
                password=self.mysql_password,
                user=self.mysql_username,
                database=self.mysql_db_name,
            ) as connection:
                cursor = connection.cursor(dictionaries=True)
                cursor.execute(
                    "SELECT * FROM quiz_description WHERE quiz_id = ?", (quiz_id,)
                )
                possible_quiz_descriptions = cursor.fetchall()
                if len(possible_quiz_descriptions) == 0:
                    raise QuizDescriptionNotFoundException("Quiz description not found")
                elif len(possible_quiz_descriptions) > 1:
                    raise MathProblemsModuleException(
                        "There are too many quiz descriptions with the same id!"
                    )
                return QuizDescription.from_dict(
                    possible_quiz_descriptions[0], cache=self
                )

    async def update_quiz_description(self, quiz_id: int, description: QuizDescription):
        """Update quiz description"""
        assert isinstance(quiz_id, int)
        assert isinstance(description, QuizDescription)
        try:
            await self.get_quiz_description(quiz_id)
        except QuizDescriptionNotFoundException:
            raise QuizDescriptionNotFoundException(
                "Quiz description not found - you need to use add_quiz_description instead"
            )

        if self.use_sqlite:
            async with aiosqlite.connect(self.db_name) as conn:
                cursor = await conn.cursor()
                await cursor.execute(
                    """UPDATE quiz_description
                    SET description = ?, license = ?, time_limit = ?, intensity = ?, category = ?, quiz_id = ?, author = ?, guild_id = ?
                    WHERE quiz_id = ?""",
                    (
                        description.description,
                        description.license,
                        description.time_limit,
                        description.intensity,
                        description.category,
                        description.quiz_id,
                        description.author,
                        description.guild_id,
                        description.quiz_id,
                    ),
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
                    """UPDATE quiz_description
                    SET description = %s, license = %s, time_limit = %s, intensity = %s, category = %s, quiz_id = %s, author = %s, guild_id = %s
                    WHERE quiz_id = %s""",
                    (
                        description.description,
                        description.license,
                        description.time_limit,
                        description.intensity,
                        description.category,
                        description.quiz_id,
                        description.author,
                        description.guild_id,
                        description.quiz_id,
                    ),
                )
                connection.commit()

    async def add_quiz_description(self, description: QuizDescription):
        """Add quiz description"""
        assert isinstance(description, QuizDescription)
        try:
            await self.get_quiz_description(description.quiz_id)
            raise MathProblemsModuleException("Quiz description already exists")
        except QuizDescriptionNotFoundException:
            pass
        if self.use_sqlite:
            async with aiosqlite.connect(self.db_name) as conn:
                conn.row_factory = dict_factory
                cursor = await conn.cursor()
                await cursor.execute(
                    """INSERT INTO quiz_description (description, license, time_limit, intensity, quiz_id, author, category. guild_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        # These will replace the ?'s
                        description.description,
                        description.license,
                        description.time_limit,
                        description.intensity,
                        description.quiz_id,
                        description.author,
                        description.category,
                        description.guild_id,
                    ),
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
                    """INSERT INTO quiz_description (description, license, time_limit, intensity, quiz_id, author, category, guild_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s. %s)
                    """,
                    (
                        # These will replace the ?'s
                        description.description,
                        description.license,
                        description.time_limit,
                        description.intensity,
                        description.quiz_id,
                        description.author,
                        description.category,
                        description.guild_id,
                    ),
                )
                connection.commit()

    async def delete_quiz_description(self, quiz_id: int):
        """DELETE quiz description!"""

        assert isinstance(quiz_id, int)
        if self.use_sqlite:
            async with aiosqlite.connect(self.db) as conn:
                cursor = await conn.cursor()
                await cursor.execute(
                    "DELETE * FROM quiz_description WHERE quiz_id = ?", (quiz_id,)
                )  # Delete it
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
                    "DELETE * FROM quiz_description WHERE quiz_id = ?", (quiz_id,)
                )  # Delete it
                connection.commit()

    async def get_quizzes_by_func(
        self: "QuizRelatedCache",
        func: typing.Callable[[Quiz, Any], bool] = lambda quiz: False,
        args: typing.Union[tuple, list] = None,
        kwargs: dict = None,
    ) -> typing.List[Quiz]:
        """Get the quizzes that match the function.
        Function is a function that takes in the quiz, and the provided arguments and keyword arguments.
        Return something True-like to signify you want the quiz in the list, and False-like to signify you don't.
        """
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}
        await self.update_cache()
        return [quiz for quiz in self.cached_quizzes if func(quiz, *args, **kwargs)]  # type: ignore

    async def initialize_sql_table(self):
        """Initialize the SQL tables if they don't already exist"""
        await super().initialize_sql_table()  # Initialize base problem-related tables

        if self.use_sqlite:
            async with aiosqlite.connect(self.db_name) as conn:
                cursor = await conn.cursor()
                await cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS quiz_description (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        quiz_id INTEGER,
                        description TEXT,
                        license TEXT,
                        time_limit INTEGER,
                        intensity REAL,
                        category TEXT,
                        author INTEGER,
                        guild_id INTEGER,
                        FOREIGN KEY (quiz_id) REFERENCES quizzes(quiz_id)
                    )
                    """
                )
                await cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS quizzes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        guild_id INTEGER,
                        quiz_id INTEGER,
                        problem_id INTEGER,
                        question TEXT,
                        answer BLOB,
                        voters BLOB,
                        solvers BLOB,
                        author INTEGER,
                        FOREIGN KEY (quiz_id) REFERENCES quiz_description(quiz_id)
                    )
                    """
                )
                await cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS quiz_submissions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        guild_id INTEGER,
                        quiz_id INTEGER,
                        user_id INTEGER,
                        submissions BLOB,
                        FOREIGN KEY (quiz_id) REFERENCES quiz_description(quiz_id)
                    )
                    """
                )
                await cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS quiz_submission_sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        quiz_id INTEGER,
                        guild_id INTEGER,
                        is_finished INTEGER,
                        answers BLOB,
                        start_time INTEGER,
                        expire_time INTEGER,
                        special_id INTEGER,
                        attempt_num INTEGER,
                        FOREIGN KEY (quiz_id) REFERENCES quiz_description(quiz_id)
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
                    CREATE TABLE IF NOT EXISTS quiz_description (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        quiz_id INT,
                        description TEXT,
                        license TEXT,
                        time_limit INT,
                        intensity REAL,
                        category TEXT,
                        author INT,
                        guild_id INT,
                        FOREIGN KEY (quiz_id) REFERENCES quizzes(quiz_id)
                    )
                    """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS quizzes (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        guild_id INT,
                        quiz_id INT,
                        problem_id INT,
                        question TEXT,
                        answer LONGBLOB,
                        voters LONGBLOB,
                        solvers LONGBLOB,
                        author INT,
                        FOREIGN KEY (quiz_id) REFERENCES quiz_description(quiz_id)
                    )
                    """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS quiz_submissions (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        guild_id INT,
                        quiz_id INT,
                        user_id INT,
                        submissions LONGBLOB,
                        FOREIGN KEY (quiz_id) REFERENCES quiz_description(quiz_id)
                    )
                    """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS quiz_submission_sessions (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        user_id INT,
                        quiz_id INT,
                        guild_id INT,
                        is_finished INT,
                        answers LONGBLOB,
                        start_time INT,
                        expire_time INT,
                        special_id INT,
                        attempt_num INT,
                        FOREIGN KEY (quiz_id) REFERENCES quiz_description(quiz_id)
                    )
                    """
                )
                connection.commit()
