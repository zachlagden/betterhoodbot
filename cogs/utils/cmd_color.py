"""
(c) 2024 Zachariah Michael Lagden (All Rights Reserved)
You may not use, copy, distribute, modify, or sell this code without the express permission of the author.

This cog allows the user to change their color role.
The available colors are purple, blue, green, hot pink, orange, red, yellow, and black.
"""

# Third-party libraries
from discord.ext import commands
import discord

# Helper functions
from helpers.colors import MAIN_EMBED_COLOR, ERROR_EMBED_COLOR
from helpers.errors import handle_error

# Config
from config import CUSTOM_CONFIG


class Utils_ColorCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.color_role_ids = CUSTOM_CONFIG["color_cmd"]["colors"]

    def format_color(self, color):
        return f"`{color}` - <@&{self.color_role_ids[color]}>"

    @commands.command(aliases=["colour"])
    async def color(self, ctx: commands.Context, *, color: str):
        if color.lower() not in self.color_role_ids:
            embed = discord.Embed(
                title="Error",
                description="The color you provided is not valid. Please choose from the following options.",
                color=ERROR_EMBED_COLOR,
            )

            color_options = ""
            for color in self.color_role_ids:
                color_options += f"{self.format_color(color)}\n"

            embed.add_field(name="Color Options", value=color_options)

            await ctx.reply(embed=embed, mention_author=False)
            return

        role = ctx.guild.get_role(self.color_role_ids[color.lower()])

        if role in ctx.author.roles:
            embed = discord.Embed(
                title="Error",
                description="You have already selected this color.",
                color=ERROR_EMBED_COLOR,
            )
            return ctx.reply(embed=embed, mention_author=False)

        # Check if the user has a color role already
        for crole in ctx.author.roles:
            if crole.id in self.color_role_ids.values():
                await ctx.author.remove_roles(
                    crole, reason="User requested color change."
                )

        await ctx.author.add_roles(role, reason="User requested color change.")

        embed = discord.Embed(
            title="Success",
            description=f"Your color has been changed to <@&{role.id}>.",
            color=MAIN_EMBED_COLOR,
        )

        await ctx.reply(embed=embed, mention_author=False)

    @color.error
    async def color_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="Invalid Usage",
                description="Please specify a color.",
                color=ERROR_EMBED_COLOR,
            )

            embed.add_field(name="Usage", value=f"```{ctx.prefix}color <color>```")
            embed.set_footer(text="Color Command")

            await ctx.reply(embed=embed, mention_author=False)

        elif isinstance(error, commands.BadArgument):
            embed = discord.Embed(
                title="Error",
                description="Invalid color specified.",
                color=ERROR_EMBED_COLOR,
            )
            embed.set_footer(text="Color Command")

            await ctx.reply(embed=embed, mention_author=False)

        else:
            await handle_error(ctx, error)


async def setup(bot: commands.Bot):
    await bot.add_cog(Utils_ColorCommand(bot))
