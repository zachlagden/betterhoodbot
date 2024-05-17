"""
(c) 2024 Zachariah Michael Lagden (All Rights Reserved)
You may not use, copy, distribute, modify, or sell this code without the express permission of the author.

This cog is responsible for the money interactions commands in the bot.
"""

# Python standard library
import logging
import random

# Third-party libraries
from discord.ext import commands
import discord

# Helper functions
from helpers.colors import MAIN_EMBED_COLOR, ERROR_EMBED_COLOR, SUCCESS_EMBED_COLOR
from helpers.errors import handle_error
from helpers.money import (
    user_balance,
    format_money,
    format_time,
    DatabaseImpossibleError,
)

# Setup logger for this module
RICKLOG = logging.getLogger("rickbot")


class MoneyInteractionsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def create_embed(self, title: str, description: str, color: int) -> discord.Embed:
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_footer(text="Better Hood Money")
        return embed

    @commands.command(name="steal", aliases=["rob"])
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def _steal(self, ctx: commands.Context, member: discord.Member):
        if member == ctx.author:
            await ctx.message.reply(
                embed=self.create_embed(
                    "Error", "You cannot steal from yourself!", ERROR_EMBED_COLOR
                ),
                mention_author=False,
            )

            ctx.command.reset_cooldown(ctx)  # type: ignore
            return

        success_chance = random.randint(1, 100)
        query1 = user_balance(ctx.author.id)
        query2 = user_balance(member.id)

        if query1 and query2:
            stealer_wallet, stealer_bank = query1
            victim_wallet, victim_bank = query2
        else:
            raise DatabaseImpossibleError("User balance query failed.")

        if stealer_wallet < 500:
            await ctx.message.reply(
                embed=self.create_embed(
                    "Error",
                    "You need at least $500 in your wallet to steal.",
                    ERROR_EMBED_COLOR,
                ),
                mention_author=False,
            )

            ctx.command.reset_cooldown(ctx)  # type: ignore
            return
        elif victim_wallet < 500:
            await ctx.message.reply(
                embed=self.create_embed(
                    "Error",
                    "The victim needs at least $500 in their wallet to steal.",
                    ERROR_EMBED_COLOR,
                ),
                mention_author=False,
            )

            ctx.command.reset_cooldown(ctx)  # type: ignore
            return
        elif stealer_bank < 1000:
            await ctx.message.reply(
                embed=self.create_embed(
                    "Error",
                    "You need at least $1,000 in your bank to steal.",
                    ERROR_EMBED_COLOR,
                ),
                mention_author=False,
            )

            ctx.command.reset_cooldown(ctx)  # type: ignore
            return
        elif victim_bank < 1000:
            await ctx.message.reply(
                embed=self.create_embed(
                    "Error",
                    "The victim needs at least $1,000 in their bank to steal.",
                    ERROR_EMBED_COLOR,
                ),
                mention_author=False,
            )

            ctx.command.reset_cooldown(ctx)  # type: ignore
            return

        if success_chance <= 30:  # 30% chance of success
            stolen_percent = random.choices(
                [10, 30, 50, 70, 80, 90, 100], cum_weights=[10, 30, 60, 80, 90, 95, 100]
            )[0]

            stolen_amount = int((stolen_percent / 100) * victim_wallet)

            user_balance(ctx.author.id, adjust_wallet=stolen_amount)
            user_balance(member.id, adjust_wallet=-stolen_amount)

            await log_money_transaction(
                [
                    {
                        "users": {"from": member, "to": ctx.author},
                        "movement": {"from": "wallet", "to": "wallet"},
                        "amount": stolen_amount,
                        "reason": "Robbery Success",
                    }
                ],
            )

            situations = [
                "sneaking into their room while they were asleep",
                "hacking their digital wallet",
                "picking their pocket in a crowded market",
                "conning them with a fake charity",
                "distracting them with a street performance",
                "tricking them during a card game",
                "slipping away with their bag at the gym",
                "posing as a valet and taking their valuables",
                "setting up a fake toll booth",
                "creating a diversion at a cafe",
            ]

            situation = random.choice(situations)

            reply_embed = self.create_embed(
                "Successful Steal!",
                f"You successfully stole {format_money(stolen_amount)} by {situation}.",
                SUCCESS_EMBED_COLOR,
            )
            await ctx.message.reply(embed=reply_embed, mention_author=False)

        else:  # Consequences if the steal fails
            fail_situations = [
                "during the escape, you tripped and were caught",
                "the target noticed and confronted you immediately",
                "a nearby security camera caught the entire act",
                "the target's friends intervened just in time",
                "a sudden call from the target's phone interrupted your attempt",
                "a sudden rainstorm ruined your escape plan",
                "the target's pet dog started barking loudly",
                "a sudden earthquake shook the ground",
                "a sudden power outage occurred",
            ]

            fail_situation = random.choice(fail_situations)

            if success_chance <= 80:  # 50% chance to lose some of their wallet
                lost_percent = random.choices(
                    [10, 30, 50, 70, 80, 90, 100],
                    cum_weights=[10, 30, 60, 80, 90, 95, 100],
                )[0]
                lost_amount = int((lost_percent / 100) * stealer_wallet)

                user_balance(member.id, adjust_wallet=-lost_amount)

                await log_money_transaction(
                    [
                        {
                            "users": {"from": ctx.author, "to": self.bot.user},
                            "movement": {"from": "wallet", "to": "bank"},
                            "amount": -lost_amount,
                            "reason": "Robbery Failure (Lost Wallet)",
                        }
                    ],
                )

                reply_embed = self.create_embed(
                    "Caught!",
                    f"Caught! You lost {format_money(lost_amount)} from your wallet {fail_situation}.",
                    ERROR_EMBED_COLOR,
                )
                await ctx.message.reply(embed=reply_embed, mention_author=False)

            elif success_chance <= 90:  # 40% chance of being caught by the victim
                user_balance(ctx.author.id, adjust_wallet=-stealer_wallet)
                user_balance(member.id, adjust_wallet=stealer_wallet)

                await log_money_transaction(
                    [
                        {
                            "users": {"from": ctx.author, "to": member},
                            "movement": {"from": "wallet", "to": "wallet"},
                            "amount": stealer_wallet,
                            "reason": "Robbery Failure (Caught by Victim)",
                        }
                    ],
                )

                reply_embed = self.create_embed(
                    "Caught by Victim!",
                    "Caught by the victim! They took all the money in your wallet.",
                    ERROR_EMBED_COLOR,
                )
                await ctx.message.reply(embed=reply_embed, mention_author=False)

            else:  # 10% chance of being caught by the police
                bank_penalty_percent = random.randint(1, 10)
                bank_penalty = int((bank_penalty_percent / 100) * stealer_bank)

                user_balance(
                    ctx.author.id,
                    adjust_wallet=-stealer_wallet,
                    adjust_bank=-bank_penalty,
                )

                await log_money_transaction(
                    [
                        {
                            "users": {"from": ctx.author, "to": self.bot.user},
                            "movement": {"from": "wallet", "to": "bank"},
                            "amount": -bank_penalty,
                            "reason": "Robbery Failure (Caught by Police)",
                        }
                    ],
                )

                reply_embed = self.create_embed(
                    "Caught by Police!",
                    f"Caught by the police! You've lost all your wallet money and {format_money(bank_penalty)} from your bank.",
                    ERROR_EMBED_COLOR,
                )
                await ctx.message.reply(embed=reply_embed, mention_author=False)

    @_steal.error
    async def _steal_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CommandOnCooldown):
            reply_embed = self.create_embed(
                "Error",
                f"You can steal again in {format_time(round(error.retry_after))}.",
                ERROR_EMBED_COLOR,
            )
            await ctx.message.reply(embed=reply_embed, mention_author=False)

        else:
            ctx.command.reset_cooldown(ctx)  # type: ignore

        if isinstance(error, commands.MissingRequiredArgument):
            reply_embed = self.create_embed(
                "Error",
                "Please mention the user you would like to steal from.",
                ERROR_EMBED_COLOR,
            )
            await ctx.message.reply(embed=reply_embed, mention_author=False)

        elif isinstance(error, commands.BadArgument):
            reply_embed = self.create_embed(
                "Error",
                "Please mention a valid user.",
                ERROR_EMBED_COLOR,
            )
            await ctx.message.reply(embed=reply_embed, mention_author=False)

        else:
            await handle_error(ctx, error)


async def setup(bot: commands.Bot):
    await bot.add_cog(MoneyInteractionsCog(bot))
