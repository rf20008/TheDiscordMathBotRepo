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
import os

import disnake
from disnake.ui import Modal

from .base_on_error import base_on_error


class MyModal(Modal):
    """A wrapper around disnake.Modal that allows passing in a custom callback :-)"""

    def __init__(self, *args, **kwargs):
        async def default_callback(modal, modal_inter, *args, **kwargs):
            raise NotImplementedError

        self._callback = kwargs.pop("callback", default_callback)

        async def _check(inter, *args, **kwargs):
            raise NotImplementedError("You need to implement this check yourself!")

        kwargs["custom_id"] = (
            kwargs["custom_id"]
            if "custom_id" in kwargs.keys()
            else os.urandom(20).hex()
        )
        self._check = kwargs.pop("check", _check)
        self._extra_args = kwargs.pop("extra_args", [])
        self._on_error = kwargs.pop("on_error", MyModal.on_error)
        self._inter: disnake.ApplicationCommandInteraction = kwargs.pop("inter", None)
        self.on_timeout = kwargs.pop("on_timeout", MyModal.on_timeout)
        super().__init__(*args, **kwargs)

    async def callback(self, inter: disnake.ModalInteraction):
        if await self._check(inter):
            await self._callback(self, inter, *self._extra_args)

    async def on_error(self, error, inter):
        await inter.send(**(await base_on_error(inter, error)))

    async def on_timeout(self):
        await self._inter.send("You didn't submit the modal fast enough!")
        return
