"""
(c) 2024 Zachariah Michael Lagden (All Rights Reserved)
You may not use, copy, distribute, modify, or sell this code without the express permission of the author.

This cog is responsible for the role commands in the bot.
"""

# Python standard library
from typing import Optional

# Third-party libraries
from discord.ext import commands
from discord import app_commands
import discord

# Helper functions
from helpers.colors import MAIN_EMBED_COLOR, ERROR_EMBED_COLOR


class Utils_RoleSlashCommand(commands.Cog):
    """
    Commands cog for managing Discord roles.
    """

    def __init__(self, bot):
        self.bot = bot

    async def _send_embed(
        self, interaction, title, description, color, ephemeral=False
    ):
        """Helper to send formatted Discord embeds."""
        embed = discord.Embed(title=title, description=description, color=color)
        await interaction.response.send_message(embed=embed, ephemeral=ephemeral)

    async def _send_role_info(self, interaction, role):
        """Sends an embed with detailed information about a role."""
        embed = discord.Embed(
            title=f"Role Information: {role.name}", color=MAIN_EMBED_COLOR
        )
        role_info = [
            ("Role Name", role.name),
            ("Role ID", role.id),
            (
                "Role Color",
                (
                    str(role.color)
                    if str(role.color) != "#000000"
                    else "This role has no color."
                ),
            ),
            ("Role Permissions", str(role.permissions)),
            ("Role Position", role.position),
            ("Number of Members", len(role.members)),
            ("Role Created At", role.created_at.strftime("%Y-%m-%d %H:%M:%S")),
        ]
        for name, value in role_info:
            embed.add_field(name=name, value=value, inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=False)

    async def _modify_role(self, interaction, member, role, action):
        """Add or remove roles from a member based on the action specified."""
        if action.lower() in ["add", "remove"]:
            method = getattr(member, f"{action.lower()}_roles")
            await method(role)
            actioned = "added to" if action == "add" else "removed from"
            description = f"{role.name} has been {actioned} {member.mention}."
            await self._send_embed(
                interaction,
                f"Role {action.capitalize()}",
                description,
                MAIN_EMBED_COLOR,
                ephemeral=False,
            )
        else:
            await self._send_embed(
                interaction,
                "Error",
                "Invalid action. Use `add` or `remove`.",
                ERROR_EMBED_COLOR,
                ephemeral=True,
            )

    @app_commands.command(
        name="role",
        description="Handles the addition, removal, or information display of roles.",
    )
    @app_commands.describe(
        action="The action to perform (add, remove, info).",
        member="The member to modify.",
        role="The role to add, remove, or get info on.",
    )
    @app_commands.choices(
        action=[
            app_commands.Choice(name="Add", value="add"),
            app_commands.Choice(name="Remove", value="remove"),
            app_commands.Choice(name="Info", value="info"),
        ]
    )
    async def _role(
        self,
        interaction: discord.Interaction,
        action: str,
        member: Optional[discord.Member] = None,
        role: Optional[discord.Role] = None,
    ):
        guild = interaction.guild
        author = interaction.user

        # Handle role information request
        if action == "info":
            if role:
                await self._send_role_info(interaction, role)
            else:
                await self._send_embed(
                    interaction,
                    "Error",
                    "The role must be specified for info action.",
                    ERROR_EMBED_COLOR,
                    ephemeral=True,
                )
            return

        if not member or not role:
            await self._send_embed(
                interaction,
                "Error",
                "Both member and role must be specified for add or remove actions.",
                ERROR_EMBED_COLOR,
                ephemeral=True,
            )
            return

        # Check permissions before role modification
        if author.top_role <= role or guild.me.top_role <= role:
            await self._send_embed(
                interaction,
                "Error",
                "You do not have permission to manage this role.",
                ERROR_EMBED_COLOR,
                ephemeral=True,
            )
            return

        if not guild.me.guild_permissions.manage_roles:
            await self._send_embed(
                interaction,
                "Error",
                "I do not have permission to add or remove roles.",
                ERROR_EMBED_COLOR,
                ephemeral=True,
            )
            return

        # Modify role as requested
        await self._modify_role(interaction, member, role, action)


async def setup(bot: commands.Bot):
    """Setup the cog."""
    await bot.add_cog(Utils_RoleSlashCommand(bot))
