"""You can distribute any version of the Software created and distributed *before* 23:17:55.00 July 28, 2024 GMT-4
under the GNU General Public License version 3 or at your option, any  later option.
But versions of the code created and/or distributed *on or after* that date must be distributed
under the GNU *Affero* General Public License, version 3, or, at your option, any later version.

The Discord Math Problem Bot Repo - ConstantsLoader

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License
as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License along with this program.
If not, see <https://www.gnu.org/licenses/>.

Author: Samuel Guo (64931063+rf20008@users.noreply.github.com)"""
import os

import dotenv


class BotConstants:
    """Bot constants"""

    def __init__(self, env_path):
        dotenv.load_dotenv(env_path)
        self.MYSQL_USERNAME = os.environ.get("mysql_username")
        self.MYSQL_PASSWORD = os.environ.get("mysql_password")
        self.MYSQL_DB_IP = os.environ.get("mysql_db_ip")
        self.MYSQL_DB_NAME = os.environ.get("mysql_db_name")
        self.DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
        self.USE_SQLITE = os.environ.get("use_sqlite") == "True"
        self.SQLITE_DB_PATH = os.environ.get("sqlite_database_path")
        self.SOURCE_CODE_LINK = os.environ.get("source_code_link")
