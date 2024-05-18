"""
(c) 2024 Zachariah Michael Lagden (All Rights Reserved)
You may not use, copy, distribute, modify, or sell this code without the express permission of the author.

This cog is for the withdraw command, which allows users to withdraw money from their bank.
"""

# Python standard library
import logging

# Third-party libraries
from discord.ext import commands
import discord

# Helper functions
from helpers.colors import ERROR_EMBED_COLOR, SUCCESS_EMBED_COLOR
from helpers.errors import handle_error
from helpers.custom.money import (
    user_balance,
    format_money,
    log_money_transaction,
    DatabaseImpossibleError,
)


class Money_WithdrawCommand(commands.Cog):
    """A cog for handling the withdraw command in a Discord bot."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="withdraw", aliases=["with"])
    async def _withdraw(self, ctx: commands.Context, amount: int):
        """Withdraws money from the bank to the wallet."""
        if amount < 1:
            embed = discord.Embed(
                title="Error",
                description="You cannot withdraw less than $1.",
                color=ERROR_EMBED_COLOR,
            )
            embed.set_footer(text="Better Hood Money")
            await ctx.message.reply(embed=embed, mention_author=False)
            return

        query = user_balance(ctx.author.id)
        if not query:
            raise DatabaseImpossibleError(
                "The user's balance could not be retrieved from the database."
            )

        _, bank = query
        if bank < amount:
            embed = discord.Embed(
                title="Error",
                description="Insufficient funds in your bank.",
                color=ERROR_EMBED_COLOR,
            )
            embed.set_footer(text="Better Hood Money")
            await ctx.message.reply(embed=embed, mention_author=False)
            return

        user_balance(ctx.author.id, adjust_wallet=amount, adjust_bank=-amount)
        await log_money_transaction(ctx.author.id, ctx.author.id, amount, "Withdrawal")
        embed = discord.Embed(
            title="Success",
            description=f"You have successfully withdrawn {format_money(amount)}.",
            color=SUCCESS_EMBED_COLOR,
        )
        embed.set_footer(text="Better Hood Money")

        await ctx.message.reply(embed=embed, mention_author=False)

    @_withdraw.error
    async def _withdraw_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="Invalid Usage",
                description="Please specify an amount to withdraw.",
                color=ERROR_EMBED_COLOR,
            )
            embed.add_field(name="Usage", value=f"```{ctx.prefix}withdraw <amount>```")
            embed.set_footer(text="Better Hood Money")

            await ctx.message.reply(embed=embed, mention_author=False)

        elif isinstance(error, commands.BadArgument):
            embed = discord.Embed(
                title="Error",
                description="Invalid amount specified.",
                color=ERROR_EMBED_COLOR,
            )
            embed.set_footer(text="Better Hood Money")

            await ctx.message.reply(embed=embed, mention_author=False)

        else:
            await handle_error(ctx, error)


async def setup(bot: commands.Bot):
    await bot.add_cog(Money_WithdrawCommand(bot))
