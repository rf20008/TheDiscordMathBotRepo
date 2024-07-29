"""
You can distribute any version of the Software created and distributed *before* 23:17:55.00 July 28, 2024 GMT-4
under the GNU General Public License version 3 or at your option, any  later option.
But versions of the code created and/or distributed *on or after* that date must be distributed
under the GNU *Affero* General Public License, version 3, or, at your option, any later version.

TheDiscordMathProblemBotRepo - Denylistable

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
import time
from .dict_convertible import DictConvertible


class Denylistable(DictConvertible):
    """Objects of this class can be denylisted, removed from the denylist, and have 3 attributes"""
    denylisted: bool
    denylist_reason: str
    denylist_expiry: float
    def denylist(self, reason: str = "", duration: float = float('inf')):
        """Denylist this object for a specific duration with a reason"""
        if not isinstance(reason, str):
            raise TypeError("reason is not a str")
        if not isinstance(duration, float):
            raise TypeError("duration is not a float")
        if duration < 0:
            raise ValueError("You're denylisting for negative time")
        self.denylist_expiry = time.time() + duration
        self.denylisted = True
        self.denylist_reason = reason

    def undenylist(self):
        """Remove the object from the denylist"""
        if not self.is_denylisted():
            raise RuntimeError("This user is not currently denylisted!")
        self.denylisted = False
        self.denylist_expiry = 0.0
        self.denylist_reason = ""
    def is_denylisted(self) -> bool:
        """Check if this object is currently denylisted"""
        if not self.denylisted:
            return False
        return time.time() < self.denylist_expiry