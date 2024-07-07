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
import datetime
import logging
import math
import unittest
import unittest.mock
from unittest.mock import AsyncMock, patch

import aiofiles
import pyfakefs.fake_filesystem_unittest

from helpful_modules import threads_or_useful_funcs
from tests.mockable_aiofiles import MockableAioFiles
from tests.utils import generate_many_randoms


class TestGenerateId(unittest.TestCase):
    def test_id_range(self):
        for i in range(500):
            self.assertIn(threads_or_useful_funcs.generate_new_id(), range(2**53))

    def test_id_type(self):
        self.assertIsInstance(threads_or_useful_funcs.generate_new_id(), int)


class TestWraps(unittest.IsolatedAsyncioTestCase):
    async def test_async_wrap(self):
        def f(x):
            return x * x + 3 * x + 2

        wrapped_f = threads_or_useful_funcs.async_wrap(f)
        self.assertEqual(
            f(0),
            await wrapped_f(0),
            "f and wrapped_f are not functionally equivalent, as f(0) != wrapped_f(0)",
        )
        self.assertEqual(
            f(3),
            await wrapped_f(3),
            "f and wrapped_f are not functionally equivalent, as f(3) != wrapped_f(3)",
        )
        self.assertEqual(
            f(100),
            await wrapped_f(100),
            "f and wrapped_f are not functionally equivalent, as f(100) != wrapped_f(100)",
        )
        self.assertNotEqual(
            f(0), await wrapped_f(30333), "They are equal for some function!"
        )

    async def test_async_wrap_with_executor(self):
        # NOTE: THIS CAME FROM CHATGPT
        # Define a synchronous function

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()

        def sync_function():
            return "Hello, World!"

        # Wrap the synchronous function with async_wrap, providing an executor
        async_wrapped_function = threads_or_useful_funcs.async_wrap(sync_function)

        # Mock an executor
        executor_mock = unittest.mock.AsyncMock(spec=type(loop))
        # Make run_in_executor an AsyncMock, so it can be awaited. Otherwise, this test will fail
        executor_mock.run_in_executor = AsyncMock()  #
        # Call the wrapped function with the executor within an async context
        await async_wrapped_function(loop=executor_mock)

        # Assert that the executor's run_in_executor method was called
        executor_mock.run_in_executor.assert_called_once()


class TestClassOrThrowException(unittest.TestCase):
    def test_pass_basic_1(self):
        self.assertIsNone(
            threads_or_useful_funcs.assert_type_or_throw_exception(3111, int)
        )

    def test_pass_basic_2(self):
        self.assertIsNone(
            threads_or_useful_funcs.assert_type_or_throw_exception("hehe boi", str)
        )

    def test_pass_medium_1(self):
        self.assertIsNone(
            threads_or_useful_funcs.assert_type_or_throw_exception(
                "nope" + "hehe boi", str
            )
        )

    def test_pass_class(self):
        self.assertIsNone(
            threads_or_useful_funcs.assert_type_or_throw_exception(
                KeyboardInterrupt("hehe"), KeyboardInterrupt
            )
        )

    def test_wrong_type(self):
        self.assertRaises(
            TypeError,
            threads_or_useful_funcs.assert_type_or_throw_exception,
            ("no", int),
        )

    def test_raise_correct_error_1(self):
        self.assertRaises(
            ValueError,
            threads_or_useful_funcs.assert_type_or_throw_exception,
            *("no", int, "hehe", ValueError),
        )

    def test_raise_correct_error_2(self):
        self.assertRaises(
            RuntimeError,
            threads_or_useful_funcs.assert_type_or_throw_exception,
            1392929292,
            float,
            "hehe",
            RuntimeError,
        )


