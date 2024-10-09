"""You can distribute any version of the Software created and distributed *before* 23:17:55.00 July 28, 2024 GMT-4
under the GNU General Public License version 3 or at your option, any  later option.
But versions of the code created and/or distributed *on or after* that date must be distributed
under the GNU *Affero* General Public License, version 3, or, at your option, any later version.

The Discord Math Problem Bot Repo - Error Logging

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License
as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License along with this program.
If not, see <https://www.gnu.org/licenses/>.

Author: Samuel Guo (64931063+rf20008@users.noreply.github.com)"""
import datetime
import time
import traceback

MONTH_NAMES = {
    1: "January",
    2: "February,",
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


async def log_error(error, file_path="", send_to_webhook=False):
    log_error_to_file(error, file_path)
    if send_to_webhook:
        raise NotImplementedError("Not done yet")


def log_error_to_file(error, file_path=""):
    "Log the error to a file"
    if not isinstance(file_path, str):
        raise TypeError("file_path is not a string")
    if not isinstance(error, BaseException):
        raise TypeError("error is not an error")
    if file_path == "":
        now = datetime.datetime.now()
        file_path = (
            f"error_logs/{now.year} {MONTH_NAMES[now.month]} {now.day}.txt"
        )
    err_msg = traceback.format_exception(type(error), error, tb=error.__traceback__)
    msg = time.asctime() + "\n\n" + "".join([str(item) for item in err_msg]) + "\n\n"

    try:
        with open(file_path, "a") as f:
            f.write(msg)
    except Exception as exc:
        raise Exception(
            "***File path not found.... or maybe something else happened.... anyway please report this :)***"
        ) from exc
