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
import asyncio
import concurrent.futures
import datetime
import io
import os
import logging
import pathlib
import random
import time
import traceback
import types
from functools import partial, wraps
from logging import handlers
from typing import Any, Optional, Callable

import aiofiles
import disnake

from .the_documentation_file_loader import DocumentationFileLoader

# Licensed under GPLv3

log = logging.getLogger(__name__)

TYPE_CLASS = type(int)  # the class 'type'


def generate_new_id():
    """Generate a random number from 0 to 2**53-1"""
    return random.randint(0, 2**53 - 1)


def async_wrap(func):
    """Turn a sync function into an asynchronous function
    Source: https://dev.to/0xbf/turn-sync-function-to-async-python-tips-58nn
    """

    @wraps(func)
    async def run(*args, loop=None, executor=None, **kwargs):
        if loop is None:
            loop = asyncio.get_event_loop()
        pfunc = partial(func, *args, **kwargs)
        return await loop.run_in_executor(executor, pfunc)

    return run


def modified_async_wrap(func):
    assert isinstance(func, types.FunctionType)
    if asyncio.iscoroutinefunction(func):
        return func
    return async_wrap(func)


def loading_documentation_thread():
    """This thread reloads the documentation."""
    d = DocumentationFileLoader()
    d.load_documentation_into_readable_files()
    del d


def get_log(name: Optional[str]) -> logging.Logger:
    _log = logging.getLogger(name)
    TRFH = handlers.TimedRotatingFileHandler(
        filename="logs/bot.log", when="midnight", encoding="utf-8", backupCount=300
    )
    _log.addHandler(TRFH)
    return _log


def _generate_special_id(guild_id, quiz_id, user_id, attempt_num):
    return str(
        {
            "quiz_id": quiz_id,
            "guild_id": guild_id,
            "user_id": user_id,
            "attempt_num": attempt_num,
        }
    )


def assert_type_or_throw_exception(
    thing: Any,
    err_type: TYPE_CLASS,
    msg: str = "Wrong type provided!",
    exc_type: Exception = TypeError,
):
    """
    Assert that `thing` is of type `type` or throw an exception.
    Parameters
    ---------
    thing : Any
        The thing to test
    type: `py:class:type`
        A thing to test the type against
    msg: str
        The message of the error that will be raised if the thing is not of type
    exc_type: BaseException
        The exception type thrown. Defaults to `py:class:TypeError`.
    """
    if not isinstance(thing, err_type):
        raise exc_type(msg)  # type: ignore
    return


def extended_gcd(a, b):
    if a == 0:
        return b, 0, 1
    else:
        gcd, x1, y1 = extended_gcd(b % a, a)
        x = y1 - (b // a) * x1
        y = x1
        return gcd, x, y


def miller_rabin(n, k=100):
    if not isinstance(n, int) or n < 2:
        raise ValueError("no; n is not an int or n<2")
    if n % 2 == 0:
        return n == 2
    s = 0
    d = n - 1
    while d & 1 == 0:
        d = d >> 1
        s += 1
    for _ in range(k):
        a = random.randint(2, n - 2)
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        y = x
        for j in range(s):
            y = (x * x) % n
            if y == 1:
                return False  # n is composite, we have a witness
            if y == n - 1:
                break
            x = y
        if y != 1:
            return False
    return True


month_num_to_name_dict = {
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December",
}


def humanify_date(date: datetime.datetime | datetime.date):
    return (
        str(date.year) + " " + month_num_to_name_dict[date.month] + " " + str(date.day)
    )


def ensure_eval_logs_exist():
    try:
        logs_folder = pathlib.Path("eval_log")
        logs_folder.mkdir(exist_ok=True)
        return
    except:
        print(
            "I don't have permission to create an eval logs folder so logs may be missing!"
        )
        traceback.print_exc()


def get_log(name: Optional[str]) -> logging.Logger:
    _log = logging.getLogger(name)
    TRFH = handlers.TimedRotatingFileHandler(
        filename="logs/bot.log", when="midnight", encoding="utf-8", backupCount=300
    )
    _log.addHandler(TRFH)
    return _log


async def log_evaled_code(
    code: str, filepath: str = "", time_ran: datetime.datetime = None
) -> None:
    if time_ran == None:
        time_ran = datetime.datetime.now()
    # determine the filepath
    date = humanify_date(time_ran)
    if filepath == "":
        filepath = f"eval_log/{date}"
    try:
        to_open = aiofiles.open(filepath, "a")
        async with to_open as file:
            await file.write("\n" + str(time_ran) + "\n" + code + "\n")
    except Exception as e:
        raise RuntimeError(
            "While attempting to log the code that was evaluated, I ran into some problems!"
        ) from e


import secrets


def secure_fisher_yates_shuffle(sequence):
    # Convert to a list to allow in-place shuffling
    shuffled_sequence = list(sequence)
    n = len(shuffled_sequence)

    for i in range(n - 1, 0, -1):
        # Use secrets.randbelow for secure randomness
        j = secrets.randbelow(i + 1)

        # Swap elements
        shuffled_sequence[i], shuffled_sequence[j] = (
            shuffled_sequence[j],
            shuffled_sequence[i],
        )

    return shuffled_sequence


def file_version_of_item(item: str, file_name: str) -> disnake.File:
    """
    Return a disnake.File with the specified filename that contains the string provided.
    """
    if not isinstance(item, str):
        raise TypeError("item is not a string")
    if not isinstance(file_name, str):
        raise TypeError("file_name is not a string")
    return disnake.File(io.BytesIO(bytes(item, "utf-8")), filename=file_name)

def generate_custom_id(bytelen: int = 20):
    return os.urandom(bytelen).hex()

async def async_wait_for_future(future: asyncio.Future | concurrent.futures.Future, timeout: float | None = None, interval: float = 0.3):
    if isinstance(future, asyncio.Future):
        if timeout is not None:
            return await asyncio.wait_for(future, timeout)
        return await future
    if not isinstance(future, concurrent.futures.Future):
        raise TypeError("future isn't a concurrent.futures.Future")
    start = time.time()
    while timeout is None or (time.time() - start < timeout):
        await asyncio.sleep(interval)
        if future.done():
            return future.result()
    raise TimeoutError(f"Future didn't complete within {timeout} seconds")

def first_true(lo: int, hi: int, f: Callable[[int], bool]):

    # bin search [lo, hi), where f(lo)=false, f(hi)=true
    # We want the first L such that f(L)=true, but f(x)=false for all x<L
    # assume f is monotonically increasing (f(x) = false implies f(y)=false for all y<x, and f(x)=true implies f(y)=true for all y>x)

    # if f(mid) is true, then mid...hi is all true so hi=mid else it's false so lo..mid is all false, so lo=mid
    hi += 1
    while hi > lo:
        mid = (lo + hi)//2
        if f(mid):
            hi = mid
        else:
            lo = mid+1
    return lo
def last_true(lo: int, hi: int, f: Callable[[int], bool]):

    # bin search [lo, hi), where f(lo)=true, f(hi)=false
    # We want the last R such that f(x)=true, and there exists no r>R s.t. f(r)=true
    # assume f is monotonically decreasing (f(x) = false implies f(y)=false for all y>x, and f(x)=true implies f(y)=true for all y<x)
    lo-=1
    while hi > lo:
        mid = (lo + hi)//2
        if f(mid):
            lo = mid
        else:
            hi = mid-1
    return lo