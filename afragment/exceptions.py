"""
Custom exceptions for the afragment library.
"""


class FragmentAPIError(Exception):
    """Base exception for all Fragment API errors."""

    def __init__(self, message: str, response: dict = None):
        super().__init__(message)
        self.message = message
        self.response = response

    def __str__(self):
        return self.message


class AuthenticationError(FragmentAPIError):
    """Raised when authentication fails (invalid or expired hash/cookie)."""

    def __init__(self, message: str = "Authentication failed: invalid or expired credentials", response: dict = None):
        super().__init__(message, response)


class PriceChangedError(FragmentAPIError):
    """Raised when the price changes during initialization."""

    def __init__(self, message: str = "Price was changed, please retry", response: dict = None):
        super().__init__(message, response)


class InvalidRecipientError(FragmentAPIError):
    """Raised when the recipient username doesn't exist or isn't eligible."""

    def __init__(self, message: str = "Invalid recipient: user not found or not eligible", response: dict = None):
        super().__init__(message, response)



