"""
(c) 2024 Zachariah Michael Lagden (All Rights Reserved)
You may not use, copy, distribute, modify, or sell this code without the express permission of the author.

This cog is for the transfer command, which allows users to transfer money to another user's bank.
"""

# Python Standard library
import asyncio

# Third-party libraries
from discord.ext import commands
import aiohttp
import discord

# Helper functions
from helpers.colors import ERROR_EMBED_COLOR, SUCCESS_EMBED_COLOR, MAIN_EMBED_COLOR
from helpers.custom.format import format_money, format_time
from helpers.errors import handle_error
from helpers.logs import RICKLOG

# Database
from db import money_collection

# Config
from config import CUSTOM_CONFIG


class Money_TransferCommand(commands.Cog):
    """A cog for handling the transfer command in a Discord bot."""

    def __init__(self, bot):
        self.bot = bot

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

        query = money_collection.find_one({"uid": ctx.author.id})
        user = query if query else {}

        query = money_collection.find_one({"uid": member.id})
        recieving_user = query if query else {}

        if user.get("bank", 0) < amount:
            embed = discord.Embed(
                title="Error",
                description="You do not have enough money in your bank to transfer that amount.",
                color=ERROR_EMBED_COLOR,
            )
            embed.set_footer(text="Better Hood Money")
            await ctx.message.reply(embed=embed, mention_author=False)
            ctx.command.reset_cooldown(ctx)
            return

        tax = amount * 0.1
        net_amount = amount - tax

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
                money_collection.update_one(
                    {"uid": ctx.author.id},
                    {"$inc": {"bank": -amount}},
                )

                money_collection.update_one(
                    {"uid": member.id},
                    {"$inc": {"bank": net_amount}},
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
                            title="Bank Transfer",
                            description=f"{ctx.author.mention} has transferred {format_money(amount)} to {member.mention}.",
                            color=ERROR_EMBED_COLOR,
                        )

                        webhook_embed.add_field(
                            name="Sender's Original Bank",
                            value=format_money(user.get("bank", 0)),
                        )

                        webhook_embed.add_field(
                            name="Sender's New Bank",
                            value=format_money(user.get("bank", 0) - amount),
                        )

                        webhook_embed.add_field(
                            name="Recipient's Original Bank",
                            value=format_money(recieving_user.get("bank", 0)),
                        )

                        webhook_embed.add_field(
                            name="Recipient's New Bank",
                            value=format_money(
                                recieving_user.get("bank", 0) + net_amount
                            ),
                        )

                        webhook_embed.set_footer(text="Better Hood Money")

                        await webhook.send(
                            username="Better Hood Money Transactions",
                            avatar_url=self.bot.user.avatar.url,
                            embed=webhook_embed,
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
        if isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(
                title="Error",
                description=f"You've already transferred money recently. Try again in {format_time(int(error.retry_after))}.",
                color=ERROR_EMBED_COLOR,
            )
            embed.set_footer(text="Better Hood Money")
            await ctx.message.reply(embed=embed, mention_author=False)

        elif isinstance(error, commands.MissingRequiredArgument):
            # Because the error is raised, we can clear the user's cooldown
            ctx.command.reset_cooldown(ctx)

            embed = discord.Embed(
                title="Invalid Usage",
                description="Please specify a user and an amount to transfer.",
                color=ERROR_EMBED_COLOR,
            )
            embed.add_field(
                name="Usage", value=f"```{ctx.prefix}transfer <@user> <amount>```"
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
    await bot.add_cog(Money_TransferCommand(bot))
