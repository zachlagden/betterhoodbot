"""
(c) 2024 Zachariah Michael Lagden (All Rights Reserved)
You may not use, copy, distribute, modify, or sell this code without the express permission of the author.

This cog is for the give command, which allows users to give money to another user.
"""

# Third-party libraries
from discord.ext import commands
import discord

# Helper functions
from helpers.colors import ERROR_EMBED_COLOR, SUCCESS_EMBED_COLOR
from helpers.errors import handle_error
from helpers.custom.money import (
    user_balance,
    format_money,
    format_time,
    log_money_transaction,
    DatabaseImpossibleError,
)


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
