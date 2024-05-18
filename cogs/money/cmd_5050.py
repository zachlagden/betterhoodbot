"""
(c) 2024 Zachariah Michael Lagden (All Rights Reserved)
You may not use, copy, distribute, modify, or sell this code without the express permission of the author.

This cog is for the 5050 command, which allows users to gamble a specified amount of money with a 50% chance to double it.
"""

# Imports

# Python Standard Library
from discord.ext import commands
import discord
import logging
import random

# Helper functions
from helpers.colors import ERROR_EMBED_COLOR, SUCCESS_EMBED_COLOR
from helpers.errors import handle_error
from helpers.custom.money import (
    user_balance,
    format_money,
    log_money_transaction,
    DatabaseImpossibleError,
)

RICKLOG = logging.getLogger("rickbot")


class Money_5050Command(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="5050")
    async def _5050(self, ctx: commands.Context, amount: int):
        """
        Gamble a specified amount of money with a 50% chance to double it. Can only be used with money in the wallet.
        """
        # Ensure amount is positive
        if amount <= 0:
            embed = discord.Embed(
                title="Invalid Amount",
                description="Please enter a positive number.",
                color=ERROR_EMBED_COLOR,
            )
            embed.set_footer(text="Better Hood Money")

            await ctx.message.reply(embed=embed, mention_author=False)
            return

        query = user_balance(ctx.author.id)
        if query:
            wallet, _ = query
        else:
            raise DatabaseImpossibleError("User balance query failed.")

        if wallet < amount:
            embed = discord.Embed(
                title="Insufficient Funds",
                description="You do not have enough money in your wallet to gamble that amount.",
                color=ERROR_EMBED_COLOR,
            )
            embed.set_footer(text="Better Hood Money")

            await ctx.message.reply(embed=embed, mention_author=False)
            return

        # Calculate the result
        if random.choice([True, False]):
            adjust_amount = amount * 2
            adjust_wallet = adjust_amount
            result_text = f"You won {format_money(adjust_amount)}! It's been added to your wallet."
            color = SUCCESS_EMBED_COLOR

            await log_money_transaction(
                [
                    {
                        "users": {"from": self.bot.user, "to": ctx.author},
                        "movement": {"from": "bank", "to": "wallet"},
                        "amount": amount,
                        "reason": "Won 5050",
                    }
                ],
            )
        else:
            adjust_wallet = -amount
            result_text = f"You lost {format_money(amount)}. It has been taken from your wallet loser."
            color = ERROR_EMBED_COLOR

            await log_money_transaction(
                [
                    {
                        "users": {"from": ctx.author, "to": self.bot.user},
                        "movement": {"from": "wallet", "to": "bank"},
                        "amount": -amount,
                        "reason": "Lost 5050",
                    }
                ],
            )

        # Update balance
        user_balance(ctx.author.id, adjust_wallet=adjust_wallet)

        embed = discord.Embed(
            title="5050",
            description=result_text,
            color=color,
        )

        await ctx.message.reply(embed=embed, mention_author=False)

    @_5050.error
    async def _5050_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="Invalid Usage",
                description="You need to specify the amount of money you want to gamble.",
                color=ERROR_EMBED_COLOR,
            )
            embed.add_field(name="Usage", value=f"```{ctx.prefix}5050 <amount>```")
            embed.set_footer(text="Better Hood Money")

            await ctx.message.reply(embed=embed, mention_author=False)

        elif isinstance(error, commands.BadArgument):
            embed = discord.Embed(
                title="Invalid Amount",
                description="Please enter a valid number.",
                color=ERROR_EMBED_COLOR,
            )

            await ctx.message.reply(embed=embed, mention_author=False)

        else:
            await handle_error(ctx, error)


async def setup(bot: commands.Bot):
    await bot.add_cog(Money_5050Command(bot))
