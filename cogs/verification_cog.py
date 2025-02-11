"""Copyright © Samuel Guo / rf20008 (on Github) / ay136416 (on Discord) 2021-present

You can distribute any version of the Software created and distributed *before* 23:17:55.00 July 28, 2024 GMT-4
under the GNU General Public License version 3 or at your option, any  later option.
But versions of the code created and/or distributed *on or after* that date must be distributed
under the GNU *Affero* General Public License, version 3, or, at your option, any later version.

This file is part of TheDiscordMathProblemBotRepo

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

import asyncio
import datetime
import time
import traceback

import disnake
import cryptography
from disnake import ApplicationCommandInteraction
from disnake.ext import commands

import helpful_modules.checks
from helpful_modules.custom_bot import TheDiscordMathProblemBot
from helpful_modules import problems_module
from helpful_modules.custom_embeds import SuccessEmbed, SimpleEmbed, ErrorEmbed
from .helper_cog import HelperCog

ONE_WEEK = datetime.timedelta(weeks=1).total_seconds()


# TODO: add the /verification_codes info command
# TODO: add the /verification_codes check command
# TODO: add the /verification_codes delete command
# TODO: add stuff to my TOS about verification codes

class VerificationCog(HelperCog):
    bot: TheDiscordMathProblemBot

    def __init__(self, bot: TheDiscordMathProblemBot):
        super().__init__(bot)

    @commands.slash_command(
        name="verification_codes", description="Manage your verification codes", options=[]
    )
    async def verification_codes(self, inter: disnake.ApplicationCommandInteraction):
        """
        /verification_codes
        This subclass is used to manage your verification codes
        """
        pass

    @verification_codes.sub_command(
        name="generate",
        description="Generate a new verification code",
        options=[
            disnake.Option(
                name="duration",
                description="How long your verification code should last for (in seconds)",
                type=disnake.OptionType.number,
                required=False,
                min_value=1e-200
            ),
            disnake.Option(
                name="here",
                description="Whether to send your code here (ephemerally) or into your DMs",
                type=disnake.OptionType.boolean,
                required=False,
            )
        ]
        # TODO: add a WHERE option
    )
    async def generate(self, inter: disnake.ApplicationCommandInteraction, duration: float = ONE_WEEK,
                       here: bool = True):
        """/verification_codes generate [duration: float = 604800] [here: bool = True]
        Generate a verification code, valid for `duration` seconds.
        Your code will be sent as an ephemeral message if `here` is true; otherwise, it will be sent to your DMs.
        KEEP YOUR CODES PRIVATE!!! If someone else gets your code, they can impersonate you!!!"""
        if duration < 0:
            await inter.send(embed=ErrorEmbed("Your code must be valid for a positive amount of time"))
            return
        code_info, code = await problems_module.VerificationCodeInfo.generate_verification_code_info(
            user_id=inter.author.id,
            duration=duration
        )
        await self.bot.cache.set_verification_code_info(code_info)
        # TODO: log code generation
        if here:
            await inter.send(
                embed=SuccessEmbed(
                    f"I have successfully set your code information! Your secret code is `{code}`."
                    f" Keep it secret OR ELSE PEOPLE CAN IMPERSONATE YOU!!!!!!"
                ),
                ephemeral=True
            )
            return
        else:
            await inter.send(embed=SuccessEmbed("I have sent your code to your DMs!"))
            await inter.author.send(embed=SuccessEmbed(
                f"Your secret code is `{code}`. "
                f"Keep it secret OR ELSE PEOPLE CAN IMPERSONATE YOU!!!!!!"
            ))
            return

    @verification_codes.sub_command(
        name="info",
        description="Get information about your verification code",
        options=[
            disnake.Option(
                name="detailed",
                description="whether your information should be detailed",
                required=False,
                type=disnake.OptionType.boolean
            )
        ]
    )
    async def info(self, inter: disnake.ApplicationCommandInteraction, detailed: bool = False):
        """/verification_codes info [detailed: bool = False]
        Get info about your verification code (if you have one)"""
        # Give them remaining duration, total duration, expiry, and
        print("HEHE!")
        try:
            vcode_info: problems_module.VerificationCodeInfo = await self.bot.cache.get_verification_code_info(inter.author.id)
        except problems_module.VerificationCodeInfoNotFound as e:
            print(e)
            await inter.send("You don't have a verification code! Try using /verification_codes generate.")
            return
        embed = SuccessEmbed(title='Your verification code info')
        embed.add_field("User id", inter.author.id)
        embed.add_field("Created at", disnake.utils.format_dt(vcode_info.created_at, 'F'))
        embed.add_field(
            name="Expiry status",
            value=f"{'Expired' if vcode_info.is_expired else 'Valid'} (expire{'d' if vcode_info.is_expired else 's'} at {disnake.utils.format_dt(vcode_info.expiry, 'F')}"
        )
        if detailed:
            embed.add_field("Scrypt N", vcode_info.scrypt_parameters.scrypt_n)
            embed.add_field("Scrypt P", vcode_info.scrypt_parameters.scrypt_p)
            embed.add_field("Scrypt R", vcode_info.scrypt_parameters.scrypt_r)
            embed.add_field("Scrypt len", vcode_info.scrypt_parameters.scrypt_len)
        await inter.send(embed=embed)
        return


    @commands.cooldown(2, 15.0, type=commands.BucketType.user)
    @verification_codes.sub_command(
        name="check",
        description="Check whether your verification code is the string provided",
        options=[
            disnake.Option(
                name="possible_code",
                description="What you think your code is",
                required=True,
                type=disnake.OptionType.string
            ),
            disnake.Option(
                name="person",
                description="Who to check this code for (for owners only) (provide a USER ID)",
                required=False,
                type=disnake.OptionType.integer
            )
        ]
    )
    async def check(self, inter: disnake.ApplicationCommandInteraction, possible_code: str, person: int | None = None):
        """/verification_codes check (possible_code: str) [person: int]
        Check whether the code of `person` is `possible_code`.
        Rate limit: 2 times per 15.0 seconds.
        You can only set `person` if you own this bot.
        person is the user_id of the person you want to check."""
        # only owners can set `person`
        if person is not None and not await self.bot.is_owner(inter.author):
            await inter.send(
                embed=ErrorEmbed("You can only check your own verification codes because you don't own the bot"),
                ephemeral=True)
            return
        # who's the target?
        target = inter.author.id
        print(person)
        if person is not None:
            target = person

        # get the code
        try:
            code_info: problems_module.VerificationCodeInfo = await self.bot.cache.get_verification_code_info(
                user_id=target)
        except problems_module.VerificationCodeInfoNotFound:
            if person != inter.author.id and person is not None:
                await inter.send(
                    embed=ErrorEmbed(f"The user with user id {person} does not have a verification code set."),
                    ephemeral=True)
            else:
                await inter.send(embed=ErrorEmbed("You don't have a verification code set. Try setting one!"),
                                 ephemeral=True)

            # try to remove their code
            await self.bot.cache.delete_verification_code_info(user_id=target)
            return

        # check the code now!
        try:
            await code_info.check_code(possible_code)
            await inter.send(embed=SuccessEmbed(f"Your verification code is {possible_code}! Keep this a secret."),
                             ephemeral=True)
            return

        except problems_module.VerificationCodeExpiredException:
            # the code is expired
            if person is not None:  # is it for someone else?
                await inter.send(embed=ErrorEmbed(f"The user with user id {person}'s verification code has expired."),
                                 ephemeral=True)
            else:
                await inter.send(embed=ErrorEmbed("Your verification code has expired. Please generate a new one"),
                                 ephemeral=True)
            return
        except cryptography.exceptions.InvalidKey:
            await inter.send(f"Your verification code is NOT {possible_code}. Keep this a secret")
            return

    @verification_codes.sub_command(
        name="delete",
        description="Delete your verification code information",
        options=[disnake.Option(
            name="person",
            description="Who to check this code for (for owners only) (provide a USER ID)",
            required=False,
            type=disnake.OptionType.integer
        )]
    )
    async def delete(self, inter: disnake.ApplicationCommandInteraction, person: int | None = None):
        """/verification_codes
        Delete your (or someone else's) verification code.
        If you don't own this bot, you can only delete your own verification code!"""
        if person is not None and not await self.bot.is_owner(inter.author):
            await inter.send(
                embed=ErrorEmbed("You can only delete your own verification codes if you aren't the owner!"),
                ephemeral=True)

        # target
        target = inter.author.id if person is None else person
        # do they even have a code?
        try:
            code_info: problems_module.VerificationCodeInfo = await self.bot.cache.get_verification_code_info(
                user_id=target)
        except problems_module.VerificationCodeInfoNotFound:
            if person is not None:
                await inter.send(
                    embed=ErrorEmbed(f"The user with user id {person} does not have a verification code set."),
                    ephemeral=True)
            else:
                await inter.send(embed=ErrorEmbed("You don't have a verification code set. Try setting one!"),
                                 ephemeral=True)
            return

        # actually delete
        await self.bot.cache.delete_verification_code_info(user_id=target)

        # and tell them
        if person:
            await inter.send(embed=SuccessEmbed(
                f"I successfully deleted the verification code of the user whose user id is {person}. "
                f"However, they have not been notified."
                f"You should notify them (I won't notify them, because of the Discord TOS)"), ephemeral=True)
        else:
            await inter.send(embed=SuccessEmbed("I successfully deleted your verification code!"))

        return

    @commands.slash_command(
        name="vcode_denylist",
        description="Denylist someone from the verification code system (for trusted users only)",
        options=[
            disnake.Option(
                name="user",
                description="The user to denylist",
                type=disnake.OptionType.user,
                required=True,
            ),
            disnake.Option(
                name="reason",
                description="Why you're denylisting this user",
                type=disnake.OptionType.string,
                required=True
            ),
            disnake.Option(
                name="duration",
                description="The length of the denylist",
                type=disnake.OptionType.number,
                required=False,
                min_value=0.0
            )
        ]
    )
    @helpful_modules.checks.trusted_users_only()
    async def vcode_denylist(self, inter: disnake.ApplicationCommandInteraction, user: disnake.User, reason: str,
                             duration: float = float('inf')):
        """/vcode_denylist [user: User] [reason] (duration: float=inf)
        Denylist someone from the verification code system!
        ONLY for admins!"""
        # part 1: recheck
        print("NO")
        if not await self.bot.is_trusted(inter.author):
            await inter.send(embed=ErrorEmbed("You are not allowed to perform this action!"), ephemeral=True)
            return
        # step 2: recheck the status
        status: problems_module.UserData = await self.bot.cache.get_user_data(user.id,
                                                                              default=problems_module.UserData.default(
                                                                                  user.id))
        # even if they're denylisted we'll overwrite
        status.verification_code_denylist.denylisted = True
        status.verification_code_denylist.denylist_expiry = time.time() + duration
        status.verification_code_denylist.denylist_reason = reason
        await self.bot.cache.set_user_data(user_id=user.id, new=status)
        await inter.send(embed=SuccessEmbed(
            f"{user.display_name} has been successfully added to the denylist of the verification code system!"),
            ephemeral=True)
        return

    @commands.slash_command(
        name="vcode_undenylist",
        description="Remove the denylist of someone from the verification code system (for trusted users only)",
        options=[
            disnake.Option(
                name="user",
                description="The user of which to remove the denylist",
                type=disnake.OptionType.user,
                required=True,
            )
        ]
    )
    @helpful_modules.checks.trusted_users_only()
    async def vcode_undenylist(self, inter: disnake.ApplicationCommandInteraction, user: disnake.User):
        """/vcode_undenylist [user: User] [reason] (duration: float=inf)
        Remove someone's denylist from the verification code system
        ONLY for admins!"""
        if not await self.bot.is_trusted(inter.author):
            await inter.send(embed=ErrorEmbed("You are not allowed to perform this action!"), ephemeral=True)
            return
        # step 2: recheck the status
        status: problems_module.UserData = await self.bot.cache.get_user_data(user.id,
                                                                              default=problems_module.UserData.default(
                                                                                  user.id))
        # even if they're denylisted we'll overwrite
        status.verification_code_denylist.denylisted = False
        status.verification_code_denylist.denylist_expiry = time.time() - 1.0
        status.verification_code_denylist.denylist_reason = ""
        await self.bot.cache.set_user_data(user_id=user.id, new=status)
        await inter.send(embed=SuccessEmbed(
            f"{user.display_name} has been successfully removed from the denylist of the verification code system!"),
            ephemeral=True)
        return

    async def cog_slash_command_check(self, inter: ApplicationCommandInteraction) -> bool:
        """Check that someone is not denylisted from the verification code denylist system!"""
        try:
            status: problems_module.UserData = await asyncio.wait_for(self.bot.cache.get_user_data(inter.author.id), timeout=1)
        except asyncio.TimeoutError as error:
            return False
        if not hasattr(status, "verification_code_denylist"):
            return True
        deny = status.verification_code_denylist.is_denylisted()
        if not deny:
            return True
        if status.verification_code_denylist.denylist_expiry == float('inf'):
            until_str = 'never'
        else:
            if status.verification_code_denylist.denylist_expiry < time.time():
                until_str = f"{disnake.utils.format_dt(status.verification_code_denylist.denylist_expiry, 'R')} ago"
            else:
                until_str = f'in {disnake.utils.format_dt(status.verification_code_denylist.denylist_expiry, "R")}'
        msg = f"""You are denylisted from the verification code system! To appeal, you must use /appeal. Note that appeals are seen very rarely...,
        The reason you've been denylisted is {status.verification_code_denylist.denylist_reason}. This ban expires {until_str}"""
        raise helpful_modules.checks.DenylistedException(
            msg
        )


def setup(bot: TheDiscordMathProblemBot):
    bot.add_cog(VerificationCog(bot))
