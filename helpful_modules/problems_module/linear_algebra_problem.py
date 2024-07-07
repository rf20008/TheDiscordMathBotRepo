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

import numbers
from copy import deepcopy

import mpmath

from .base_problem import BaseProblem
from .errors import LinearAlgebraUserInputErrorException, MathProblemsModuleException

BOT_ID = 845751152901750824
TOLERANCE = 1e-3
FORMAT_HELP = """To answer this question, give your answer in the form var1 var2 var3 ... varN. You must put the 
values of each variable space-separated, without "var1=". Also, each value cannot have any spaces. For example, 
if the solution is (var1, var2) = (3,4), the **only** correct answer is "3 4". Some teachers may ask you to answer in 
the form "(var name for all var names) = (ordered tuple)". For example, they may ask you to say "(var1, var2) = (3,
4)". However, this WILL NOT be accepted! Also, you cannot enter your answer in any other form. You cannot say "x=3, 
y=4" or "var1=3, var2=4", etc. They will not be parsed correctly. Remember that you cannot have **ANY** spaces in any 
of the tokens!!!! The reason for this extreme formatting format is that I don't want to have to parse many different 
formats."""


class LinearAlgebraProblem(BaseProblem):
    """
    Represents a linear algebra problem.

    Attributes:
        coeffs (list): A list of coefficient matrices for the linear equations.
        equal_to (list): A list of values equal to the right-hand side of the equations.
    """

    coeffs: list
    equal_to: list

    def __init__(self, *args, **kwargs):
        """
        Initializes a LinearAlgebraProblem instance.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        self.coeffs = kwargs.pop("coeffs")
        self.equal_to = kwargs.pop("equal_to")
        super().__init__(*args, **kwargs)

    @classmethod
    def from_coefficients(
        cls,
        coeffs: list,
        equal_to: list,
        author_id: int = BOT_ID,
        guild_id: str | None = None,
        *args,
        **kwargs,
    ):
        """
        Creates a LinearAlgebraProblem instance from coefficients.

        Args:
            coeffs (list): A list of coefficient matrices for the linear equations.
            equal_to (list): A list of values equal to the right-hand side of the equations.
            author_id (int): The author's ID. Defaults to 845751152901750824.
            guild_id: The guild's ID. Defaults to None.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            LinearAlgebraProblem: An instance of LinearAlgebraProblem.
        """
        question = "Solve the following system of equations: "
        if not isinstance(equal_to, list):
            raise TypeError("Equal_to is not a list, but it must be a list")
        num_eqs = len(equal_to)
        if not isinstance(coeffs, list):
            raise TypeError("coeffs must be a list")
        if not coeffs:
            raise ValueError("No coefficients given!")
        if num_eqs != len(coeffs):
            raise ValueError(
                "The number of equations does not match the number of coefficient sets"
            )

        num_vars = len(coeffs[0])
        for equation_id in range(len(coeffs)):
            equation = coeffs[equation_id]
            if len(equation) != num_vars:
                raise ValueError(
                    "coeffs is not a rectangular matrix. You must pass in a rectangular matrix"
                )
            eq = ""
            for i in range(len(equation)):
                coeff = equation[i]
                if (
                    not isinstance(coeff, float)
                    and not isinstance(coeff, numbers.Number)
                    and not isinstance(coeff, mpmath.mpc)
                    and not isinstance(coeff, complex)
                ):
                    raise ValueError(
                        "A non-numeric value was found. All coefficients must be numbers"
                    )
                if coeff == 0:
                    continue
                elif isinstance(coeff, numbers.Real) and coeff < 0:
                    eq += "-"
                else:
                    eq += "+"
                eq += f"{coeff}*(var{i})"
            eq += f"={equal_to[equation_id]}\n"
            question += eq
        question += FORMAT_HELP
        question += f"\n Your answer will be considered correct if it satisfies each equation to within {TOLERANCE} absolute or relative precision"
        return LinearAlgebraProblem(
            question,
            *args,
            coeffs=coeffs,
            equal_to=equal_to,
            author=author_id,
            guild_id=guild_id,
            **kwargs,
        )

    def check_answer(self, answer):
        """
        Checks if the provided answer is correct.

        Args:
            answer (str): The answer provided by the user.

        Returns:
            bool: True if the answer is correct, False otherwise.
        """
        tokens = answer.split(" ")
        tokens = list(
            map(lambda tok: tok.replace("i", "j"), tokens)
        )  # remember: we use j for complex numbers in Python
        try:
            values = list(map(mpmath.mpc, tokens))
        except ValueError:
            tokens_that_dont_work = []
            for token in tokens:
                try:
                    mpmath.mpc(token)
                except ValueError:
                    tokens_that_dont_work.append(token)
            raise LinearAlgebraUserInputErrorException(
                f"Some tokens (specifically: {tokens_that_dont_work}) can't be converted to complex numbers"
            )
        for equation_idx in range(len(self.coeffs)):
            equation = self.coeffs[equation_idx]
            # compute values dot equation and check
            if len(equation) != len(self.coeffs[0]):
                raise MathProblemsModuleException(
                    "The matrix of coefficients is not rectangular"
                )
            if len(values) != len(equation):
                raise LinearAlgebraUserInputErrorException(
                    "You don't have enough variable values to satisfy all the equations"
                )
            lhs = 0.0
            for i in range(len(equation)):
                lhs += values[i] * equation[i]
            rhs = self.equal_to[equation_idx]
            diff = abs(lhs - rhs) / max(abs(lhs), abs(rhs), 1)
            if diff > TOLERANCE:
                return False
        return True

    def get_extra_stuff(self):
        """
        Gets extra information associated with the problem.

        Returns:
            dict: A dictionary containing extra information.
        """
        return {
            "coeffs": self.coeffs,
            "equal_to": self.equal_to,
            "type": "LinearAlgebraProblem",
        }

    def __deepcopy__(self, memodict: dict):
        return LinearAlgebraProblem(
            question=deepcopy(self.question),
            voters=deepcopy(self.voters),
            answers=deepcopy(self.answers),
            solvers=deepcopy(self.solvers),
            author=deepcopy(self.author),
            id=deepcopy(self.id),
            guild_id=deepcopy(self.guild_id),
            **deepcopy(self.get_extra_stuff()),
        )
