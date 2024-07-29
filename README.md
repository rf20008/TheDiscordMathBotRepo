[![Number of source lines of code](https://img.shields.io/tokei/lines/github/rf20008/TheDiscordMathProblemBotRepo)](https://img.shields.io)
<!---TODO: rewrite--->
# Quick links / Table of Contents

## Quick links
Invite - https://discord.com/oauth2/authorize?client_id=845751152901750824&scope=bot+applications.commands&permissions=2147535872 <br>
Terms & Conditions - https://github.com/rf20008/TheDiscordMathProblemBotRepo/blob/beta/TERMS_AND_CONDITIONS.md
Privacy Policy - https://github.com/rf20008/TheDiscordMathProblemBotRepo/blob/beta/PRIVACY_POLICY.md

## Table of Contents
<!----- todo: use links----->
DISCLAIMERS <br>
* Legal Disclaimers <br>
If you run into issues <br>
Announcements <br>
Contribute :-) <br>
Invite my bot! <br>
Documentation <br>
Self-host my bot <br>
 * Steps <br>
 * Update the bot with my changes <br>
 * env key-value pairs required <br>
Attribution/Contributors <br>
# DISCLAIMER

My bot is just a platform for storing problems. If someone submits a copyrighted problem, I'm not responsible, but they are. You can look up who submitted a problem using /show_problem_info.
(If you need to, you can submit a request using /submit_a_request)
# Legal Disclaimers
1) I am not a lawyer. I did not write this file with assistance from any lawyers, and I did not ask for any legal advice while writing this. As of February 4, 2024, I am a high school student who is not studying law.
2) This file is not intended to be legal advice, and does not constitute legal advice. This file is supposed to be a README to introduce people to my bot.
3) This file is NOT LEGALLY BINDING and DOES NOT constitute an agreement between you and me.
# If you run into issues
If you run into any issues create an issue or DM me (ay136416#2707).
However, this bot is mainly for **my fun** and may not be supported that often.

# Announcements

<ol>
<li> As of July 28, 2024, I have migrated to the AGPLv3 since my bot is a Discord Bot and it inherently works over a network</li>
<li> CC-BY-SA 4.0 is no longer a valid license to use this bot under! You **must** license the bot under GPLv3 (or a later version.)
(CC-BY-SA 4.0 has a one way migration to GPLv3, so you are allowed to do this. </li>
<li> **Everything (even things that do not explicitly say they are licensed under AGPLv3) in this repository except for things that are ignored in .gitignore are licensed under AGPLv3. This includes every python file.** </li>
</ol>



# Contribute :-)

If you open a PR/Issue, I'll look at it and maybe merge it! <br>
A few guidelines:
1) Use the main branch, not master <br>
2) If you are pull requesting to my bot directly into the main branch, please make sure your code works! <br>
3) If you are pull requesting to my bot via the beta branch, please make sure your code works, but it is okay if it doesn't (for now), but later, not so much <br>
4) This bot is coded using OOP and abstraction, so if you want to add a new feature or change an existing one, please keep this in mind. <br>
5) main.py is used to run the bot! helpful_modules include essential elements of the bot, but are not exposed to the user (basically utils). cogs is the cogs!<br>
6) No syntax errors, please! <br>
7) You should lint your code. (this uses [python-black](https://pypi.org/project/black/)) <br>
8) Follow common sense <br>
9) Make sure to follow GPLv3! (You'll need to include the link to the modified version of my code and make it somehow __***easily***__ accessible through the bot (or if you're just fixing a bug the 'forked from' label should be enough attribution), state significant changes made to the software, include the license (which is already done for you, don't modify LICENSE. Treat it as read-only.) You must state if )
# Invite my bot!

Recommended invite: https://discord.com/oauth2/authorize?client_id=845751152901750824&scope=bot+applications.commands&permissions=2147535872

(However, the bot is in an alpha phase. I do not make any guarantees that it will work right now)

# Documentation

Documentation for my bot has been replaced with /documentation. I might set up a website soon. However, I don't have a domain.



# Self-host my bot
My code is open source, so you can! There may be bugs, however. Of course, I cannot stop you from self-hosting due to the GPLv3.

I only recommend self-hosting this if you want to help develop the bot or you want to host your own instance of this bot for your server.
Just follow the AGPLv3 and you're fine!

## Steps
(This assumes you already have knowledge of the command line and how to make a new discord application. If you don't have this knowledge, you probably aren't qualified to self-host a bot.)
If you don't, you can either help me with my code (if you want to modify the code and help everyone out) or invite my bot.
No privileged intents are required (the bot has been designed to not require privileged intents, but this is causing some non-essential features to be not-so-great)
1. Create a new Discord application with a bot user. Save the token (you will need it later)
2. You will need Python ~3.10~3.12. I have only tested this bot with CPython (which is the official Python implementation). If you don't already have Python 3.10 on your computer., install it [here](https://www.python.org/downloads/release/python-3101/).
3. Create a venv (execute ``python3.12 -m venv /path/to/new/virtual/environment``)
4. Move to your new venv (use the cd command)
5. Install poetry, a dependency installer (``pip3 install git+https://github.com/python-poetry/poetry.git``). You can also optionally install it outside.
6. Clone my repo (``git clone https://github.com/rf20008/TheDiscordMathProblemBotRepo``)
7. Move to the new directory containing the repository you cloned (which should be this one. The folder name is the same name as the repository name)
8. Create a .env file inside the repository folder. Inside it, you need to put your discord token, SQLite database path (or not). Make sure to follow the env key-value pairs! 
Make sure to add the env keys listed below.
9. __***MAKE SURE YOUR SOURCE CODE IS PUBLIC (OR AVAILABLE TO THE PEOPLE WHO USE IT)!***__ This is for compliance with GPLv3.
10. Run the main.py file (```poetry install; pip3 install -r requirements.txt; python3 main.py```) Don't use the -O / -OO option (assert statements are necessary to run the bot, and they only run if \_\_debug\_\_ is true, which is not the case if the -O option is given)
11. Invite the bot  (use the invite link, but replace the client_id field with your bot's client id)
12. Make sure you follow the AGPL and provide copies of your source code to people who use your bot!
## Update the bot with my changes

1. Run ``cd path/to/your/repo/``
2. Run ``git pull`` (updates the repo). If you haven't cloned the repo.
3. If there are any merge conflicts, please fix them. Then do step 2. If there are no merge conflicts, skip this step.
4. Stop your bot! And then re-start it again (follow step 10.)


## .env key-value pairs required

Required:
DISCORD_TOKEN: your discord token
use_sqlite: str (if not set to the string "True", mysql will be used) # Use this for local testing, and mysql for global testing
Eventually will be unused (and removed)
sqlite_database_path: path to sqlite db
mysql_db_ip: The IP/webserver of the MySQL database
mysql_db_username: Your username to the MySQL database
mysql_db_pass: Your password to the MySQL database
mysql_db_name: Your MySQL database name
source_code_link: link to the place that contains the bot's source code. This must be public and have the actual source code 
 Filling it out __should__ fulfill the "Disclose source" requirement of GPLv3, if it is valid). However, unless I am sued or legally obligated to check if it's valid, I won't check. 
I might still check

## Attribution / Contributors

MySQL: https://pypi.org/project/mysql-connector-python/#files <br>
GPLv3 simplified: https://tldrlegal.com/license/gnu-general-public-license-v3-(gpl-3) <br>
@duck-master helped me revise the privacy policy. Thanks so much! <br>
(get_git_revision_hash)[https://stackoverflow.com/a/21901260] <br>
Disabling buttons: https://stackoverflow.com/questions/68842747/how-to-disable-button-once-it-is-clicked-in-discord-js-13 & help from @umairshasheen78 (through Discord) <br>
MySQL placeholders: https://stackoverflow.com/questions/2527941/python-mysqldb-placeholders-syntax#2527950 <br>
https://stackoverflow.com/a/21901260 for the get_git_revision_hash :-) <br>
Disnake: https://github.com/DisnakeDev/disnake <br>
Bot avatar: https://thumbs.dreamstime.com/z/creative-division-sign-circular-cold-gradient-spectrum-original-152718833.jpg <br>
And the many un-listed people who contributed ideas/code! <br>
