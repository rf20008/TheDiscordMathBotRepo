"""
You can distribute any version of the Software created and distributed *before* 23:17:55.00 July 28, 2024 GMT-4
under the GNU General Public License version 3 or at your option, any  later option.
But versions of the code created and/or distributed *on or after* that date must be distributed
under the GNU *Affero* General Public License, version 3, or, at your option, any later version.

This file is part of The Discord Math Problem Bot Repo

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
import json
import warnings

from . import problems_module
from .problems_module import AppealQuestion
numFileSavers = 0


class FileSaver:
    """A class that saves files"""

    def __init__(
        self,
        name=None,
        enabled=False,
        printSuccessMessagesByDefault=False,
    ):
        """Creates a new FileSaver object."""
        global numFileSavers
        numFileSavers += 1
        if name is None:
            name = "FileSaver" + str(numFileSavers)
        self.id = numFileSavers
        self.printSuccessMessagesByDefault = printSuccessMessagesByDefault
        self.enabled = True
        self.name = name

    def __str__(self):
        return self.name

    def enable(self):
        """Enables self."""
        self.enabled = True

    def disable(self):
        """Disables self"""
        self.enabled = False

    def load_files(self, main_cache, printSuccessMessages=None):
        """Loads files from file names specified in self.__init__."""
        if not isinstance(
            main_cache, problems_module.MathProblemCache
        ) and not isinstance(main_cache, problems_module.RedisCache):
            raise TypeError("main_cache is not a MathProblemCache.")
        if not self.enabled:
            raise RuntimeError("I'm not enabled! I can't load files!")
        trusted_users = []
        if (
            printSuccessMessages
            or printSuccessMessages is None
            and self.printSuccessMessagesByDefault
        ):
            print(
                f"{str(self)}: Attempting to load vote_threshold from vote_threshold.txt, trusted_users_list from trusted_users.txt, and math_problems  from math_problems.json..."
            )
        with open("math_problems.json", "r") as file:
            mathProblems = json.load(fp=file)

        with open("trusted_users.txt", "r") as file2:
            for line in file2:
                trusted_users.append(int(line))
        vote_threshold = False
        with open("vote_threshold.txt", "r") as file3:
            lines = file3.readlines()
            for line in lines:
                # Make sure that an empty string does not become the new vote threshold
                if line.strip().isnumeric(): # .strip() is needed to make sure that we remove the trailing newline
                    vote_threshold = int(line)
        if vote_threshold is False:
            raise RuntimeError("vote_threshold not given!!")

        with open("guild_math_problems.json", "r") as file4:
            guildMathProblems = json.load(fp=file4)


        questions = self.load_appeal_questions()
        if (
            printSuccessMessages
            or printSuccessMessages is None
            and self.printSuccessMessagesByDefault
        ):
            print(f"{self.name}: Successfully loaded files.")

        return {
            "guildMathProblems": guildMathProblems,
            "trusted_users": trusted_users,
            "mathProblems": mathProblems,
            "vote_threshold": vote_threshold,
            "appeal_questions": questions
        }

    def save_files(
        self,
        main_cache=None,
        printSuccessMessages=None,
        *,
        guild_math_problems_dict={},
        vote_threshold=3,
        math_problems_dict={},
        trusted_users_list={},
        questionnaire: dict[str, list[AppealQuestion]] | None = None
    ):
        """Saves files to file names specified in __init__.
        It does NOT SAVE the math_problems_dict"""

        if not isinstance(
            main_cache, problems_module.MathProblemCache
        ) and not isinstance(main_cache, problems_module.RedisCache):
            raise TypeError("main_cache is not a MathProblemCache.")
        if not self.enabled:
            raise RuntimeError("I'm not enabled! I can't load files!")
        if (
            printSuccessMessages
            or printSuccessMessages is None
            and self.printSuccessMessagesByDefault
        ):
            print(
                f"{str(self)}: Attempting to save math problems vote_threshold to vote_threshold.txt, trusted_users_list to  trusted_users.txt..."
            )
        # main_cache.update_file_cache() #Removed method

        with open("trusted_users.txt", "w") as file2:
            warnings.warn(category=DeprecationWarning, message="storing trusted users in a dict is deprecated and should be removed")

            for user in trusted_users_list:
                file2.write(str(user))
                file2.write("\n")
                # print(user)

        with open("vote_threshold.txt", "w") as file3:
            file3.write(str(vote_threshold))
        with open("guild_math_problems.json", "w") as file4:
            warnings.warn(category=DeprecationWarning,
                          message="storing GuildMathProblems in a dict is deprecated and should be removed")
            e = json.dumps(obj=guild_math_problems_dict)
            file4.write(e)
        with open("math_problems.json", "w") as file5:
            warnings.warn(category=DeprecationWarning,
                          message="storing MathProblems in a dict is deprecated and should be removed")
            json.dump(fp=file5, obj=math_problems_dict)
        with open("appeal_questions.json", "w") as file6:
            json.dump(fp=file6, obj={key: [question.to_dict for question in questionset] for key, questionset in questionnaire.items()})

        if (
            printSuccessMessages
            or printSuccessMessages is None
            and self.printSuccessMessagesByDefault
        ):
            print(f"{self.name}: Successfully saved files.")

    def change_name(self, new_name):
        self.name = new_name

    def my_id(self):
        return self.id

    def goodbye(self):
        print(str(self) + ": Goodbye.... :(")
        del self
    def load_appeal_questions(self):
        with open("appeal_questions.json", "r") as file5:
            questions = json.load(fp=file5)
        # turn the questions into AppealQuestions
        # Iterate over each key - value pair in the questions dictionary
        for key, questionset in questions.items():
            l = []
            for question in questionset:
                print(question)
                l.append(AppealQuestion.from_dict(question))
            # Convert each dictionary in the questionset to an AppealQuestion object
            questions[key] = [AppealQuestion.from_dict(question) for question in questionset]
        return questions