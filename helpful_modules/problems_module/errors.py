"""
You can distribute any version of the Software created and distributed *before* 23:17:55.00 July 28, 2024 GMT-4
under the GNU General Public License version 3 or at your option, any  later option.
But versions of the code created and/or distributed *on or after* that date must be distributed
under the GNU *Affero* General Public License, version 3, or, at your option, any later version.

TheDiscordMathProblemBotRepo - Errors

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


class MathProblemsModuleException(Exception):
    """The base exception for problems_module."""

    pass


class BGSaveNotSupportedOnSQLException(MathProblemsModuleException):
    """Raised when someone tries to call .bgsave but we're using SQL (BGsave is only used in redis"""

    pass


class TooLongArgument(MathProblemsModuleException):
    """Raised when an argument passed into MathProblem() is too long."""

    pass


class TooLongAnswer(TooLongArgument):
    """Raised when an answer is too long."""

    pass


class TooLongQuestion(TooLongArgument):
    """Raised when a question is too long."""

    pass


class GuildAlreadyExistsException(MathProblemsModuleException):
    """Raised when MathProblemCache.add_empty_guild tries to run on a guild that already has problems."""

    pass


class TooManyProblems(MathProblemsModuleException):
    """Raised when trying to add problems when there is already the maximum number of problems."""

    pass


class ThingNotFound(KeyError, IndexError, MathProblemsModuleException):
    """Raised when a thing is not found"""

    pass


class ProblemNotFound(ThingNotFound):
    """Raised when a problem isn't found"""

    pass


class ProblemNotFoundException(ProblemNotFound):
    """Raised when a problem is not found."""

    pass


class ProblemNotWrittenException(ThingNotFound):
    """Raised when trying to grade a written problem but the problem is not a written problem"""

    pass


class QuizAlreadySubmitted(MathProblemsModuleException):
    """Raised when trying to submit a quiz that has already been submitted"""

    pass


class SQLException(MathProblemsModuleException):
    """Raised when an error happens relating to SQL!"""

    pass


class MySQLException(SQLException, aiomysql.Error):
    """A generic MYSQL exception"""

    def __init__(self, message, base_error):
        SQLException.__init__(self, message)
        self.base_error = base_error


class QuizNotFound(ThingNotFound):
    """Raised when a quiz isn't found"""

    pass



class SessionNotFound(ThingNotFound):
    """Raised when a Session isn't found"""
    pass


class VerificationCodeInfoNotFound(ThingNotFound):
    """Raised when verification code information is not found"""

    pass


class AppealViewInfoNotFound(ThingNotFound):
    """Raised when appeal view info is not found"""

    pass


class FormatException(KeyError, MathProblemsModuleException):
    """Raised when something is not formatted correctly"""

    pass


class IsRowException(FormatException):
    """Raised when expecting a dictionary but got a row instead."""

    pass


class TooMuchUserDataException(FormatException):
    """Raised when there is too much user data!"""

    pass


class UserDataNotExistsException(ThingNotFound):
    """Raised by MathProblemCache.set_user_data when user data does not exist!"""

    pass


class TooManyQuizzesException(MathProblemsModuleException):
    """Raised a guild has too many quizzes"""

    def __init__(self, num_quizzes: int):
        message: str = (
            f"The guild already has {num_quizzes} quizzes, which is too much!"
        )
        super().__init__(message)


class QuizSessionNotFoundException(ThingNotFound):
    """Raised when trying to find quiz sessions but they are not found"""

    pass


class QuizSessionOvertimeException(MathProblemsModuleException):
    """Raised when a quiz session is attempted to be modified but they ran out of time"""

    pass


class QuizDescriptionNotFoundException(ThingNotFound):
    """Raised when Quiz Description is not found"""

    pass


class InvalidDictionaryInDatabaseException(FormatException):
    """Raised when a dictionary is expected in the database as part of a string data type, but it could not be compiled"""

    def __init__(self, msg: str):
        super().__init__(msg)

    @classmethod
    def from_invalid_data(cls, invalid_data: str):
        return cls(
            f"""I expected a dictionary here, but instead I got {invalid_data} -- OH NO!"""
        )


class PMDeprecationWarning(DeprecationWarning):
    """Raised when someone tries to use a feature of the problems module that is deprecated"""

    pass


class LockedCacheException(RuntimeError):
    """Raised when an operation is done on a locked RedisCache"""

    pass


class LinearAlgebraUserInputErrorException(MathProblemsModuleException):
    "Raised when a Linear Algebra user input has a problem"
    pass


class SQLNotSupportedInRedisException(MathProblemsModuleException):
    """Raised when a redis cache attempts to run SQL"""

    pass


class OwnershipNotDeterminableException(MathProblemsModuleException):
    """Raised when the ownership of an object cannot be determined"""

    pass


class VerificationCodeExpiredException(MathProblemsModuleException):
    """Raised when a verification code is expired"""

    pass

class UnsavedContentWarning(Warning):
    """Raised when content is not being saved"""
    pass

class PastWarning(Warning):
    """A warning about things that were supported in the past but no longer are"""