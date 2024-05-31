"""
(c) 2024 Zachariah Michael Lagden (All Rights Reserved)
You may not use, copy, distribute, modify, or sell this code without the express permission of the author.

This cog is for the give command, which allows users to give money to another user.
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


class Money_GiveCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="give", aliases=["pay"])
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def _give(self, ctx: commands.Context, member: discord.Member, amount: int):
        """Allows a user to give money to another user. The give command is wallet to wallet."""
        if amount < 1 or amount > 1000:
            embed = discord.Embed(
                title="Error",
                description="You can only give an amount between $1 and $1000.",
                color=ERROR_EMBED_COLOR,
            )
            embed.set_footer(text="Better Hood Money")
            await ctx.message.reply(embed=embed, mention_author=False)
            ctx.command.reset_cooldown(ctx)
            return

        query = money_collection.find_one({"uid": ctx.author.id})
        user = query if query else {}

        if user.get("wallet", 0) < amount:
            embed = discord.Embed(
                title="Error",
                description="You do not have enough money in your wallet to give that amount.",
                color=ERROR_EMBED_COLOR,
            )
            embed.set_footer(text="Better Hood Money")
            await ctx.message.reply(embed=embed, mention_author=False)
            ctx.command.reset_cooldown(ctx)
            return

        query = money_collection.find_one({"uid": member.id})
        recieveing_user = query if query else {}

        money_collection.update_one(
            {"uid": ctx.author.id},
            {"$inc": {"wallet": -amount}},
        )

        money_collection.update_one(
            {"uid": member.id},
            {"$inc": {"wallet": amount}},
            upsert=True,
        )

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

                webhook_embed = discord.Embed(
                    title="Wallet Transaction",
                    description=f"{ctx.author.mention} has given {member.mention} {format_money(amount)}.",
                    color=ERROR_EMBED_COLOR,
                )

                webhook_embed.add_field(
                    name="Sender's Original Wallet",
                    value=format_money(user.get("wallet", 0)),
                )

                webhook_embed.add_field(
                    name="Sender's New Wallet",
                    value=format_money(user.get("wallet", 0) - amount),
                )

                webhook_embed.add_field(
                    name="Reciever's Original Wallet",
                    value=format_money(recieveing_user.get("wallet", 0)),
                )

                webhook_embed.add_field(
                    name="Reciever's New Wallet",
                    value=format_money(recieveing_user.get("wallet", 0) + amount),
                )

                webhook_embed.set_footer(text="Better Hood Money")

                await webhook.send(
                    username="Better Hood Money Transactions",
                    avatar_url=self.bot.user.avatar.url,
                    embed=webhook_embed,
                )

        embed = discord.Embed(
            title="Success",
            description=f"You have successfully given {format_money(amount)} to {member.display_name}.",
            color=SUCCESS_EMBED_COLOR,
        )
        embed.set_footer(text="Better Hood Money")
        await ctx.message.reply(embed=embed, mention_author=False)

    @_give.error
    async def _give_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(
                title="Error",
                description=f"You've already given money recently. Try again in {format_time(int(error.retry_after))}.",
                color=ERROR_EMBED_COLOR,
            )
            embed.set_footer(text="Better Hood Money")
            await ctx.message.reply(embed=embed, mention_author=False)

        elif isinstance(error, commands.MissingRequiredArgument):
            # Because the error is raised, we can clear the user's cooldown
            ctx.command.reset_cooldown(ctx)

            embed = discord.Embed(
                title="Invalid Usage",
                description="Please specify a user and an amount to give.",
                color=ERROR_EMBED_COLOR,
            )
            embed.add_field(
                name="Usage", value=f"```{ctx.prefix}give <@user> <amount>```"
            )
            embed.set_footer(text="Better Hood Money")
            await ctx.message.reply(embed=embed, mention_author=False)

        elif isinstance(error, commands.BadArgument):
            # Because the error is raised, we can clear the user's cooldown
            ctx.command.reset_cooldown(ctx)

            embed = discord.Embed(
                title="Error",
                description="Invalid user or amount specified.",
                color=ERROR_EMBED_COLOR,
            )
            embed.set_footer(text="Better Hood Money")
            await ctx.message.reply(embed=embed, mention_author=False)

        else:
            # Because the error is raised, we can clear the user's cooldown
            ctx.command.reset_cooldown(ctx)

            await handle_error(ctx, error)


async def setup(bot: commands.Bot):
    await bot.add_cog(Money_GiveCommand(bot))
