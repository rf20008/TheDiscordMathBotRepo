"""
You can distribute any version of the Software created and distributed *before* 23:17:55.00 July 28, 2024 GMT-4
under the GNU General Public License version 3 or at your option, any  later option.
But versions of the code created and/or distributed *on or after* that date must be distributed
under the GNU *Affero* General Public License, version 3, or, at your option, any later version.


The Discord Math Problem Bot Repo - MySQLWithSTMT

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License
as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License along with this program.
If not, see <https://www.gnu.org/licenses/>.

Author: Samuel Guo (64931063+rf20008@users.noreply.github.com)"""
import contextlib

import aiomysql

# Licensed under AGPLv3 (or later)


@contextlib.contextmanager  # type: ignore
def mysql_connection(*args, **kwargs) -> aiomysql.Connection:
    """A custom with statement to connect to a MySQL database.
    This makes connecting to MYSQL possible within a context wrapper. This is a wrapper around MySQL
    You must take care to provide the correct arguments and keyword arguments, which will be directly passed to the mysql.connector.connect() method.
    If an exception happens in the with statement, the connection will commit and close and then the exception will be raised.
    Otherwise, the connection will commit and close. It will not return anything. :-)
    This function is licensed under GPLv3."""
    connection = aiomysql.connect(*args, **kwargs)  # type: ignore
    try:
        yield connection
    except:
        print(
            "An exception occured!. After closing resources, the exception will be raised"
        )
        connection.commit()
        connection.close()
        raise
    finally:
        connection.commit()
        connection.close()
