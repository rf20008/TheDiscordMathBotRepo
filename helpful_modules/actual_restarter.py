"""You can distribute any version of the Software created and distributed *before* 23:17:55.00 July 28, 2024 GMT-4
under the GNU General Public License version 3 or at your option, any  later option.
But versions of the code created and/or distributed *on or after* that date must be distributed
under the GNU *Affero* General Public License, version 3, or, at your option, any later version.

The Discord Math Problem Bot Repo - Actual Restarter

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License
as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License along with this program.
If not, see <https://www.gnu.org/licenses/>.

Author: Samuel Guo (64931063+rf20008@users.noreply.github.com)"""
import multiprocessing
import os
import subprocess
from sys import executable
from time import sleep

print("We are: " + str(os.path.abspath(os.getcwd())))
current_file_path = os.path.abspath(__file__)
main_script_path = os.path.abspath(
    os.path.join(os.path.dirname(current_file_path), "..", "main.py")
)
test_script_path = os.path.abspath(
    os.path.join(os.path.dirname(current_file_path), "test.py")
)
print("Current file path: " + str(current_file_path))
print("Main script path: " + str(main_script_path))
q = subprocess.Popen(
    test_script_path.split(),
    executable=executable,
    shell=False,
)

print("Q's PID is " + str(q.pid))
q.wait()
print(q.stdout)


def start():
    print(f"Hello from my subprocess! My PID is {os.getpid()}")
    print(f"{main_script_path}")

    p = subprocess.Popen(
        f"{main_script_path}".split(),
        executable=executable,
        shell=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.PIPE,
    )
    print("NEW PID: " + str(p.pid))
    # os.system(f"cd {executable}; python3.12 -m main.py")
    p.wait()


if __name__ == "__main__":
    print(f"Parent PID: {os.getpid()}")
    sp = multiprocessing.Process(target=start)
    sp.start()
    try:
        sp.join(timeout=1.0)
    finally:
        sp.kill()
        os._exit(0)  # type: ignore
