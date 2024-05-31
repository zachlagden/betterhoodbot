"""
(c) 2024 Zachariah Michael Lagden (All Rights Reserved)
You may not use, copy, distribute, modify, or sell this code without the express permission of the author.

This is a helper for formatting various types of data.
"""

# Functions


def format_money(amount: int) -> str:
    return f"${amount:,}"


def format_time(seconds: int) -> str:
    """
    A function to format seconds into a human-readable format.

    Only output the highest time unit that is not zero.

    Example:
    3660 seconds -> 1 hour 1 minute
    300 seconds -> 5 minutes
    299 seconds -> 4 minutes 59 seconds
    30 seconds -> 30 seconds
    """
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60

    # Prepare the output based on the largest time unit that's not zero
    time_parts = []
    if hours > 0:
        time_parts.append(f"{hours} hour{'s' if hours > 1 else ''}")
    if minutes > 0:
        time_parts.append(f"{minutes} minute{'s' if minutes > 1 else ''}")
    if seconds > 0 and not time_parts:
        time_parts.append(f"{seconds} second{'s' if seconds > 1 else ''}")

    return " ".join(time_parts)
