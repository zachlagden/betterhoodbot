"""
(c) 2024 Zachariah Michael Lagden (All Rights Reserved)
You may not use, copy, distribute, modify, or sell this code without the express permission of the author.

This cog counts the number of times a user has said the n-word in the server and provides a command to check the records,
as well as a leaderboard command that shows the top 10 users with the most n-word records.
"""

# Python standard library
import logging

# Third-party libraries
from discord.ext import commands
import discord

# Helper functions
from helpers.colors import MAIN_EMBED_COLOR, ERROR_EMBED_COLOR
from helpers.logs import RICKLOG, RICKLOG_CMDS


class ColorChangingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.color_role_ids = {
            "purple": 1215222975553474576,
            "blue": 1215222975553474577,
            "green": 1215222975553474578,
            "hot pink": 1215222975553474575,
            "orange": 1215222975553474573,
            "red": 1215222975553474572,
            "yellow": 1215222975553474574,
            "black": 1230536800083120188,
        }

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
        print(error)


async def setup(bot: commands.Bot):
    await bot.add_cog(ColorChangingCog(bot))
