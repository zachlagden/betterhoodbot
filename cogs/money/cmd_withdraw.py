"""
(c) 2024 Zachariah Michael Lagden (All Rights Reserved)
You may not use, copy, distribute, modify, or sell this code without the express permission of the author.

This cog is for the withdraw command, which allows users to withdraw money from their bank.
"""

# Third-party libraries
from discord.ext import commands
import aiohttp
import discord

# Helper functions
from helpers.colors import ERROR_EMBED_COLOR, SUCCESS_EMBED_COLOR
from helpers.custom.format import format_money, format_time
from helpers.errors import handle_error
from helpers.logs import RICKLOG

# Database
from db import money_collection

# Config
from config import CUSTOM_CONFIG


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

        query = money_collection.find_one({"uid": ctx.author.id})
        user = query if query else {}

        if user.get("bank", 0) < amount:
            embed = discord.Embed(
                title="Error",
                description="You do not have enough money in your bank to withdraw that amount.",
                color=ERROR_EMBED_COLOR,
            )
            embed.set_footer(text="Better Hood Money")
            await ctx.message.reply(embed=embed, mention_author=False)
            return

        money_collection.update_one(
            {"uid": ctx.author.id},
            {"$inc": {"wallet": amount, "bank": -amount}},
        )

        try:
            webhook_url = CUSTOM_CONFIG["logging"]["transactions"]["webhook"]
        except KeyError:
            RICKLOG.critical(
                "No webhook URL found for transaction logging. Not logging this transaction."
            )
        else:
            with aiohttp.ClientSession() as session:
                webhook: discord.Webhook = discord.Webhook.from_url(
                    webhook_url, session=session
                )

                webhook_embed = discord.Embed(
                    title="Withdrawal",
                    description=f"{ctx.author.mention} has withdrawn {format_money(amount)} from their bank.",
                    color=ERROR_EMBED_COLOR,
                )

                webhook_embed.add_field(
                    name="Original Bank",
                    value=format_money(user.get("bank", 0)),
                )

                webhook_embed.add_field(
                    name="New Bank",
                    value=format_money(user.get("bank", 0) - amount),
                )

                webhook_embed.set_footer(text="Better Hood Money")

                await webhook.send(
                    username="Better Hood Money Transactions",
                    avatar_url=self.bot.user.avatar.url,
                    embed=webhook_embed,
                )

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
