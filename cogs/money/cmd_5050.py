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

# Third-Party Libraries
import aiohttp

# Helper functions
from helpers.colors import ERROR_EMBED_COLOR, SUCCESS_EMBED_COLOR
from helpers.custom.errors import DatabaseImpossibleError
from helpers.custom.format import format_money
from helpers.errors import handle_error
from helpers.logs import RICKLOG_CMDS

# Database
from helpers.db import money_collection

# Config
from helpers.config import CUSTOM_CONFIG

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

        # Get the user's wallet balance
        query = money_collection.find_one({"uid": ctx.author.id})

        if not query:
            wallet, original_wallet = 0, 0
        else:
            wallet, original_wallet = query["wallet"], query["wallet"]

        # Ensure the user has enough money in their wallet
        if amount > wallet:
            embed = discord.Embed(
                title="Insufficient Funds",
                description="You do not have enough money in your wallet.",
                color=ERROR_EMBED_COLOR,
            )
            embed.set_footer(text="Better Hood Money")

            await ctx.message.reply(embed=embed, mention_author=False)
            return

        # Bet is okay so take the money from the wallet
        wallet -= amount

        # Randomly determine if the user wins
        win = random.choice([True, False])

        if win:
            amount *= 2
            wallet += amount

            embed = discord.Embed(
                title="You Won!",
                description=f"You won {format_money(amount)}!",
                color=SUCCESS_EMBED_COLOR,
            )

        else:
            embed = discord.Embed(
                title="You Lost",
                description=f"You lost {format_money(amount)}.",
                color=ERROR_EMBED_COLOR,
            )

        embed.set_footer(text="Better Hood Money")

        # Update the user's wallet
        money_collection.update_one(
            {"uid": ctx.author.id},
            {"$set": {"wallet": wallet}},
        )

        # Log this transaction

        try:
            webhook_url = CUSTOM_CONFIG["logging"]["transactions"]["webhook"]
        except KeyError:
            RICKLOG.critical(
                "No webhook URL found for transaction logging. Not logging this transaction."
            )
        else:
            async with aiohttp.ClientSession() as session:
                webhook: discord.Webhook = discord.Webhook.from_url(
                    webhook_url, session=session
                )

                if win:
                    webhook_embed = discord.Embed(
                        title="5050 Win",
                        description=f"{ctx.author.mention} won {format_money(amount)}",
                        color=SUCCESS_EMBED_COLOR,
                    )

                    webhook_embed.add_field(
                        name="Original Wallet", value=format_money(original_wallet)
                    )
                    webhook_embed.add_field(
                        name="New Wallet", value=format_money(wallet)
                    )
                    webhook_embed.add_field(
                        name="Amount Won", value=format_money(amount)
                    )
                else:
                    webhook_embed = discord.Embed(
                        title="5050 Loss",
                        description=f"{ctx.author.mention} lost {format_money(amount)}",
                        color=ERROR_EMBED_COLOR,
                    )

                    webhook_embed.add_field(
                        name="Original Wallet", value=format_money(original_wallet)
                    )
                    webhook_embed.add_field(
                        name="New Wallet", value=format_money(wallet)
                    )
                    webhook_embed.add_field(
                        name="Amount Lost", value=format_money(amount)
                    )

                    webhook_embed.set_footer(text="Better Hood Money")

                await webhook.send(
                    username="Better Hood Money Transactions",
                    avatar_url=self.bot.user.avatar.url,
                    embed=webhook_embed,
                )

        await ctx.message.reply(embed=embed, mention_author=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(Money_5050Command(bot))
