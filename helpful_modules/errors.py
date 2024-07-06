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
class NotInSupportServerWarning(Warning):
    """A warning when the bot's not in the support server"""
    pass


class AppealViewMessageNotFoundException(Exception):
    "Raised when the message of an appeal view isn't found"
    pass


class AppealViewChannelCantSeeException(Exception):
    """Raised when the bot can't see the #appeals channel or messages in it"""