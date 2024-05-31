"""
(c) 2024 Zachariah Michael Lagden (All Rights Reserved)
You may not use, copy, distribute, modify, or sell this code without the express permission of the author.

This cog allows server staff to clean up messages in the server.
"""

# Import the required modules

# Python standard library
import datetime
import asyncio

# Third-party libraries
from discord.ext import commands
from discord import app_commands
from discord import ui
import discord

# Helper functions
from helpers.colors import MAIN_EMBED_COLOR, ERROR_EMBED_COLOR
from helpers.errors import handle_error


class Utils_CleanupSlashCommands(commands.Cog):
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

    @app_commands.command(
        name="botcleanup", description="Cleans up bot messages in the channel."
    )
    @app_commands.describe(limit="The number of messages to check.")
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    async def _bot_cleanup(self, interaction: discord.Interaction, limit: int = 100):
        await interaction.response.defer()

        # Fetch the messages
        try:
            query = interaction.channel.history(limit=limit)

        except discord.errors.Forbidden as error:
            embed = discord.Embed(
                title="Error",
                description="I do not have permission to fetch messages in this channel. Please make sure I have the `Read Message History` permission.",
                color=ERROR_EMBED_COLOR,
            )

            embed.add_field(name="Error", value=f"```{error}```", inline=False)

            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        except discord.errors.HTTPException as error:
            embed = discord.Embed(
                title="Error",
                description="An error occurred while fetching messages. Please try again later. If the issue persists, contact the bot owner.",
                color=ERROR_EMBED_COLOR,
            )

            embed.add_field(name="Error", value=f"```{error}```", inline=False)

            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        # Iterate through the messages
        to_bulk_delete = []
        to_delete_14_days_old = []

        async for message in query:
            if message == interaction.message:
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
            if isinstance(interaction.channel, (discord.TextChannel, discord.Thread)):
                if len(to_bulk_delete) > 100:
                    for i in range(0, len(to_bulk_delete), 100):
                        await interaction.channel.delete_messages(
                            to_bulk_delete[i : i + 100]
                        )
                else:
                    await interaction.channel.delete_messages(to_bulk_delete)
            else:
                embed = discord.Embed(
                    title="Error",
                    description="I cannot delete messages in this channel.",
                    color=ERROR_EMBED_COLOR,
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

        except discord.errors.Forbidden as error:
            embed = discord.Embed(
                title="Error",
                description="I do not have permission to delete messages in this channel. Please make sure I have the `Manage Messages` permission.",
                color=ERROR_EMBED_COLOR,
            )

            embed.add_field(name="Error", value=f"```{error}```", inline=False)

            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        except discord.errors.HTTPException as error:
            embed = discord.Embed(
                title="Error",
                description="An error occurred while deleting messages. Please try again later. If the issue persists, contact the bot owner.",
                color=ERROR_EMBED_COLOR,
            )

            embed.add_field(name="Error", value=f"```{error}```", inline=False)

            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        # Number of messages deleted
        number_of_messages_deleted = len(to_bulk_delete)

        has_deleted = False

        # If there are messages that are over 14 days old, we will delete them individually, but check with the user first
        if len(to_delete_14_days_old) > 0:
            # Ask the user if they want to delete the messages over 14 days old
            class ConfirmDeleteView(ui.View):
                def __init__(self, interaction, to_delete_14_days_old):
                    super().__init__()
                    self.interaction = interaction
                    self.to_delete_14_days_old = to_delete_14_days_old
                    self.value = None

                @ui.button(label="Confirm", style=discord.ButtonStyle.green)
                async def confirm(
                    self, button: ui.Button, interaction: discord.Interaction
                ):
                    self.value = True
                    self.stop()

                @ui.button(label="Cancel", style=discord.ButtonStyle.red)
                async def cancel(
                    self, button: ui.Button, interaction: discord.Interaction
                ):
                    self.value = False
                    self.stop()

            prompt_embed = discord.Embed(
                title="Bot Cleanup",
                description=(
                    f"Found {len(to_delete_14_days_old)} messages older than 14 days. "
                    "Do you want to delete them individually?"
                ),
                color=MAIN_EMBED_COLOR,
            )

            prompt_message = await interaction.followup.send(
                embed=prompt_embed,
                view=ConfirmDeleteView(interaction, to_delete_14_days_old),
            )

            unable_to_delete = []

            try:
                view = ConfirmDeleteView(interaction, to_delete_14_days_old)
                await view.wait()

                if view.value:
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
                pass

        if not has_deleted:
            embed = discord.Embed(
                title="Bot Cleanup",
                description=f"Success!\nMessages Fetched: `{limit}`\nMessages Bulk Deleted: `{number_of_messages_deleted}`\nTotal Messages Deleted: `{number_of_messages_deleted}`",
                color=MAIN_EMBED_COLOR,
            )

        embed.set_footer(
            text=f"Cleanup Utility | {self.bot.user.name} | Deleting this message after 10s"
        )

        await interaction.followup.send(embed=embed, delete_after=10)

    @_bot_cleanup.error
    async def _bot_cleanup_error(self, interaction: discord.Interaction, error):
        await handle_error(interaction, error)


async def setup(bot: commands.Bot):
    await bot.add_cog(Utils_CleanupSlashCommands(bot))
