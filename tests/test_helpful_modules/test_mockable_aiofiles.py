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

from .mockable_aiofiles import MockableAioFiles


import unittest
import asyncio
from pyfakefs.fake_filesystem_unittest import TestCase

class TestMockableAioFiles(TestCase):

    def setUp(self):
        self.setUpPyfakefs()

    async def test_write_and_read(self):
        async with MockableAioFiles('test_file.txt', 'w') as mock_file:
            await mock_file.write('This is a test.')

        # Check with open() to ensure content was written
        with open('test_file.txt', 'r') as file:
            content = file.read()
        self.assertEqual(content, 'This is a test.')

    async def test_readline(self):
        # Use standard open() to write content
        with open('test_file.txt', 'w') as file:
            file.write('Line 1\nLine 2\nLine 3\n')

        async with MockableAioFiles('test_file.txt', 'r') as mock_file:
            line1 = await mock_file.readline()
            line2 = await mock_file.readline()
        self.assertEqual(line1, 'Line 1\n')
        self.assertEqual(line2, 'Line 2\n')

    async def test_readall(self):
        # Use standard open() to write content
        with open('test_file.txt', 'w') as file:
            file.write('Content\nMore content\nFinal content\n')

        async with MockableAioFiles('test_file.txt', 'r') as mock_file:
            content = [chunk async for chunk in mock_file.readall()]
        self.assertEqual(content, ['C', 'o', 'n', 't', 'e', 'n', 't', '\n', 'M', 'o', 'r', 'e', ' ', 'c', 'o', 'n', 't', 'e', 'n', 't', '\n', 'F', 'i', 'n', 'a', 'l', ' ', 'c', 'o', 'n', 't', 'e', 'n', 't', '\n'])

    async def test_readlines(self):
        # Use standard open() to write content
        with open('test_file.txt', 'w') as file:
            file.write('Line 1\nLine 2\nLine 3\n')

        async with MockableAioFiles('test_file.txt', 'r') as mock_file:
            lines = [line async for line in mock_file.readlines()]
        self.assertEqual(lines, ['Line 1\n', 'Line 2\n', 'Line 3\n'])

    async def test_close(self):
        async with MockableAioFiles('test_file.txt', 'w') as mock_file:
            await mock_file.write('Test content.')

        # Check with open() to ensure content was written
        with open('test_file.txt', 'r') as file:
            content = file.read()
        self.assertEqual(content, 'Test content.')

    async def test_iteration(self):
        # Use standard open() to write content
        with open('test_file.txt', 'w') as file:
            file.write('Line 1\nLine 2\nLine 3\n')

        async with MockableAioFiles('test_file.txt', 'r') as mock_file:
            lines = [line async for line in mock_file]
        self.assertEqual(lines, ['Line 1\n', 'Line 2\n', 'Line 3\n'])

    async def test_read_write_same_file(self):
        async with MockableAioFiles('test_file.txt', 'w') as mock_file:
            # Attempting to read from the file opened in write mode should raise ValueError
            with self.assertRaises(ValueError):
                await mock_file.read()

        # Attempting to write to the file opened in read mode should raise ValueError
        with open('test_file.txt', 'r') as file:
            mock_file_read = MockableAioFiles('test_file.txt', 'r')
            await mock_file_read.__aenter__()
            with self.assertRaises(ValueError):
                await mock_file_read.write('Invalid write operation.')
            await mock_file_read.__aexit__()

if __name__ == '__main__':
    unittest.main()
