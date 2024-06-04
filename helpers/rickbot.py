"""
(c) 2024 Zachariah Michael Lagden (All Rights Reserved)
You may not use, copy, distribute, modify, or sell this code without the express permission of the author.

This is a helper file full of RickBot specific constants and functions.

Please do not change anything in this file, as it will make me sad,
RickBot is RickBot, and RickBot is perfect. No need to change anything.
"""

# Import the required modules

# Python standard library
import glob

# Third-party modules
from termcolor import colored

# discord.py library
from discord.ext.commands import Bot

# Helpers
from helpers.logs import RICKLOG

# Functions


def display_error_logs_if_found_in_error_folder() -> None:
    errors = 0
    for _ in glob.glob("errors/*.txt"):  # type: ignore
        errors += 1

    print("\n")

    if errors > 0:
        RICKLOG.critical(
            f"Found {colored(errors, 'red', attrs=['bold', 'underline'])} unchecked error logs in the errors folder. If you have check these errors please delete them."
        )
        RICKLOG.info(
            f"Please check the error logs in the errors folder for more information."
        )


def rickbot_start_msg(bot: Bot) -> None:
    """
    Print a message to the console when the bot is ready.
    """
    print(START_SUCCESS_RICKBOT_ART)
    RICKLOG.info(f'Logged in as {colored(bot.user.name, "light_cyan", attrs=["bold", "underline"])} with ID {colored(bot.user.id, "light_cyan", attrs=["bold", "underline"])}')  # type: ignore
    # Log extra information from the bot
    RICKLOG.info(
        f'Connected to {colored(len(bot.guilds), "light_cyan", attrs=["bold", "underline"])} guilds.'
    )
    RICKLOG.info(
        f'Connected to {colored(len(bot.users), "light_cyan", attrs=["bold", "underline"])} users.'
    )
    RICKLOG.info(
        f'Loaded {colored(len(bot.commands), "light_cyan", attrs=["bold", "underline"])} commands.'
    )

    RICKLOG.info(
        f'Loaded {colored(len(bot.cogs), "light_cyan", attrs=["bold", "underline"])} cogs.'
    )

    display_error_logs_if_found_in_error_folder()


# Constants

START_SUCCESS_RICKBOT_ART = (
    str(
        """
    {0}        {1}
   {2}     {3}
  {4}     {5}
 {6}   {7}
{8} {9}
""".format(
            colored("//   ) )               //", "magenta", attrs=["bold"]),
            colored("//   ) )", "cyan", attrs=["bold"]),
            colored("//___/ /  ( )  ___     //___", "magenta", attrs=["bold"]),
            colored("//___/ /   ___    __  ___", "cyan", attrs=["bold"]),
            colored("/ ___ (   / / //   ) ) //\ \\", "magenta", attrs=["bold"]),  # type: ignore
            colored("/ __  (   //   ) )  / /", "cyan", attrs=["bold"]),
            colored("//   | |  / / //       //  \ \\", "magenta", attrs=["bold"]),  # type: ignore
            colored("//    ) ) //   / /  / /", "cyan", attrs=["bold"]),
            colored("//    | | / / ((____   //    \ \\", "magenta", attrs=["bold"]),  # type: ignore
            colored("//____/ / ((___/ /  / /", "cyan", attrs=["bold"]),
        )
    )
    + "                      "
    + colored("RickBot:", "magenta", attrs=["bold"])
    + " "
    + colored("Ready!", "green", attrs=["bold"])
    + "\n"
)
