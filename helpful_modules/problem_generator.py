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

import math
import random

import numpy as np

from helpful_modules.problems_module import ComputationalProblem, LinearAlgebraProblem
from helpful_modules.threads_or_useful_funcs import generate_new_id

BOT_ID = 845751152901750824
OPERATIONS = ["+", "-", "/", "*"]
COMPLEXITY_LIMIT = 200
NUMBER_RANGE = (-100, 100)
ANSWER_RANGE = (-30000, 30000)
ZERO_TOL = 1e-10


# these are from ChatGPT
def infix_to_postfix(infix_expression):
    precedence = {"+": 1, "-": 1, "*": 2, "/": 2, "^": 3}
    postfix_stack = []
    operator_stack = []
    operand = ""

    # Helper function to handle appending operands to the postfix stack
    def append_operand(op):
        if len(op) > 0:
            postfix_stack.append(op)

    for char in infix_expression:
        if char == " ":
            continue
        if char.isdigit():
            operand += char
        else:
            append_operand(operand)
            operand = ""
            if char == "(":
                operator_stack.append(char)
            elif char == ")":
                while operator_stack and operator_stack[-1] != "(":
                    postfix_stack.append(operator_stack.pop())
                if operator_stack:
                    operator_stack.pop()  # Discard the '('
            else:
                while operator_stack and precedence.get(
                    operator_stack[-1], 0
                ) >= precedence.get(char, 0):
                    postfix_stack.append(operator_stack.pop())
                operator_stack.append(char)

    append_operand(operand)

    # Append remaining operators from operator stack to postfix stack
    while operator_stack:
        postfix_stack.append(operator_stack.pop())

    return postfix_stack


def evaluate_postfix(postfix_expression):
    stack = []

    for token in postfix_expression:
        print(stack)
        if token.isdigit():
            stack.append(float(token))
        else:
            operand2 = stack.pop()
            operand1 = stack.pop()
            result = perform_operation(operand1, operand2, token)
            stack.append(result)

    return stack[0]


def perform_operation(operand1, operand2, operator):
    if operator == "+":
        return operand1 + operand2
    elif operator == "-":
        return operand1 - operand2
    elif operator == "*":
        return operand1 * operand2
    elif operator == "/":
        return operand1 / operand2
    elif operator == "^":
        return operand1**operand2


# the following implementation is from GFG. It is not mine
# link: https://www.geeksforgeeks.org/convert-infix-prefix-notation/
def is_operator(c: str):
    return not c.isalpha() and not c.isdigit()


def get_priority(c: str):
    if c in "+-":
        return 1
    if c in "*/":
        return 2
    if c == "^":
        return 3
    return 0


def infixToPostfix(infix):
    infix = "(" + infix + ")"
    l = len(infix)
    char_stack = []
    output = ""
    for i in range(l):
        # is it a digit/expression?:
        if infix[i].isalpha() or infix[i].isdigit():
            output += infix[i]
        elif infix[i] == "(":
            char_stack.append("(")
        elif infix[i]:
            # we need to reverse it because we have to pop
            while char_stack[-1] != "(":
                output += char_stack.pop()
            char_stack.pop()
        else:
            if is_operator(char_stack[-1]):
                if infix[i] == "^":
                    while get_priority(infix[i]) <= get_priority(char_stack[-1]):
                        output += char_stack.pop()
                else:
                    while get_priority(infix[i]) < get_priority(char_stack[-1]):
                        output += char_stack.pop()
                char_stack.append(infix[i])
    while len(char_stack) != 0:
        output += char_stack.pop()
    return output


def evaluate_postfix_expr(expr):
    thing_stack = []
    raise NotImplementedError("This is not implemented yet")


def generate_arithmetic_expression(complexity: int = 7):
    """Generate an arithmetic problem, the string expression (What is ...) and the answer"""
    if not isinstance(complexity, int):
        raise TypeError("Complexity is not an int")
    if complexity < 0 or complexity > COMPLEXITY_LIMIT:
        raise RuntimeError("The arithmetic expression is too complex")
    if complexity == 0:
        r = random.randint(*NUMBER_RANGE)
        if r >= 0:
            return str(r), r
        return f"({r})", r
    a = random.randint(0, complexity - 1)
    bef, bef_res = generate_arithmetic_expression(a)
    aft, aft_res = generate_arithmetic_expression(complexity - a - 1)
    while True:
        op = random.choice(OPERATIONS)
        match op:
            case "^":

                if math.log(abs(bef_res)) * aft_res > math.log(ANSWER_RANGE[1]):
                    continue
                if aft_res - math.floor(aft_res) >= 0.000001:
                    continue
                a = bef_res**aft_res
                if isinstance(a, complex):
                    if abs(a.imag) >= ZERO_TOL:
                        continue
                return (f"({bef} ^ {aft})"), (a)
            case "*":
                if not (ANSWER_RANGE[0] <= bef_res * aft_res <= ANSWER_RANGE[1]):
                    continue
                return (f"({bef} * {aft})", bef_res * aft_res)
            case "+":
                if not ANSWER_RANGE[0] <= (bef_res + aft_res) <= ANSWER_RANGE[1]:
                    continue
                return (f"({bef} + {aft})", bef_res + aft_res)
            case "-":
                if not ANSWER_RANGE[0] <= (bef_res - aft_res) <= ANSWER_RANGE[1]:
                    continue
                return (f"({bef}) - ({aft})", bef_res - aft_res)
            case "/":
                if abs(aft_res) < ZERO_TOL:
                    continue
                if not ANSWER_RANGE[0] <= (bef_res / aft_res) <= ANSWER_RANGE[1]:
                    continue
                return (f"({bef}/{aft})", bef_res / aft_res)
            case _:
                continue


def generate_arithmetic_problem(
    complexity: int = 7, guild_id: int | None = None, author_id: int = BOT_ID
):
    if not isinstance(complexity, int):
        raise TypeError("Complexity is not an int")
    if complexity < 0 or complexity > COMPLEXITY_LIMIT:
        raise RuntimeError("The arithmetic expression is too complex")
    expression, equalsto = generate_arithmetic_expression(complexity=complexity)
    return ComputationalProblem(
        question=f"Evaluate {expression}. Remember: this uses a computer. "
        f"Your answer will be considered correct "
        f"if it is within 0.1% relative tolerance or 0.001 absolute tolerance",
        answers=[equalsto],
        tolerance=0.001,
        guild_id=guild_id,
        author=author_id,
        id=generate_new_id(),
    )


def generate_linear_algebra_problem(
    num_vars: int = 3, guild_id: int | None = None, author_id: int = BOT_ID
):
    vars = np.array([random.randint(*NUMBER_RANGE) for _ in range(num_vars)])
    matrix = np.array(
        [
            [random.randint(*NUMBER_RANGE) for _ in range(num_vars)]
            for __ in range(num_vars)
        ]
    )
    equal_to = matrix.dot(vars)
    return LinearAlgebraProblem.from_coefficients(
        coeffs=list(map(list, matrix)),
        equal_to=list(equal_to),
        guild_id=guild_id,
        author_id=author_id,
        id=generate_new_id(),
    )
