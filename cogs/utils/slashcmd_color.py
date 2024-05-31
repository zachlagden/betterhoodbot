"""
(c) 2024 Zachariah Michael Lagden (All Rights Reserved)
You may not use, copy, distribute, modify, or sell this code without the express permission of the author.

This cog allows the user to change their color role.
The available colors are purple, blue, green, hot pink, orange, red, yellow, and black.
"""

# Third-party libraries
from discord.ext import commands
from discord import app_commands
import discord

# Helper functions
from helpers.colors import MAIN_EMBED_COLOR, ERROR_EMBED_COLOR
from helpers.errors import handle_error

# Config
from config import CUSTOM_CONFIG


class Utils_ColorSlashCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.color_role_ids = CUSTOM_CONFIG["color_cmd"]["colors"]

    def format_color(self, color):
        return f"`{color}` - <@&{self.color_role_ids[color]}>"

    @app_commands.command(name="color", description="Change your color role.")
    @app_commands.describe(color="The color you want to change to.")
    @app_commands.choices(
        color=[
            app_commands.Choice(name=color.capitalize(), value=color)
            for color in CUSTOM_CONFIG["color_cmd"]["colors"]
        ]
    )
    async def _color(self, interaction: discord.Interaction, color: str):
        if color.lower() not in self.color_role_ids:
            embed = discord.Embed(
                title="Invalid Usage",
                description="The color you provided is not valid. Please choose from the following options.",
                color=ERROR_EMBED_COLOR,
            )

            color_options = "\n".join(self.format_color(c) for c in self.color_role_ids)
            embed.add_field(name="Color Options", value=color_options)

            return await interaction.response.send_message(embed=embed, ephemeral=True)

        await interaction.response.defer()

        role = interaction.guild.get_role(self.color_role_ids[color.lower()])

        if role in interaction.user.roles:
            embed = discord.Embed(
                title="Error",
                description="You have already selected this color.",
                color=ERROR_EMBED_COLOR,
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)

        # Remove any existing color roles
        roles_to_remove = [
            r for r in interaction.user.roles if r.id in self.color_role_ids.values()
        ]
        await interaction.user.remove_roles(
            *roles_to_remove, reason="User requested color change."
        )

        await interaction.user.add_roles(role, reason="User requested color change.")

        embed = discord.Embed(
            title="Success",
            description=f"Your color has been changed to <@&{role.id}>.",
            color=MAIN_EMBED_COLOR,
        )

        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Utils_ColorSlashCommand(bot))
