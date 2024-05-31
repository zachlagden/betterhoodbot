"""
(c) 2024 Zachariah Michael Lagden (All Rights Reserved)
You may not use, copy, distribute, modify, or sell this code without the express permission of the author.

This is a helper for custom errors.
"""

# Import the required modules

# Helpers
from helpers.logs import RICKLOG_HELPERS

# Error Classes


class DatabaseImpossibleError(Exception):
    """Raised when an error that should'nt be possible occurs in the database."""

    def __init__(self, message: str):
        super().__init__(message)
        RICKLOG_HELPERS.critical(f"Database Impossible Error: {message}")


class MoneyTransactionLogError(Exception):
    """Raised when a money transaction log fails."""

    def __init__(self, message: str):
        super().__init__(message)
        RICKLOG_HELPERS.critical(f"Money Transaction Log Error: {message}")
