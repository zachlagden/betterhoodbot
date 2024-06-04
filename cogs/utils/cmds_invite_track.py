import discord
from discord.ext import commands
from datetime import datetime

# Helper functions and constants
from helpers.colors import MAIN_EMBED_COLOR, ERROR_EMBED_COLOR
from helpers.errors import handle_error
from helpers.db import invites_collection, users_collection


class Utils_InviteTrackerCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.invites_cache = {}

    async def cache_invites(self):
        """Caches the current invites for all guilds the bot is in."""
        for guild in self.bot.guilds:
            self.invites_cache[guild.id] = await guild.invites()

    @commands.Cog.listener()
    async def on_ready(self):
        """Caches invites when the bot is ready."""
        await self.cache_invites()

    @commands.Cog.listener()
    async def on_invite_create(self, invite):
        """Updates the cache and logs invite creation in the database."""
        if invite.guild.id in self.invites_cache:
            self.invites_cache[invite.guild.id].append(invite)
        else:
            self.invites_cache[invite.guild.id] = [invite]

        # Log invite creation in the database
        invites_collection.update_one(
            {"invite_code": invite.code, "guild_id": invite.guild.id},
            {
                "$set": {
                    "invite_code": invite.code,
                    "guild_id": invite.guild.id,
                    "inviter_id": invite.inviter.id,
                    "max_uses": invite.max_uses,
                    "created_at": datetime.utcnow(),
                    "deleted": False,
                }
            },
            upsert=True,
        )

    @commands.Cog.listener()
    async def on_invite_delete(self, invite):
        """Updates the cache and logs invite deletion in the database."""
        if invite.guild.id in self.invites_cache:
            self.invites_cache[invite.guild.id] = [
                i for i in self.invites_cache[invite.guild.id] if i.code != invite.code
            ]

        # Log invite deletion in the database
        invites_collection.update_one(
            {"invite_code": invite.code, "guild_id": invite.guild.id},
            {"$set": {"deleted": True, "deleted_at": datetime.utcnow()}},
        )

        # Update users who joined with this invite
        users_collection.update_many(
            {"invite_code": invite.code, "guild_id": invite.guild.id},
            {"$set": {"invite_code": "deleted"}},
        )

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Tracks which invite a member used to join and updates the database."""
        cached_invites = self.invites_cache.get(member.guild.id, [])
        current_invites = await member.guild.invites()

        used_invite = None
        for invite in cached_invites:
            for current_invite in current_invites:
                if (
                    invite.code == current_invite.code
                    and invite.uses < current_invite.uses
                ):
                    used_invite = current_invite
                    break
            if used_invite:
                break

        if used_invite:
            join_position = (
                users_collection.count_documents({"guild_id": member.guild.id}) + 1
            )
            invite_uses = (
                users_collection.count_documents({"invite_code": used_invite.code}) + 1
            )
            users_collection.insert_one(
                {
                    "user_id": member.id,
                    "guild_id": member.guild.id,
                    "invite_code": used_invite.code,
                    "inviter_id": used_invite.inviter.id,
                    "join_date": datetime.utcnow(),
                    "join_position": join_position,
                    "invite_uses_position": invite_uses,
                }
            )
            invites_collection.update_one(
                {"invite_code": used_invite.code}, {"$inc": {"uses": 1}}, upsert=True
            )

        await self.cache_invites()

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Tracks when a member leaves and updates the database."""
        record = users_collection.find_one(
            {"user_id": member.id, "guild_id": member.guild.id}
        )
        if record:
            inviter_id = record.get("inviter_id")
            if inviter_id:
                invites_collection.update_one(
                    {"inviter_id": inviter_id}, {"$inc": {"invites_count": -1}}
                )
            users_collection.update_one(
                {"user_id": member.id, "guild_id": member.guild.id},
                {"$set": {"left_date": datetime.utcnow()}},
            )

    @commands.command()
    async def invites(self, ctx, member: discord.Member = None):
        """Shows how many invites a user has."""
        if member is None:
            member = ctx.author

        invites_count = users_collection.count_documents({"inviter_id": member.id})

        embed = discord.Embed(
            title=f"{member.display_name}'s Invites",
            description=f"{member.mention} has invited {invites_count} member(s).",
            color=MAIN_EMBED_COLOR,
        )
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command()
    async def how_joined(self, ctx, member: discord.Member):
        """Checks how a user joined the server."""
        try:
            record = users_collection.find_one(
                {"user_id": member.id, "guild_id": ctx.guild.id}
            )

            if record:
                inviter_id = record.get("inviter_id")
                inviter = self.bot.get_user(inviter_id) if inviter_id else None
                invite_code = record.get("invite_code", "Unknown")
                join_position = record.get("join_position", "Unknown")
                invite_uses_position = record.get("invite_uses_position", "Unknown")

                embed = discord.Embed(
                    title="Invite Information",
                    description=(
                        f"{member.mention} joined using invite code `{invite_code}` created by "
                        f"{inviter.mention if inviter else 'Unknown User'}.\n"
                        f"Joined as member number {join_position}.\n"
                        f"Joined as invite number {invite_uses_position} with this invite."
                    ),
                    color=MAIN_EMBED_COLOR,
                )
            else:
                embed = discord.Embed(
                    title="Invite Information",
                    description=f"No information found for how {member.mention} joined.",
                    color=ERROR_EMBED_COLOR,
                )
        except Exception as e:
            embed = discord.Embed(
                title="Error",
                description=f"An error occurred while retrieving the data: {e}",
                color=ERROR_EMBED_COLOR,
            )

        await ctx.reply(embed=embed, mention_author=False)

    @how_joined.error
    async def how_joined_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            embed = discord.Embed(
                title="Invalid Usage",
                description="Please enter a valid user.",
                color=ERROR_EMBED_COLOR,
            )

            embed.add_field(
                name="Usage",
                value=f"```{ctx.prefix}how_joined [@user]```",
                inline=False,
            )
            embed.set_footer(text="Invite Tracker")

            await ctx.reply(embed=embed, mention_author=False)
        else:
            await handle_error(ctx, error)


async def setup(bot: commands.Bot):
    await bot.add_cog(Utils_InviteTrackerCommands(bot))
