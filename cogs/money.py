"""
(c) 2024 Zachariah Michael Lagden (All Rights Reserved)
You may not use, copy, distribute, modify, or sell this code without the express permission of the author.

This cog is responsible for money commands in the bot.
"""

# Python standard library
from typing import Union
from datetime import datetime
import logging
import asyncio

# Third-party libraries
from discord.ext import commands
import discord

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

# Setup logger for this module
RICKLOG = logging.getLogger("rickbot")


class MoneyCog(commands.Cog):
    """A cog for handling money-related commands in a Discord bot."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="balance", aliases=["bal", "money"])
    async def _balance(
        self,
        ctx: commands.Context,
        member: Union[discord.Member, discord.User, None] = None,
    ):
        """Displays the balance of the specified user, or the calling user if none specified."""
        member = member or ctx.author
        query = user_balance(member.id)
        if not query:
            raise DatabaseImpossibleError(
                "The user's balance could not be retrieved from the database."
            )

        wallet, bank = query
        title = "Your balance:" if member == ctx.author else f"{member}'s balance:"
        embed = discord.Embed(title=title, color=MAIN_EMBED_COLOR)
        embed.set_author(
            name="💵Better Hood Balance💵",
            icon_url="https://cdn.discordapp.com/avatars/1230580580899491861/23e9c3bc9af61804ed90903fea9e0c52.webp?size=1024",
        )
        embed.add_field(name="💰Wallet", value=format_money(wallet), inline=False)
        embed.add_field(name="🏦Bank", value=format_money(bank), inline=False)
        embed.set_footer(text="Better Hood Money")
        await ctx.message.reply(embed=embed, mention_author=False)

    @commands.command(name="deposit", aliases=["dep"])
    async def _deposit(self, ctx: commands.Context, amount: int):
        """Deposits money from the wallet to the bank."""
        if amount < 1:
            embed = discord.Embed(
                title="Error",
                description="You cannot deposit less than $1.",
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

        wallet, _ = query
        if wallet < amount:
            embed = discord.Embed(
                title="Error",
                description="Insufficient funds in your wallet.",
                color=ERROR_EMBED_COLOR,
            )
            embed.set_footer(text="Better Hood Money")
            await ctx.message.reply(embed=embed, mention_author=False)
            return

        user_balance(ctx.author.id, adjust_bank=amount, adjust_wallet=-amount)
        await log_money_transaction(ctx.author.id, ctx.author.id, amount, "Deposit")
        embed = discord.Embed(
            title="Success",
            description=f"You have successfully deposited {format_money(amount)}.",
            color=SUCCESS_EMBED_COLOR,
        )
        embed.set_footer(text="Better Hood Money")
        await ctx.message.reply(embed=embed, mention_author=False)

    @_deposit.error
    async def _deposit_error(self, ctx: commands.Context, error):
        """Handles errors for the deposit command."""
        if isinstance(error, commands.MissingRequiredArgument):
            description = "Please specify an amount to deposit."
        elif isinstance(error, commands.BadArgument):
            description = "Invalid amount specified."
        else:
            description = str(error)
        embed = discord.Embed(
            title="Error", description=description, color=ERROR_EMBED_COLOR
        )
        embed.set_footer(text="Better Hood Money")
        await ctx.message.reply(embed=embed, mention_author=False)
        logging.exception("Error during deposit command", exc_info=error)

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
        """Handles errors for the withdraw command."""
        if isinstance(error, commands.MissingRequiredArgument):
            description = "Please specify an amount to withdraw."
        elif isinstance(error, commands.BadArgument):
            description = "Invalid amount specified."
        else:
            description = str(error)
        embed = discord.Embed(
            title="Error", description=description, color=ERROR_EMBED_COLOR
        )
        embed.set_footer(text="Better Hood Money")
        await ctx.message.reply(embed=embed, mention_author=False)
        logging.exception("Error during withdraw command", exc_info=error)

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

        query = user_balance(ctx.author.id)
        if not query:
            raise DatabaseImpossibleError(
                "The user's balance could not be retrieved from the database."
            )

        donor_wallet, _ = query
        if donor_wallet < amount:
            embed = discord.Embed(
                title="Error",
                description="Insufficient funds in your wallet.",
                color=ERROR_EMBED_COLOR,
            )
            embed.set_footer(text="Better Hood Money")
            await ctx.message.reply(embed=embed, mention_author=False)
            ctx.command.reset_cooldown(ctx)
            return

        user_balance(ctx.author.id, adjust_wallet=-amount)
        user_balance(member.id, adjust_wallet=amount)
        await log_money_transaction(ctx.author.id, member.id, amount, "Give")
        embed = discord.Embed(
            title="Success",
            description=f"You have successfully given {format_money(amount)} to {member.display_name}.",
            color=SUCCESS_EMBED_COLOR,
        )
        embed.set_footer(text="Better Hood Money")
        await ctx.message.reply(embed=embed, mention_author=False)

    @_give.error
    async def _give_error(self, ctx: commands.Context, error):
        """Handles errors for the give command."""
        if isinstance(error, commands.CommandOnCooldown):
            description = f"You've already given someone money recently. Try again in {format_time(int(error.retry_after))}."
        elif isinstance(error, commands.MissingRequiredArgument):
            if (
                "member" in ctx.command.clean_params
                and ctx.command.clean_params["member"].default
                == ctx.command.clean_params["member"]
            ):
                description = "Please mention the user you would like to give money to."
            elif (
                "amount" in ctx.command.clean_params
                and ctx.command.clean_params["amount"].default
                == ctx.command.clean_params["amount"]
            ):
                description = "Please enter the amount you would like to give."
            else:
                description = "Please enter valid command parameters."
        elif isinstance(error, commands.BadArgument):
            description = "Invalid argument provided."
        else:
            description = str(error)
        embed = discord.Embed(
            title="Error", description=description, color=ERROR_EMBED_COLOR
        )
        embed.set_footer(text="Better Hood Money")
        await ctx.message.reply(embed=embed, mention_author=False)
        ctx.command.reset_cooldown(ctx)
        logging.exception("Error during give command", exc_info=error)

    @commands.command(name="transfer", aliases=["send"])
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def _transfer(
        self, ctx: commands.Context, member: discord.Member, amount: int
    ):
        """Transfers money from one user's bank to another's bank, including a tax deduction."""
        if amount < 1000:
            embed = discord.Embed(
                title="Error",
                description="The minimum amount for transfer is $1000.",
                color=ERROR_EMBED_COLOR,
            )
            embed.set_footer(text="Better Hood Money")
            await ctx.message.reply(embed=embed, mention_author=False)
            ctx.command.reset_cooldown(ctx)
            return

        query = user_balance(ctx.author.id)
        if not query:
            raise DatabaseImpossibleError(
                "The user's balance could not be retrieved from the database."
            )

        _, sender_bank = query
        tax = int(amount * 0.10)
        net_amount = amount - tax
        if sender_bank < amount:
            embed = discord.Embed(
                title="Error",
                description="Insufficient funds in your bank.",
                color=ERROR_EMBED_COLOR,
            )
            embed.set_footer(text="Better Hood Money")
            await ctx.message.reply(embed=embed, mention_author=False)
            ctx.command.reset_cooldown(ctx)
            return

        embed = discord.Embed(
            title="Transfer Confirmation",
            description=f"Transferring {format_money(amount)} from {ctx.author.display_name} to {member.display_name}\nTax: {format_money(tax)} (10%)\nAmount after tax: {format_money(net_amount)}",
            color=MAIN_EMBED_COLOR,
        )
        embed.set_footer(text="React with ✅ to confirm or ❌ to cancel.")
        message = await ctx.message.reply(embed=embed, mention_author=False)
        await message.add_reaction("✅")
        await message.add_reaction("❌")

        def check(reaction, user):
            return (
                user == ctx.author
                and str(reaction.emoji) in ["✅", "❌"]
                and reaction.message.id == message.id
            )

        try:
            reaction, user = await self.bot.wait_for(
                "reaction_add", timeout=30.0, check=check
            )
            if str(reaction.emoji) == "✅":
                user_balance(ctx.author.id, adjust_bank=-amount)
                user_balance(member.id, adjust_bank=net_amount)
                await log_money_transaction(
                    ctx.author.id, member.id, net_amount, "Transfer"
                )
                confirmation_embed = discord.Embed(
                    title="Transfer Successful",
                    description=f"Successfully transferred {format_money(net_amount)} to {member.display_name} after a {format_money(tax)} tax deduction.",
                    color=SUCCESS_EMBED_COLOR,
                )
                confirmation_embed.set_footer(text="Better Hood Money")
                await message.edit(embed=confirmation_embed)
                await message.clear_reactions()
            elif str(reaction.emoji) == "❌":
                cancel_embed = discord.Embed(
                    title="Transfer Cancelled",
                    description="The transfer has been cancelled.",
                    color=ERROR_EMBED_COLOR,
                )
                cancel_embed.set_footer(text="Better Hood Money")
                await message.edit(embed=cancel_embed)
                await message.clear_reactions()
                ctx.command.reset_cooldown(ctx)
        except asyncio.TimeoutError:
            timeout_embed = discord.Embed(
                title="Transfer Timed Out",
                description="No reaction received in 30 seconds, the transfer has been automatically cancelled.",
                color=ERROR_EMBED_COLOR,
            )
            timeout_embed.set_footer(text="Better Hood Money")
            await message.edit(embed=timeout_embed)
            await message.clear_reactions()
            ctx.command.reset_cooldown(ctx)

    @_transfer.error
    async def _transfer_error(self, ctx: commands.Context, error):
        """Handles errors for the transfer command."""
        if isinstance(error, commands.CommandOnCooldown):
            description = f"You've already made a transfer recently. Try again in {format_time(int(error.retry_after))}."
        else:
            description = str(error)
        embed = discord.Embed(
            title="Error", description=description, color=ERROR_EMBED_COLOR
        )
        embed.set_footer(text="Better Hood Money")
        await ctx.message.reply(embed=embed, mention_author=False)
        ctx.command.reset_cooldown(ctx)
        logging.exception("Error during transfer command", exc_info=error)

    @commands.command(name="daily")
    @commands.cooldown(1, 86400, commands.BucketType.user)
    async def _daily(self, ctx: commands.Context):
        """Grants a daily monetary reward to the user."""
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


async def setup(bot: commands.Bot):
    await bot.add_cog(MoneyCog(bot))
