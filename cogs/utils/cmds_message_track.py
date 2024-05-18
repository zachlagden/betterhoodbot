"""
(c) 2024 Zachariah Michael Lagden (All Rights Reserved)
You may not use, copy, distribute, modify, or sell this code without the express permission of the author.

This cog is responsible for tracking the number of messages sent by users and assigning roles based on the number of messages sent.
"""

# Python standard library
from typing import Union

# Third-party libraries
from discord.ext import commands
import discord

# Import database
from db import messages_collection

# Helper functions
from helpers.colors import MAIN_EMBED_COLOR, ERROR_EMBED_COLOR, SUCCESS_EMBED_COLOR
from helpers.logs import RICKLOG_BG
from helpers.errors import handle_error


class Utils_MessageTrackingCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.role_rewards = {
            5000: 1227250237199089696,
            15000: 1227251162961412136,
            40000: 1227251655704055891,
            200000: 1227254873037344840,
        }

        self.reverse_role_rewards = {v: k for k, v in self.role_rewards.items()}

    @staticmethod
    def botadmincheck(ctx):
        return ctx.author.id in [1209943382860890206, 1153810697021554828]

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        RICKLOG_BG.debug(
            f"{message.author} sent a message, checking if they have been logged before..."
        )

        user_logger = messages_collection.find_one({"_id": message.author.id})

        if user_logger is None:
            RICKLOG_BG.debug(
                f"{message.author} has not been logged before, creating a new document..."
            )
            user_logger = {
                "_id": message.author.id,
                "count": 1,
            }
            messages_collection.insert_one(user_logger)
        else:
            RICKLOG_BG.debug(
                f"{message.author} has been logged before, incrementing their count..."
            )
            messages_collection.update_one(
                {"_id": message.author.id}, {"$inc": {"count": 1}}
            )
            user_logger["count"] += 1

        # Sorting roles by count in descending order to assign the highest valid role
        sorted_roles = sorted(
            self.role_rewards.items(), key=lambda item: item[0], reverse=True
        )

        highest_role_that_can_be_awarded = None
        for role_threshold, role_id in sorted_roles:
            if user_logger["count"] >= role_threshold:
                highest_role_that_can_be_awarded = role_id
                break

        # Get all the roles the user currently has that are in the role_rewards dictionary
        current_role = None
        for role in message.author.roles:
            if role.id in self.role_rewards.values():
                current_role = role
                break

        # Assign the new role if necessary
        if highest_role_that_can_be_awarded and (
            current_role is None or current_role.id != highest_role_that_can_be_awarded
        ):
            new_role = message.guild.get_role(highest_role_that_can_be_awarded)
            if new_role:
                # Before assigning the new role, remove all other roles that are in the role_rewards dictionary
                for role in message.author.roles:
                    if role.id in self.role_rewards.values():
                        await message.author.remove_roles(
                            role, reason="New role awarded."
                        )

                await message.author.add_roles(new_role)
                await message.channel.send(
                    f"Congratulations! You have reached {user_logger['count']} messages and have been awarded the {new_role.name} role.",
                    mention_author=False,
                )

    @commands.command(name="count")
    async def _count(self, ctx: commands.Context, member: Union[discord.Member, None]):
        """
        Check the number of messages a user has sent.
        """

        if not member:
            member = ctx.author

        user_logger = messages_collection.find_one({"_id": member.id})

        if user_logger is None:
            embed = discord.Embed(
                title=f"Messages sent by {member}",
                description="0 messages",
                color=MAIN_EMBED_COLOR,
            )
            embed.set_footer(text="Better Hood Utils")

            await ctx.reply(embed=embed, mention_author=False)
        else:
            embed = discord.Embed(
                title=f"Messages sent by {member}",
                description=f"{user_logger['count']} messages",
                color=MAIN_EMBED_COLOR,
            )
            embed.set_footer(text="Better Hood Utils")

            await ctx.reply(embed=embed, mention_author=False)

    @_count.error
    async def _count_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.BadArgument):
            embed = discord.Embed(
                title="Invalid Usage",
                description="Please enter a valid user.",
                color=ERROR_EMBED_COLOR,
            )
            embed.add_field("Usage", value=f"```{ctx.prefix}count <user>```")
            embed.set_footer(text="Better Hood Utils")

            await ctx.reply(embed=embed, mention_author=False)

        else:
            await handle_error(ctx, error)

    @commands.command(name="leaderboard")
    async def _leaderboard(self, ctx: commands.Context):
        """
        Show the top 10 users with the most messages sent.
        """

        leaderboard = messages_collection.find().sort("count", -1).limit(10)

        embed = discord.Embed(
            title="Leaderboard",
            description="Top 10 users with the most messages sent.",
            color=discord.Color.gold(),
        )

        for idx, user_logger in enumerate(leaderboard, start=1):
            member = ctx.guild.get_member(user_logger["_id"])
            embed.add_field(
                name=f"{idx}. {member}",
                value=f"{user_logger['count']} messages",
                inline=False,
            )

        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(Utils_MessageTrackingCommands(bot))