class TestExtendedGCD(unittest.TestCase):
    def test_gcd_basic(self):
        self.assertEqual(threads_or_useful_funcs.extended_gcd(3, 1)[0], 1)
        for i in range(300):
            x, y, d = generate_many_randoms(
                3, lows=[1, 1, 1], highs=[30000, 30000, 30000]
            )
            self.assertEqual(
                threads_or_useful_funcs.extended_gcd(x * d, y * d)[0],
                math.gcd(x * d, y * d),
            )

    def test_bezouts_condition(self):
        a, b = 3, 1
        g, x, y = threads_or_useful_funcs.extended_gcd(a, b)

        self.assertEqual(
            abs(x * a + y * b),
            1,
            f"Bezout's condition was not satisfied when a={a}, b={b}",
        )
        for i in range(300):
            a, b, d = generate_many_randoms(
                3, lows=[1, 1, 1], highs=[30000, 30000, 30000]
            )
            g, x, y = threads_or_useful_funcs.extended_gcd(a * d, b * d)
            real_gcd = math.gcd(a * d, b * d)
            self.assertEqual(
                g,
                real_gcd,
                f"Our program said gcd({a}, {b})={g} but in reality it is {real_gcd}",
            )
            self.assertEqual(
                x * a * d + y * b * d,
                g,
                f"Bezout's condition was not satisfied when a={a}, b={b}, d={d} (x={x}, y={y}, d={d}, xy+ab={x * a * d + y * b * d}, g={g}), real_gcd={real_gcd}",
            )


class TestMillerRabin(unittest.TestCase):
    def test_prime_small(self):
        failures = 0
        for _ in range(2000):
            if threads_or_useful_funcs.miller_rabin(100, 3):
                failures += 1
            if not threads_or_useful_funcs.miller_rabin(7, 3):
                failures += 1
        self.assertLess(failures / 1.15, 2000 / 64)

    def test_prime_big(self):
        m = 10**9 + 7
        self.assertFalse(threads_or_useful_funcs.miller_rabin(m * m, 300))
        self.assertTrue(threads_or_useful_funcs.miller_rabin(m, 300))
        self.assertTrue(threads_or_useful_funcs.miller_rabin(10**18 + 3, 300))
        self.assertFalse(threads_or_useful_funcs.miller_rabin(m * m - 1, 300))
        self.assertFalse(threads_or_useful_funcs.miller_rabin(m * m - 2, 300))

    def test_exceptions(self):
        self.assertRaises(
            ValueError, threads_or_useful_funcs.miller_rabin, "hehe boi", 30
        )
        self.assertRaises(ValueError, threads_or_useful_funcs.miller_rabin, 0, 15)


