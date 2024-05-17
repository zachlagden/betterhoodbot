"""
(c) 2024 Zachariah Michael Lagden (All Rights Reserved)
You may not use, copy, distribute, modify, or sell this code without the express permission of the author.

This cog is responsible for the gambling commands in the bot.
"""

# Imports

# Python Standard Library
from discord.ext import commands
from typing import Union
import discord
import logging
import random

# Import database
from db import money_collection

# Helper functions
from helpers.colors import MAIN_EMBED_COLOR, ERROR_EMBED_COLOR, SUCCESS_EMBED_COLOR
from helpers.errors import handle_error
from helpers.money import (
    user_balance,
    format_money,
    format_time,
    log_money_transaction,
    DatabaseImpossibleError,
)

RICKLOG = logging.getLogger("rickbot")


class MoneyGamblingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def create_embed(self, title: str, description: str, color: int) -> discord.Embed:
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_footer(text="Better Hood Money")
        return embed

    @commands.command(name="5050")
    async def _5050(self, ctx: commands.Context, amount: int):
        """
        Gamble a specified amount of money with a 50% chance to double it. Can only be used with money in the wallet.
        """
        # Ensure amount is positive
        if amount <= 0:
            embed = self.create_embed(
                "Invalid Amount", "Please enter a positive amount.", ERROR_EMBED_COLOR
            )
            return await ctx.send(embed=embed)

        query = user_balance(ctx.author.id)
        if query:
            wallet, _ = query
        else:
            raise DatabaseImpossibleError("User balance query failed.")

        if wallet < amount:
            embed = self.create_embed(
                "Insufficient Funds",
                f"You do not have enough money to gamble ${amount:,}.",
                ERROR_EMBED_COLOR,
            )
            return await ctx.send(embed=embed)

        # Calculate the result
        if random.choice([True, False]):  # Simplified random result calculation
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

        embed = self.create_embed("Game Result", result_text, color)
        await ctx.send(embed=embed)

    @_5050.error
    async def _5050_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.MissingRequiredArgument):
            embed = self.create_embed(
                "Missing Argument",
                "Please enter the amount you would like to gamble.",
                ERROR_EMBED_COLOR,
            )
            await ctx.send(embed=embed)
        elif isinstance(error, commands.BadArgument):
            embed = self.create_embed(
                "Invalid Argument",
                "Please enter a valid number.",
                ERROR_EMBED_COLOR,
            )
            await ctx.send(embed=embed)
        else:
            await handle_error(ctx, error)


async def setup(bot: commands.Bot):
    await bot.add_cog(MoneyGamblingCog(bot))
