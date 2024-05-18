import discord
from discord.ext import commands

# Helper functions and constants
from helpers.colors import MAIN_EMBED_COLOR, ERROR_EMBED_COLOR
from helpers.errors import handle_error
from db import invites_collection


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
        """Updates the cache when a new invite is created."""
        if invite.guild.id in self.invites_cache:
            self.invites_cache[invite.guild.id].append(invite)
        else:
            self.invites_cache[invite.guild.id] = [invite]

    @commands.Cog.listener()
    async def on_invite_delete(self, invite):
        """Updates the cache when an invite is deleted."""
        if invite.guild.id in self.invites_cache:
            self.invites_cache[invite.guild.id] = [
                i for i in self.invites_cache[invite.guild.id] if i.code != invite.code
            ]

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Tracks which invite a member used to join."""
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
            invites_collection.insert_one(
                {
                    "user_id": member.id,
                    "guild_id": member.guild.id,
                    "invite_code": used_invite.code,
                    "inviter_id": used_invite.inviter.id,
                }
            )

        await self.cache_invites()

    @commands.command()
    async def how_joined(self, ctx, member: discord.Member):
        """Checks how a user joined the server."""
        record = invites_collection.find_one(
            {"user_id": member.id, "guild_id": ctx.guild.id}
        )

        if record:
            inviter = self.bot.get_user(record["inviter_id"])
            invite_code = record["invite_code"]
            embed = discord.Embed(
                title="Invite Information",
                description=f"{member.mention} joined using invite code `{invite_code}` created by {inviter.mention if inviter else 'Unknown User'}.",
                color=MAIN_EMBED_COLOR,
            )
        else:
            embed = discord.Embed(
                title="Invite Information",
                description=f"No information found for how {member.mention} joined.",
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
                "Usage", f"```{ctx.prefix}how_joined [@user]```", inline=False
            )
            embed.set_footer(text="Invite Tracker")

            await ctx.reply(embed=embed, mention_author=False)
        else:
            await handle_error(ctx, error)


async def setup(bot: commands.Bot):
    await bot.add_cog(Utils_InviteTrackerCommands(bot))
