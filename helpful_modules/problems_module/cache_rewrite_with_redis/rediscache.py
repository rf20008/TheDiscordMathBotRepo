import asyncio
import typing
from typing import List

import orjson
from redis import asyncio as aioredis  # type: ignore

from ...FileDictionaryReader import AsyncFileDict
from ..appeal import Appeal
from ..base_problem import BaseProblem
from ..dict_convertible import DictConvertible
from ..errors import (
    FormatException,
    InvalidDictionaryInDatabaseException,
    LockedCacheException,
    ProblemNotFoundException,
    ThingNotFound,
)
from ..GuildData import GuildData
from ..quizzes import Quiz
from ..user_data import UserData


class RedisCache:
    """A class that is supposed to handle the problems, and have the same API as problems_related_cache"""

    def __init__(self, redis_url: str, password: str):
        self.redis_url = redis_url
        self.password = password
        self.redis = aioredis.from_url(
            redis_url, encoding="utf-8", decode_responses=True, password=password
        )
        self.lock = asyncio.Lock()
        self._async_file_dict = AsyncFileDict("config.json")

    @property
    def is_locked(self):
        """Return whether the cache is locked"""
        return self.lock.locked()

    async def get_key(self, thing: str):
        """Return the value with key thing
        Time complexity: O(1)"""
        return await self.redis.hget(thing)

    async def set_key(self, key: str, value: str | dict):
        """Set the thing at key to value.
        Time complexity: O(1)
        :param key: the key
        :param value: the value
        :return: Nothing
        :raises LockedCacheException: If the cache is locked"""
        if self.is_locked:
            raise LockedCacheException("The cache is currently locked!")
        await self.redis.hset(key, str(value))

    async def del_key(self, key: str):
        """Delete the key associated with key:
        Time complexity: O(1)"""
        if self.is_locked:
            raise LockedCacheException("The cache is currently locked")
        await self.redis.hdel(key)

    async def get_problem(self, guild_id: int, problem_id: int) -> BaseProblem:
        """Attempt to return the problem with guild_id and problem_id =problem_id
        Time complexity: O(1)"""
        if guild_id is not None and not isinstance(guild_id, int):
            raise TypeError("guild_id is not an int")
        result = await self.get_key(f"BaseProblem:{guild_id}:{problem_id}")
        if result is not None:
            return BaseProblem.from_dict(orjson.loads(result))
        result = await self.get_key(f"QuizProblem:{guild_id}:{problem_id}")
        if result is not None:
            return BaseProblem.from_dict(orjson.loads(result))
        raise ProblemNotFoundException("That problem is not found")

    async def get_all_problems(self):
        """Return a list of all problems!
        Time complexity: O(N)"""
        return list(
            map(BaseProblem.from_dict, await self.redis.hgetall("BaseProblem").values())
        )

    async def get_all_things(self):
        """Return a list of EVERYTHING in the data base"""
        return list(self.redis.hgetall(""))

    async def get_all_problems_by_guild(self, guild_id: int | None):
        """return a list of all problems with the guild id = id
        Time complexity: O(N)"""
        return list(
            map(
                BaseProblem.from_dict,
                await self.redis.hgetall(f"BaseProblem:{guild_id}").values(),
            )
        )

    async def get_all_problems_by_func(self, func):
        """Return a list of all problems that satisfy the function.
        It is actually implemented as filter(func, await self.get_all_problems())
        Time complexity: O(N + sumF(P) over all problems) where F(P) is the big O runtime
        of calling func on a problem P"""
        return filter(func, await self.get_all_problems())

    async def get_global_problems(self):
        """
        Return a list of all global problems.

        :return: A list of global problems.
        """
        return await self.get_all_problems_by_guild(None)

    async def add_empty_guild(self):
        """
        Deprecated method. Raises NotImplementedError.

        :raises NotImplementedError: This method is deprecated.
        """
        raise NotImplementedError("This method is deprecated")

    async def add_problem(self, problem_id: int, problem: BaseProblem):
        """
        Add a problem to the cache.

        :param problem_id: The ID of the problem.
        :param problem: The BaseProblem instance.
        :raises TypeError: If 'problem_id' is not an int or 'problem' is not a BaseProblem.
        :raises ValueError: If IDs do not match.
        """
        if not isinstance(problem_id, int) or not isinstance(problem, BaseProblem):
            raise TypeError("Problem_id is not an int or problem is not a base problem")
        if problem.id != problem_id:
            raise ValueError("Ids do not match")

        await self.set_key(
            f"BaseProblem:{problem.guild_id}:{problem_id}",
            str(problem.to_dict(show_answer=True)),
        )

    async def update_problem(self, problem_id: int, problem: BaseProblem):
        """
        Update a problem in the cache.

        :param problem_id: The ID of the problem.
        :param problem: The BaseProblem instance.
        """
        return await self.add_problem(problem_id, problem)

    async def remove_problem(self, problem_id: int, guild_id: int | None):
        """
        Remove a problem from the cache.

        :param problem_id: The ID of the problem.
        :param guild_id: The ID of the guild.
        :raises TypeError: If 'problem_id' is not an int or 'guild_id' is not an int.
        """
        if not isinstance(problem_id, int) or (
            guild_id is not None and not isinstance(guild_id, int)
        ):
            raise TypeError("Bad types!")
        await self.del_key(f"BaseProblem:{guild_id}:{problem_id}")
        await self.del_key(f"QuizProblem:{guild_id}:{problem_id}")

    # Additional methods for quizzes

    async def add_quiz_dict(self, quiz_id: int, quiz_data: dict):
        """
        Add a quiz to the cache.

        :param quiz_id: The ID of the quiz.
        :param quiz_data: The data associated with the quiz.
        """
        await self.set_key(f"Quiz:{quiz_id}", quiz_data)
        # TODO: fix the type bug

    async def add_quiz(self, quiz_id: int, quiz: Quiz):
        """Add a quiz to the dict"""
        assert quiz_id == quiz.id
        return await self.add_quiz_dict(quiz.id, quiz.to_dict())

    async def get_quiz(self, quiz_id: int) -> dict:
        """
        Get quiz data by quiz ID.

        :param quiz_id: The ID of the quiz.
        :return: The data associated with the quiz.
        :raises ProblemNotFoundException: If the quiz is not found.
        """
        result = await self.get_key(f"Quiz:{quiz_id}")
        if result is not None:
            return orjson.loads(result)
        raise ProblemNotFoundException("That quiz is not found")

    async def remove_quiz(self, quiz_id: int):
        """
        Remove a quiz from the cache.

        :param quiz_id: The ID of the quiz.
        """
        await self.del_key(f"Quiz:{quiz_id}")

    async def add_thing(self, thing: DictConvertible):
        """
        Adds a dictionary convertible object to the cache.

        :param thing: The object to add to the cache.
        :type thing: DictConvertible
        :return: Nothing.
        """
        await self.set_key(f"{thing.__class__.__name__}:{thing.guild_id}:{thing.id}", thing.to_dict())  # type: ignore

    async def add_things(self, things: List[DictConvertible]):
        """
        Adds a list of dictionary convertible objects to the cache using a batch set operation.

        :param things: The list of objects to add to the cache.
        :type things: List[DictConvertible]
        :return: Nothing.
        """
        # Check if the cache is locked before acquiring the lock
        if self.is_locked:
            raise LockedCacheException("The cache is currently locked!")

        async with self.lock:
            # Inside the lock-protected block

            # Create a pipeline to execute batch commands
            pipeline = self.redis.pipeline()

            # Add each thing to the pipeline
            for thing in things:
                key = f"{thing.__class__.__name__}:{thing.guild_id}:{thing.id}"
                value = str(thing.to_dict())
                pipeline.hset(key, value)

            # Execute the batch set operation
            await pipeline.execute()

    async def remove_thing(self, thing: DictConvertible):
        """
        Removes a dictionary convertible object from the cache.

        :param thing: The object to remove from the cache.
        :type thing: DictConvertible
        :return: Nothing.
        """
        await self.del_key(f"{thing.__class__.__name__}:{thing.guild_id}:{thing.id}")  # type: ignore

    async def get_thing(
        self,
        thing_guild_id: int,
        thing_id: int,
        cls: typing.Type[DictConvertible],
        default: DictConvertible | None = None,
    ):
        """
        Retrieves a dictionary convertible object from the cache.

        :param thing_guild_id: The guild ID associated with the object.
        :type thing_guild_id: int
        :param thing_id: The ID of the object.
        :type thing_id: int
        :param cls: The type of the dictionary convertible object.
        :type cls: typing.Type[DictConvertible]
        :param default: The default value to return if the object is not found.
        :type default: DictConvertible or None
        :return: The retrieved object.
        :rtype: DictConvertible
        :raises ThingNotFound: If the object is not found.
        """
        result = await self.get_key(f"{cls.__name__}:{thing_guild_id}:{thing_id}")
        if result is not None:
            try:
                return await cls.from_dict(orjson.loads(result))
            except FormatException as fe:
                fe.args[0] += "There was a problem with the format of the exception"
                raise fe
            except KeyError as ke:
                raise FormatException("Oh no, the formatting is bad!") from ke
            except orjson.JSONDecodeError as jde:
                raise InvalidDictionaryInDatabaseException(
                    "It's not even formatted as JSON!"
                ) from jde
            except Exception as exc:
                raise RuntimeError("Something bad happened...") from exc
        if default is not None:
            return default
        raise ThingNotFound("The thing is not found!")

    async def get_user_data(self, user_id: int, default: UserData | None = None):
        result = await self.get_key(f"UserData:{user_id}")
        if result is not None:
            try:
                return UserData.from_dict(orjson.loads(result))
            except orjson.JSONDecodeError:
                raise InvalidDictionaryInDatabaseException(
                    "We have a non-dictionary on our hands"
                )
            except FormatException as fe:
                raise FormatException("Oh no, the formatting is bad") from fe
        if default is not None:
            return default
        raise ThingNotFound("I could not find any user data")

    async def add_user_data(self, thing: UserData):
        await self.set_key(f"UserData:{thing.user_id}", str(thing.to_dict()))

    async def remove_user_data(self, thing: UserData):
        await self.del_key(f"UserData:{thing.user_id}")

    async def get_permissions_required_for_command(
        self, command_name
    ) -> typing.Dict[str, bool]:
        """
        Get the permissions required for a command.

        :param command_name: The name of the command.
        :return: A dictionary of permissions required for the command.
        """
        await self._async_file_dict.read_from_file()
        return self._async_file_dict.dict["permissions_required"][command_name]

    async def user_meets_permissions_required_to_use_command(
        self,
        user_id: int,
        permissions_required: typing.Optional[typing.Dict[str, bool]] = None,
        command_name: str | None = None,
    ) -> bool:
        """
        Return whether the user meets permissions required to use the command.

        :param user_id: The ID of the user.
        :param permissions_required: Optional permissions required for the command.
        :param command_name: Optional name of the command.
        :return: True if the user meets permissions, False otherwise.
        """
        if permissions_required is None:
            permissions_required = await self.get_permissions_required_for_command(
                command_name
            )

        if "trusted" in permissions_required.keys():
            if (
                await self.get_user_data(
                    user_id, default=UserData.default(user_id=user_id)
                )
            ).trusted != permissions_required["trusted"]:
                return False

        if "blacklisted" in permissions_required.keys():
            if (
                (
                    await self.get_user_data(
                        user_id, default=UserData.default(user_id=user_id)
                    )
                )
            ).blacklisted != permissions_required["blacklisted"]:
                return False
        user_data = await self.get_user_data(user_id)
        return all(
            getattr(user_data, key) != val for key, val in permissions_required.items()
        )

    async def get_appeal(
        self, user_id: int, default: Appeal | None = None
    ) -> Appeal | None:
        result = await self.get_key(f"Appeal:{user_id}")
        if result is not None:
            try:
                return Appeal.from_dict(orjson.loads(result))
            except orjson.JSONDecodeError:
                raise InvalidDictionaryInDatabaseException(
                    "We have a non-dictionary on our hands"
                )
            except FormatException as fe:
                raise FormatException("Oh no, the formatting is bad") from fe
        if default is not None:
            return default
        raise ThingNotFound("I could not find any appeal")

    async def add_appeal(self, thing: Appeal):
        await self.set_key(f"Appeal:{thing.user_id}", thing.to_dict())

    async def remove_appeal(self, thing: Appeal):
        await self.del_key(f"Appeal:{thing.user_id}")

    async def update_cache(self):
        """
        Deprecated method. Raises NotImplementedError.

        :raises NotImplementedError: This method is deprecated.
        """
        raise NotImplementedError(
            "This method is being removed, due to its expensiveness..."
        )

    async def add_guild_data(self, guild_data: GuildData):
        """
        Add guild data to the cache.

        :param guild_data: The GuildData instance to add.
        """
        await self.set_key(f"GuildData:{guild_data.guild_id}", guild_data.to_dict())

    async def del_guild_data(self, guild_id: int):
        """
        Remove guild data from the cache.

        :param guild_id: The ID of the guild.
        :raises TypeError: If 'guild_id' is not an int.
        """
        await self.del_key(f"GuildData:{guild_id}")

    async def get_guild_data(
        self, guild_id: int, default: GuildData | None = None
    ) -> GuildData:
        """
        Get guild data by guild ID.

        :param guild_id: The ID of the guild.
        :param default: The default GuildData instance to return if not found.
        :return: The GuildData instance.
        :raises ThingNotFound: If the guild data is not found.
        """

        result = await self.get_key(f"GuildData:{guild_id}")
        if result is not None:
            try:
                return Appeal.from_dict(orjson.loads(result))
            except orjson.JSONDecodeError:
                raise InvalidDictionaryInDatabaseException(
                    "We have a non-dictionary on our hands"
                )
            except FormatException as fe:
                raise FormatException("Oh no, the formatting is bad") from fe
        if default is not None:
            return default
        raise ThingNotFound("I could not find any guild_data")

    async def get_all_by_user_id(self, user_id: int) -> list[str]:
        """
        Get a list of keys corresponding to things authored by the specified user.

        This method queries all things stored in the Redis database and returns the keys
        of the items where the provided user_id matches the 'author', 'authors', or 'user_id'
        field in the stored JSON data.

        :param user_id: The user ID to match against.
        :type user_id: int
        :return: A list of keys corresponding to things authored by the specified user.
        :rtype: List[str]
        :raises FormatException: If a stored value in Redis is not a valid JSON dictionary.
        """
        # get all things
        things = await self.get_all_things()
        things_authored = []
        for key, value in things.items():
            dictionarified = None
            try:
                dictionarified = orjson.loads(value)  # type: ignore
            except orjson.JSONDecodeError:
                raise FormatException("Something in the redis is not a dictionary..")
            if dictionarified is None:
                raise FormatException("No dictionary found")
            if dictionarified.get("author", None) == user_id:
                things_authored.append(key)
                continue
            elif user_id in dictionarified.get("authors", []):
                things_authored.append(key)
                continue
            elif dictionarified.get("user_id", None) == user_id:
                things_authored.append(key)
                continue

        return things_authored

    async def del_all_by_user_id(self, user_id: int):
        """DELETE all things that match the user_id
        This operation is IRREVERSIBLE!
        Time complexity: O(N)
        Params:
        :param user_id: the user id of the user we need to remove all things of
        Raises
        :raises TypeError: if the user_id is not actually an int
        :raises FormatException: if something in the redis isn't a dict

        Returns
        nothing"""
        things_to_remove = await self.get_all_by_user_data(user_id=user_id)
        async with self.lock:
            await asyncio.sleep(3.0000)
            await self.redis.delete(*things_to_remove)
            await asyncio.sleep(3.0000)

    async def get_guild_data(
        self, guild_id: int, default: GuildData | None = None
    ) -> GuildData | None:
        result = await self.get_key(f"GuildData:{guild_id}")
        if result is not None:
            try:
                return GuildData.from_dict(orjson.loads(result))
            except orjson.JSONDecodeError:
                raise InvalidDictionaryInDatabaseException(
                    "We have a non-dictionary on our hands"
                )
            except FormatException as fe:
                raise FormatException("Oh no, the formatting is bad") from fe
        if default is not None:
            return default
        raise ThingNotFound("I could not find any guild data")

    async def add_guild_data(self, thing: GuildData):
        await self.set_key(f"GuildData:{thing.guild_id}", str(thing.to_dict()))

    async def remove_guild_data(self, thing: GuildData | int):
        if isinstance(thing, GuildData):
            await self.del_key(f"GuildData:{thing.guild_id}")
        else:
            await self.del_key(f"GuildData:{thing}")


# TODO: fix the rest of the commands such that this cache can work
# TODO: get a redis server
# TODO: unit tests!
