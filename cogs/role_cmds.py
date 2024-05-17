"""
(c) 2024 Zachariah Michael Lagden (All Rights Reserved)
You may not use, copy, distribute, modify, or sell this code without the express permission of the author.

This cog is responsible for the role commands in the bot.
"""

# Python standard library
import logging
from typing import Union

# Third-party libraries
from discord.ext import commands
from fuzzywuzzy import process
import discord

# Helper functions
from helpers.colors import MAIN_EMBED_COLOR, ERROR_EMBED_COLOR

# Setup logger for this module
logger = logging.getLogger("rickbot")


class RoleCmdsCog(commands.Cog):
    """
    Commands cog for managing Discord roles.
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    @commands.guild_only()
    async def role(
        self,
        ctx: commands.Context,
        action: Union[str, discord.Role, None],
        member: Union[discord.Member, None] = None,
        role: Union[str, discord.Role, None] = None,
    ):
        """Handles the addition, removal, or information display of roles."""
        # Handle role information request
        if not member and not role:
            role = await self._resolve_role(ctx, action)
            if role:
                await self._send_role_info(ctx, role)
            return

        guild: discord.Guild = ctx.guild  # type: ignore
        author: discord.Member = ctx.guild.get_member(ctx.author.id)  # type: ignore

        # Resolve the role from a string name if necessary
        if isinstance(role, str):
            role = self._find_closest_role(guild.roles, role)
            if not role:
                await self._send_error(
                    ctx, "The role name you provided does not exist."
                )
                return

        # Check permissions before role modification
        if author.top_role <= role or guild.me.top_role <= role:
            await self._send_error(
                ctx, "You do not have permission to manage this role."
            )
            return

        if not guild.me.guild_permissions.manage_roles:
            await self._send_error(
                ctx, "I do not have permission to add or remove roles."
            )
            return

        # Modify role as requested
        await self._modify_role(ctx, member, role, action)

    async def _send_embed(self, ctx, title, description, color):
        """Helper to send formatted Discord embeds."""
        embed = discord.Embed(title=title, description=description, color=color)
        await ctx.reply(embed=embed, mention_author=False)

    async def _send_role_info(self, ctx, role):
        """Sends an embed with detailed information about a role."""
        embed = discord.Embed(
            title=f"Role Information: {role.name}", color=MAIN_EMBED_COLOR
        )
        role_info = [
            ("Role Name", role.name),
            ("Role ID", role.id),
            ("Role Color", str(role.color)),
            ("Role Permissions", str(role.permissions)),
            ("Role Position", role.position),
            ("Number of Members", len(role.members)),
        ]
        for name, value in role_info:
            embed.add_field(name=name, value=value, inline=False)
        await ctx.reply(embed=embed, mention_author=False)

    async def _modify_role(self, ctx, member, role, action):
        """Add or remove roles from a member based on the action specified."""
        if action.lower() in ["add", "remove"]:
            method = getattr(member, f"{action.lower()}_roles")
            await method(role)
            actioned = "added to" if action == "add" else "removed from"
            description = f"{role.name} has been {actioned} {member.mention}."
            await self._send_embed(
                ctx, f"Role {action.capitalize()}", description, MAIN_EMBED_COLOR
            )
        else:
            await self._send_error(ctx, "Invalid action. Use `add` or `remove`.")

    def _find_closest_role(self, roles, role_name):
        """Find the closest matching role by name."""
        names = {role.name: role for role in roles}
        best_match, _ = process.extractOne(role_name, names.keys())  # type: ignore
        return names.get(best_match)

    async def _send_error(self, ctx, message):
        """Send an error embed."""
        await self._send_embed(ctx, "Error", message, ERROR_EMBED_COLOR)

    async def _resolve_role(self, ctx, action):
        """Resolve role from action if it's a role or name."""
        if isinstance(action, discord.Role):
            return action
        if isinstance(action, str):
            return self._find_closest_role(ctx.guild.roles, action)
        await self._send_error(ctx, "The role specified could not be resolved.")
        return None


async def setup(bot: commands.Bot):
    """Setup the cog."""
    await bot.add_cog(RoleCmdsCog(bot))
