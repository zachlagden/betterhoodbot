"""
(c) 2024 Zachariah Michael Lagden (All Rights Reserved)
You may not use, copy, distribute, modify, or sell this code without the express permission of the author.

This cog is for the daily command, which grants a daily reward to users.
"""

# Python standard library
from datetime import datetime

# Third-party libraries
from discord.ext import commands
import discord

# Import database
from db import money_collection

# Helper functions
from helpers.colors import ERROR_EMBED_COLOR, SUCCESS_EMBED_COLOR
from helpers.custom.money import user_balance, log_money_transaction
from helpers.errors import handle_error


class Money_DailyCommand(commands.Cog):
    """A cog for handling the daily reward command in a Discord bot."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="daily")
    @commands.cooldown(1, 86400, commands.BucketType.user)
    async def _daily(self, ctx: commands.Context):
        """Grants a daily monetary reward to the user."""
        # TODO: pretty sure the cooldown (DB) is not working

        lookup = money_collection.find_one({"_id": ctx.author.id})
        user = lookup if lookup else {}

        if "last_daily" in user:
            if (datetime.now() - user["last_daily"]).total_seconds() < 86400:
                embed = discord.Embed(
                    title="Error",
                    description="You have already claimed your daily reward today. Try again tomorrow.",
                    color=ERROR_EMBED_COLOR,
                )
                embed.set_footer(text="Better Hood Money")
                await ctx.message.reply(embed=embed, mention_author=False)
                return
            else:
                money_collection.update_one(
                    {"_id": ctx.author.id}, {"$unset": {"last_daily": ""}}
                )
        else:
            money_collection.update_one(
                {"_id": ctx.author.id}, {"$set": {"last_daily": datetime.now()}}
            )

        user_balance(ctx.author.id, adjust_bank=10000)
        await log_money_transaction(
            self.bot.user.id, ctx.author.id, 10000, "Daily Reward"
        )
        embed = discord.Embed(
            title="Daily Reward",
            description="You have successfully claimed your daily reward of $10000. It is available in your bank.",
            color=SUCCESS_EMBED_COLOR,
        )
        embed.set_footer(text="Better Hood Money")
        await ctx.message.reply(embed=embed, mention_author=False)

    @_daily.error
    async def _daily_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(
                title="Error",
                description="You have already claimed your daily reward today. Try again tomorrow.",
                color=ERROR_EMBED_COLOR,
            )
            embed.set_footer(text="Better Hood Money")
            await ctx.message.reply(embed=embed, mention_author=False)

        else:
            ctx.command.reset_cooldown(ctx)

            await handle_error(ctx, error)


async def setup(bot: commands.Bot):
    await bot.add_cog(Money_DailyCommand(bot))
