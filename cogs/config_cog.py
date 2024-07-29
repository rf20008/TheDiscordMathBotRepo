"""
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
from typing import Optional

import disnake
from disnake import Guild, GuildCommandInteraction, Member, Permissions, Role, User
from disnake.ext import commands, tasks

from helpful_modules import checks, problems_module, the_documentation_file_loader
from helpful_modules.custom_bot import TheDiscordMathProblemBot
from helpful_modules.problems_module import GuildData, MathProblemCache
from helpful_modules.threads_or_useful_funcs import get_log

from .helper_cog import HelperCog

TAB_NEWLINE = "\t\n"  # This is because f-strings cannot contain backslashes...
CHECKS = ("mod_check", "can_create_problems_check", "can_create_quizzes_check")
# TODO: migrate to permissions v2 when https://github.com/DisnakeDev/disnake/pull/405 is merged


class GuildConfigCog(HelperCog):
    def __init__(self, bot: TheDiscordMathProblemBot):
        super().__init__(bot)
        self.bot = bot
        self.cache: problems_module.MathProblemCache = bot.cache

    async def sync_check(
        self, inter: GuildCommandInteraction, cache_name: str, role: Role
    ):
        if cache_name not in CHECKS:
            return await inter.send("This is not a valid check!")

        # TODO: Refactor - don't use setattr
        data = await self.cache.get_guild_data(
            guild_id=inter.guild_id, default=GuildData.default(inter.guild_id)
        )
        try:
            check = getattr(data, cache_name)  # Get the check
            role_permissions = role.permissions  # Cache the permissions
            check.permissions = [
                name
                for name in Permissions.VALID_FLAGS
                if getattr(role_permissions, name, False)
            ]
            # For each permission, add it to the list if the given role has that permission

            setattr(data, check_name, check)  # Set it to the data
            await self.cache.set_guild_data(data=data)  # And update it so it's not lost
            await inter.send("The check has been successfully updated!!")
        except AttributeError:
            await inter.send("Uh oh! An error occurred.")
            raise

    async def user_passes_guild_mod_check(
        self, guild: Guild, author: User | Member
    ) -> bool:
        data: problems_module.GuildData = await self.cache.get_guild_data(
            guild.id, default=problems_module.GuildData.default()
        )
        return data.mod_check.check_for_user_passage(author)

    async def cog_slash_command_check(
        self, inter: disnake.GuildCommandInteraction
    ) -> bool:
        """Make sure that only trusted users or guild owners or guild mods can run this command only in guilds!"""
        return (
            inter.guild_id is not None
            and inter.guild is not None  # This is a guild!
            and (
                await self.bot.is_trusted(inter.author)
                or inter.guild.owner_id == inter.author.id
                or await self.user_passes_guild_mod_check(
                    guild=inter.guild, author=inter.author
                )
            )
        )

    @commands.slash_command(
        description="Change your guild config!",
        default_member_permissions=Permissions(administrator=True),
    )
    async def guild_config(self, inter: disnake.GuildCommandInteraction):
        """/guild_config
        Modify your guild's config -- there are subcommands"""
        pass

    @guild_config.sub_command_group(
        description="Modify your guild's mod check!",
    )
    async def modify_mod_check(self, inter: GuildCommandInteraction):
        """/guild_config modify_mod_check
        Usage:
            /guild_config_modify_mod_check add_permission [permission: str]
            -- Add a permission. This permission must be a valid permission and match up exactly with Disnake's permission names.
            /guild_config modify_mod-check remove_permission [permission: str]
            Remove a permission needed from the list of permissions needed. WARNING: If you remove all the permissions needed (for moderatorship), then ANYONE in your server can run commands as a mod in the bot!


        """
        pass

    @modify_mod_check.sub_command(
        description="Add a permission to the list of required permissions to be a mod - more info in the description",
    )
    async def add_permission(self, inter: GuildCommandInteraction, permission: str):
        f"""/guild_config modify_mod_check add_permission [permission: str]
        Add a permission!
        The list of allowed permissions is added below.
        You must type each permission exactly, or the bot will not recongnize the permission.
        Someday, I could add a dropdown menu, but there are too many permissions!
        Permission list: {TAB_NEWLINE.join([permission for permission in Permissions.VALID_FLAGS.keys()])}"""
        if permission not in Permissions.VALID_FLAGS:
            return await inter.send("Invalid permission!")

        data = await self.cache.get_guild_data(
            inter.guild.id, default=GuildData.default()
        )
        data.mod_check.permissions_needed.append(permission)
        await self.cache.set_guild_data(data=data)
        await inter.send("This has been updated!")

    # TODO: Finish everything else!
    @modify_mod_check.sub_command(
        description="Remove a required permission from the mod check"
    )
    async def remove_a_required_permission(
        self, inter: GuildCommandInteraction, permission: str
    ):
        """/guild_config remove_a_required_permission [permission: str]
        Remove a required permission from the list of required permissions to meet the mod check!
        Warning: If you remove all required permissions, then ANYBODY can act as a moderator in your server in regards to this bot!
        """
        data = await self.cache.get_guild_data(
            inter.guild_id, default=problems_module.GuildData.default(inter.guild_id)
        )
        try:
            data.mod_check.permissions_needed.remove(permission)
        except (ValueError, TypeError) as t:
            await self.cache.set_guild_data(inter.guild_id, data)
            raise
        await inter.send("Successfully completed!")
        return

    @modify_mod_check.sub_command(
        description="Add a whitelisted user to the mod check",
    )
    async def add_whitelisted_user(self, inter: GuildCommandInteraction, user: Member):
        """/guild_config modify_mod_check add_whitelisted_user [user: User]
        Add a user to the whitelisted users part of the mod check - this will fail if the user is already whitelisted
        """
        data = await self.cache.get_guild_data(
            inter.guild_id,
            default=problems_module.GuildData.default(guild_id=inter.guild_id),
        )
        if user.id in data.mod_check.whitelisted_users:
            return await inter.send("This user is already whitelisted!")
        data.mod_check.whitelisted_users.append(user.id)
        await self.cache.set_guild_data(inter.guild_id, data)
        await inter.send("You have successfully added a whitelisted user!")
        return

    @modify_mod_check.sub_command(
        description="Remove a whitelisted user from the mod check",
    )
    async def remove_whitelisted_user(self, inter: GuildCommandInteraction, user: User):
        """/guild_config modify_mod_check remove_whitelisted_user [user: User]
        Remove a whitelisted user from the list of whitelisted users for the mod check. This will work even if the user is not whitelisted
        """
        # I have no way of telling whether the user is in the server - because I don't have the members intent
        # This doesn't seem like a valid reason that Discord would give me this intent
        # so I have to work around it
        data = await self.cache.get_guild_data(
            inter.guild_id,
            default=problems_module.GuildData.default(guild_id=inter.guild_id),
        )
        try:
            data.mod_check.whitelisted_users.remove(
                user.id
            )  # potentially O(N) operation
            await self.cache.set_guild_data(inter.guild_id, data=data)
            await inter.send("Data sent!")
            return
        except ValueError:
            await inter.send("This user is not whitelisted")
            return

    @modify_mod_check.sub_command(
        description="add_denylisted_user",
    )
    async def add_denylisted_user(self, inter: GuildCommandInteraction, user: User):
        """/guild_config modify_mod_check add_blacklisted_user [user: User]
        Add a denylisted user to the mod check, which prevents this user from interacting as a mod with this bot, even if they meet all other requirements
        """  # noqa: E401

        data = await self.cache.get_guild_data(
            inter.guild_id,
            default=problems_module.GuildData.default(guild_id=inter.guild_id),
        )
        data.denylisted_users.append(user.id)
        await self.cache.set_guild_data(inter.guild_id, data=data)
        await inter.send(
            "Successfully added a denylisted user to the list of denylisted users..."
        )

    @commands.slash_command(
        description="Remove a denylisted user from the list of denylisted users in the mod check",
    )
    async def remove_denylisted_user(self, inter: GuildCommandInteraction, user: User):
        """/guild_config modify_mod_check remove_denylisted_user [user: User]
        Attempt to remove a denylisted user from the list of denylisted users, and don't do anything if the user is not denyisted
        """
        data = await self.cache.get_guild_data(
            inter.guild_id, default=problems_module.GuildData.default()
        )
        try:
            data.mod_check.denylisted_users.remove(user.id)
            await self.cache.set_guild_data(inter.guild_id, data=data)
            await inter.send("Successfully removed the user's denylistness")
            return
        except ValueError:
            await inter.send(
                "The user is not denylisted, so I cannot undenylist the user from the mod check."
            )
            raise  # for debugging purposes

    @guild_config.sub_command(
        description="Sync a check's permissions with a role",
    )
    async def sync_required_permission(
        self, inter: GuildCommandInteraction, check_name: str, role: Role
    ):
        """/guild_config modify_mod_check sync_required_permission (check_name: str|mod_check|can_create_problems_check|can_create_quizzes_check) [role: Role]
        Sync the permissions needed of the given check with the role. This will be deprecated when Disnake supports permissions v2!

        """
        await self.sync_check(inter, check_name, role)


def setup(bot: TheDiscordMathProblemBot):
    bot.add_cog(GuildConfigCog(bot))
