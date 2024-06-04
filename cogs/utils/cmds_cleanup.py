"""
(c) 2024 Zachariah Michael Lagden (All Rights Reserved)
You may not use, copy, distribute, modify, or sell this code without the express permission of the author.

This cog allows server staff to clean up messages in the server.
"""

# Import the required modules

# Python standard library
import logging
import datetime
import asyncio

# Third-party libraries
from discord.ext import commands
import discord

# Helper functions
from helpers.colors import MAIN_EMBED_COLOR, ERROR_EMBED_COLOR
from helpers.errors import handle_error


class Utils_CleanupCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.list_of_common_prefixes = [
            "!",
            "?",
            ".",
            ",",
            "-",
            "!!",
            "??",
            "..",
            ",,",
            "--",
        ]

    @commands.command(name="botcleanup", aliases=["bcu"])
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.bot_has_guild_permissions(manage_messages=True, read_message_history=True)
    async def _bot_cleanup(self, ctx: commands.Context, limit: int = 100):
        await ctx.message.add_reaction("👌")

        # Fetch the messages
        try:
            query = ctx.channel.history(limit=limit)

        except discord.errors.Forbidden as error:
            embed = discord.Embed(
                title="Error",
                description="I do not have permission to fetch messages in this channel. Please make sure I have the `Read Message History` permission.",
                color=ERROR_EMBED_COLOR,
            )

            embed.add_field(name="Error", value=f"```{error}```", inline=False)

            await ctx.message.reply(embed=embed)
            return

        except discord.errors.HTTPException as error:
            embed = discord.Embed(
                title="Error",
                description="An error occurred while fetching messages. Please try again later. If the issue persists, contact the bot owner.",
                color=ERROR_EMBED_COLOR,
            )

            embed.add_field(name="Error", value=f"```{error}```", inline=False)

            await ctx.message.reply(embed=embed)
            return

        # Iterate through the messages
        to_bulk_delete = []
        to_delete_14_days_old = []

        async for message in query:
            if message == ctx.message:
                continue

            if message.author.bot or message.author == self.bot.user:
                to_bulk_delete.append(message)
            elif message.content.startswith(tuple(self.list_of_common_prefixes)):
                to_bulk_delete.append(message)
            elif message.content.startswith("```"):
                to_bulk_delete.append(message)
            elif message.content.startswith("/"):
                to_bulk_delete.append(message)

        # Check if message is older than 13 days
        for message in to_bulk_delete:
            if (datetime.datetime.now(datetime.UTC) - message.created_at).days >= 13:
                to_delete_14_days_old.append(message)

        # Remove messages older than 14 days from the bulk delete list
        to_bulk_delete = [
            msg for msg in to_bulk_delete if msg not in to_delete_14_days_old
        ]

        # Delete the messages
        try:
            if isinstance(ctx.channel, (discord.TextChannel, discord.Thread)):
                if len(to_bulk_delete) > 100:
                    for i in range(0, len(to_bulk_delete), 100):
                        await ctx.channel.delete_messages(to_bulk_delete[i : i + 100])
                else:
                    await ctx.channel.delete_messages(to_bulk_delete)
            else:
                embed = discord.Embed(
                    title="Error",
                    description="I cannot delete messages in this channel.",
                    color=ERROR_EMBED_COLOR,
                )
                await ctx.message.reply(embed=embed)
                return

        except discord.errors.Forbidden as error:
            embed = discord.Embed(
                title="Error",
                description="I do not have permission to delete messages in this channel. Please make sure I have the `Manage Messages` permission.",
                color=ERROR_EMBED_COLOR,
            )

            embed.add_field(name="Error", value=f"```{error}```", inline=False)

            await ctx.message.reply(embed=embed)
            return

        except discord.errors.HTTPException as error:
            embed = discord.Embed(
                title="Error",
                description="An error occurred while deleting messages. Please try again later. If the issue persists, contact the bot owner.",
                color=ERROR_EMBED_COLOR,
            )

            embed.add_field(name="Error", value=f"```{error}```", inline=False)

            await ctx.message.reply(embed=embed)
            return

        # Number of messages deleted
        number_of_messages_deleted = len(to_bulk_delete)

        has_deleted = False

        # If there are messages that are over 14 days old, we will delete them individually, but check with the user first
        if len(to_delete_14_days_old) > 0:
            # Ask the user if they want to delete the messages over 14 days old
            prompt_embed = discord.Embed(
                title="Bot Cleanup",
                description=(
                    f"Found {len(to_delete_14_days_old)} messages older than 14 days. "
                    "Do you want to delete them individually?"
                ),
                color=MAIN_EMBED_COLOR,
            )
            prompt_embed.set_footer(text="React with ✅ to confirm or ❌ to cancel.")
            prompt_message = await ctx.send(embed=prompt_embed)
            await prompt_message.add_reaction("✅")
            await prompt_message.add_reaction("❌")

            def check(reaction, user):
                return (
                    user == ctx.author
                    and str(reaction.emoji) in ["✅", "❌"]
                    and reaction.message.id == prompt_message.id
                )

            unable_to_delete = []

            try:
                bot: commands.Bot = self.bot
                reaction, _ = await bot.wait_for(
                    "reaction_add", timeout=60, check=check
                )

                await prompt_message.delete()

                if str(reaction.emoji) == "✅":
                    for message in to_delete_14_days_old:
                        message: discord.Message
                        try:
                            await message.delete()
                        except discord.errors.Forbidden as error:
                            unable_to_delete.append(message)
                        except discord.errors.HTTPException as error:
                            unable_to_delete.append(message)

                    # Send a message to the channel
                    embed = discord.Embed(
                        title="Bot Cleanup",
                        description=f"Success!\nMessages Fetched: `{limit}`\nMessages Bulk Deleted: `{number_of_messages_deleted}`\nMessages Older than 14 Days Deleted: `{len(to_delete_14_days_old) - len(unable_to_delete)}`\nMessages Unable to Delete: `{len(unable_to_delete)}`\nTotal Messages Deleted: `{number_of_messages_deleted + len(to_delete_14_days_old) - len(unable_to_delete)}`",
                        color=MAIN_EMBED_COLOR,
                    )
                    has_deleted = True

            except asyncio.TimeoutError:
                await prompt_message.delete()

        if not has_deleted:
            embed = discord.Embed(
                title="Bot Cleanup",
                description=f"Success!\nMessages Fetched: `{limit}`\nMessages Bulk Deleted: `{number_of_messages_deleted}`\nTotal Messages Deleted: `{number_of_messages_deleted}`",
                color=MAIN_EMBED_COLOR,
            )

        embed.set_footer(
            text=f"Cleanup Utility | {ctx.bot.user.name} | Deleting this message after 10s"
        )

        await ctx.send(embed=embed, delete_after=10)

    @_bot_cleanup.error
    async def _bot_cleanup_error(self, ctx: commands.Context, error):
        await handle_error(ctx, error)


async def setup(bot: commands.Bot):
    await bot.add_cog(Utils_CleanupCommands(bot))