class TestEvalLogsAndLogs(pyfakefs.fake_filesystem_unittest.TestCase):
    def setUp(self):
        self.setUpPyfakefs()

        try:
            self.loop = asyncio.get_running_loop()
        except RuntimeError:
            self.loop = asyncio.new_event_loop()

    async def ensure_eval_logs_exist_test(self):
        # Test if the logs folder is created successfully
        with patch("builtins.print") as mock_print:
            threads_or_useful_funcs.ensure_eval_logs_exist()
            mock_print.assert_not_called()  # Ensure print is not called on success

        # Test if an exception is caught and a message is printed
        with patch("builtins.print") as mock_print:
            with patch("pathlib.Path.mkdir", side_effect=PermissionError):
                threads_or_useful_funcs.ensure_eval_logs_exist()
                mock_print.assert_any_call(
                    "I don't have permission to create an eval logs folder so logs may be missing!"
                )

    def test_ensure_eval_logs_exist(self):
        self.loop.run_until_complete(self.ensure_eval_logs_exist_test())

    def get_log_test(self):
        with open("logs/bot.log", "w") as f:
            f.write("hehe boi!!!")
        # Test if a logger is returned with the correct handler
        log = threads_or_useful_funcs.get_log("test_logger")
        handlers = log.handlers
        self.assertTrue(
            any(
                isinstance(handler, logging.handlers.TimedRotatingFileHandler)
                for handler in handlers
            )
        )

    async def log_evaled_code_permission_test(self):
        # TODO: fix the mocking of aiofiles (the problem is __aenter__)

        code = "print('Hello, World!')"
        filepath = "eval_log/test_date"
        time_ran = datetime.datetime.now()

        # Test permission error
        with patch(
            "aiofiles.open",
            new=AsyncMock(
                side_effect=PermissionError("YOU DO NOT HAVE PERMISSION! MUHAHAHA!")
            ),
        ):
            with self.assertRaises(RuntimeError):
                await threads_or_useful_funcs.log_evaled_code(code, filepath, time_ran)

    def test_log_evaled_code_permission(self):
        self.loop.run_until_complete(self.log_evaled_code_permission_test())

    async def log_evaled_code_file_write_test(self):
        self.fs.create_dir("logs/eval_logs/")
        self.fs.create_dir("eval_log/")
        # make sure we write to the right file
        mock_open3 = AsyncMock()
        mock_open3.side_effect = MockableAioFiles
        mock_open3.__aenter__ = AsyncMock(side_effect=MockableAioFiles)
        mock_open3.__aexit__ = AsyncMock(side_effect=MockableAioFiles)
        with patch(
            "aiofiles.open",
            # new_callable= lambda *args, **kwargs: MockableAioFiles(*args, **kwargs)
            wraps=MockableAioFiles,
        ):
            print(
                f"Right before the test, aiofiles.open is of type {type(aiofiles.open)}"
            )
            await threads_or_useful_funcs.log_evaled_code(
                code="no", filepath="haha.log"
            )
        with open("haha.log", "r") as file:
            self.assertIn("no", "\n".join(file.readlines()))

    def test_log_evaled_code_file_write(self):
        self.loop.run_until_complete(self.log_evaled_code_file_write_test())

    async def log_evaled_code_actual_write_test(self):
        self.fs.create_dir("logs/eval_logs/")
        self.fs.create_dir("eval_log/")
        code = "print('Hello, World!')"
        filepath = "eval_log/HAHA.txt"
        time_ran = datetime.datetime.now()
        # Patch aiofiles.open to use the mock_open function
        with patch("aiofiles.open", wraps=MockableAioFiles):
            # reset_mocks()
            # Test if the code is successfully written to the file
            with patch(
                "helpful_modules.threads_or_useful_funcs.humanify_date",
                return_value="test_date",
            ):
                await threads_or_useful_funcs.log_evaled_code(code, filepath, time_ran)
                with open("eval_log/HAHA.txt", "r") as file:
                    lines = file.readlines()
                    self.assertIn(f"\n{str(time_ran)}\n\n{code}\n", "\n".join(lines))

            # Test if the default filepath is set when not provided
            with patch(
                "helpful_modules.threads_or_useful_funcs.humanify_date",
                return_value="test_date.txt",
            ):
                await threads_or_useful_funcs.log_evaled_code(code, time_ran=time_ran)
                with open("eval_log/test_date.txt", "r") as file:
                    lines = file.readlines()
                    self.assertIn(f"\n{str(time_ran)}\n\n{code}\n", "\n".join(lines))

            # Test if an exception is raised when writing to the file fails
            # reset_mocks()

    def test_log_evaled_code(self):
        self.loop.run_until_complete(self.log_evaled_code_actual_write_test())


class TestHumanifyDate(unittest.TestCase):
    def test_humanify_date(self):
        # Test with a datetime object
        datetime_obj = datetime.datetime(2023, 1, 15)
        formatted_date = threads_or_useful_funcs.humanify_date(datetime_obj)
        expected_result = "2023 January 15"
        self.assertEqual(formatted_date, expected_result)

        # Test with a date object
        date_obj = datetime.date(2023, 1, 15)
        formatted_date = threads_or_useful_funcs.humanify_date(date_obj)
        expected_result = "2023 January 15"
        self.assertEqual(formatted_date, expected_result)


class TestSecureFisherYatesShuffle(unittest.TestCase):
    @patch(
        "helpful_modules.threads_or_useful_funcs.secrets.randbelow",
        side_effect=[2, 1, 0, 0, 0],
    )
    def test_secure_fisher_yates_shuffle(self, mock_randbelow):
        my_list = [1, 2, 3, 4, 5]
        shuffled_list = threads_or_useful_funcs.secure_fisher_yates_shuffle(my_list)

        self.assertNotEqual(my_list, shuffled_list)
        self.assertCountEqual(my_list, shuffled_list)
        mock_randbelow.assert_called_with(2)


if __name__ == "__main__":
    unittest.main()
