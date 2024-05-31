"""
(c) 2024 Zachariah Michael Lagden (All Rights Reserved)
You may not use, copy, distribute, modify, or sell this code without the express permission of the author.

This cog is for the daily command, which grants a daily reward to users.
"""

# Python standard library
import datetime

# Third-party libraries
from discord_timestamps import format_timestamp, TimestampType
from discord.ext import commands
import aiohttp
import discord

# Import database
from db import money_collection

# Helper functions
from helpers.colors import ERROR_EMBED_COLOR, SUCCESS_EMBED_COLOR
from helpers.custom.format import format_money
from helpers.logs import RICKLOG

# Config
from config import CUSTOM_CONFIG


class Money_DailyCommand(commands.Cog):
    """A cog for handling the daily reward command in a Discord bot."""

    def __init__(self, bot):
        self.bot = bot

        self.daily_reward_amount = 10000
        self.daily_reward_cooldown = 86400

    @commands.command(name="daily")
    async def _daily(self, ctx: commands.Context):
        """Grants a daily monetary reward to the user."""

        query = money_collection.find_one({"uid": ctx.author.id})
        user = query if query else {}

        if "data" in user and "last_daily" in user["data"]:
            if (
                datetime.datetime.now() - user["data"]["last_daily"]
            ).total_seconds() < self.daily_reward_cooldown:
                expires = user["data"]["last_daily"] + datetime.timedelta(
                    seconds=self.daily_reward_cooldown
                )
                timestamp = format_timestamp(expires, TimestampType.RELATIVE)

                embed = discord.Embed(
                    title="Error",
                    description=f"You have already claimed your daily reward today. Try again {timestamp}.",
                    color=ERROR_EMBED_COLOR,
                )
                embed.set_footer(text="Better Hood Money")
                await ctx.message.reply(embed=embed, mention_author=False)
                return
        else:
            money_collection.update_one(
                {"uid": ctx.author.id},
                {"$set": {"data": {"last_daily": datetime.datetime.now()}}},
            )

        # Add money to user's bank
        money_collection.update_one(
            {"uid": ctx.author.id},
            {"$inc": {"bank": self.daily_reward_amount, "wallet": 0}},
            upsert=True,
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
                    title="Daily Reward",
                    description=f"{ctx.author.mention} has been rewarded {format_money(self.daily_reward_amount)}",
                    color=ERROR_EMBED_COLOR,
                )

                webhook_embed.add_field(
                    name="Original Wallet", value=format_money(user.get("wallet", 0))
                )
                webhook_embed.add_field(
                    name="New Wallet",
                    value=format_money(
                        user.get("wallet", 0) + self.daily_reward_amount
                    ),
                )

                webhook_embed.set_footer(text="Better Hood Money")

                await webhook.send(
                    username="Better Hood Money Transactions",
                    avatar_url=self.bot.user.avatar.url,
                    embed=webhook_embed,
                )

        embed = discord.Embed(
            title="Daily Reward",
            description=f"You have successfully claimed your daily reward of {format_money(self.daily_reward_amount)}. It is available in your bank.",
            color=SUCCESS_EMBED_COLOR,
        )

        embed.set_footer(text="Better Hood Money")

        await ctx.message.reply(embed=embed, mention_author=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(Money_DailyCommand(bot))
