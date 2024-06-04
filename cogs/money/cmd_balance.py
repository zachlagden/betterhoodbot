"""
(c) 2024 Zachariah Michael Lagden (All Rights Reserved)
You may not use, copy, distribute, modify, or sell this code without the express permission of the author.

This cog is for the balance command, which allows users to check their balance.
"""

# Python standard library
from typing import Union

# Third-party libraries
from discord.ext import commands
import discord

# Helper functions
from helpers.colors import MAIN_EMBED_COLOR, ERROR_EMBED_COLOR
from helpers.custom.format import format_money
from helpers.errors import handle_error
from helpers.logs import RICKLOG_CMDS

# Database
from helpers.db import money_collection


class Money_BalanceCommand(commands.Cog):
    """A cog for handling the balance command in a Discord bot."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="balance", aliases=["bal", "money"])
    async def _balance(
        self,
        ctx: commands.Context,
        member: Union[discord.Member, discord.User, None] = None,
    ):
        """
        Displays the balance of the specified user, or the calling user if none specified.
        """

        # Get the user's wallet balance
        query = money_collection.find_one(
            {"uid": ctx.author.id if member is None else member.id}
        )

        if not query:
            bank, wallet = 0, 0
        else:
            bank, wallet = query["bank"], query["wallet"]

        title = "Your balance:" if member is None else f"{member}'s balance:"
        embed = discord.Embed(title=title, color=MAIN_EMBED_COLOR)
        embed.set_author(
            name="💵Better Hood Balance💵",
            icon_url="https://cdn.discordapp.com/avatars/1230580580899491861/23e9c3bc9af61804ed90903fea9e0c52.webp?size=1024",
        )
        embed.add_field(name="💰Wallet", value=format_money(wallet), inline=False)
        embed.add_field(name="🏦Bank", value=format_money(bank), inline=False)
        embed.set_footer(text="Better Hood Money")
        await ctx.message.reply(embed=embed, mention_author=False)

    @_balance.error
    async def _balance_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.BadUnionArgument):
            embed = discord.Embed(
                title="Invalid Usage",
                description="Please enter a valid user.",
                color=ERROR_EMBED_COLOR,
            )

            embed.add_field("Usage", f"```{ctx.prefix}balance [@user]```", inline=False)
            embed.set_footer(text="Better Hood Money")

            await ctx.message.reply(embed=embed, mention_author=False)

        else:
            await handle_error(ctx, error)


async def setup(bot: commands.Bot):
    await bot.add_cog(Money_BalanceCommand(bot))
