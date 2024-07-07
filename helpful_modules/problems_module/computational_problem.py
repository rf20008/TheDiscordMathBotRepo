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

from copy import deepcopy

import mpmath

from .base_problem import BaseProblem


class ComputationalProblem(BaseProblem):
    def __init__(self, *args, **kwargs):
        tolerance = kwargs.pop("tolerance", 0.001)
        super().__init__(*args, **kwargs)
        if not isinstance(tolerance, float) and tolerance is not None:
            raise TypeError("tolerance isn't a float")
        self.tolerance = tolerance

    def check_answer(self, answer):
        if super().check_answer(answer):
            return True
        if self.tolerance is None:
            return False
        if isinstance(answer, str):
            # try to partition it to try to parse it as a complex
            try:
                try:

                    real, plus, imag = answer.partition("+")
                    answer = mpmath.mpc(real, imag[:-1])
                except ValueError:
                    answer = mpmath.mpc(answer)
            except ValueError:
                # we can't parse it as a complex
                return False

        return any(
            abs(answer - complex(correct_answer)) <= self.tolerance
            for correct_answer in self.answers
        )

    def get_extra_stuff(self):
        return {"tolerance": self.tolerance, "type": "ComputationalProblem"}

    def __deepcopy__(self, memodict: dict):
        return ComputationalProblem(
            question=deepcopy(self.question),
            voters=deepcopy(self.voters),
            answers=deepcopy(self.answers),
            solvers=deepcopy(self.solvers),
            author=deepcopy(self.author),
            id=deepcopy(self.id),
            guild_id=deepcopy(self.guild_id),
            **deepcopy(self.get_extra_stuff()),
        )
