"""
afragment - Async Python library for Fragment.com API

Purchase Telegram Stars, Premium subscriptions, and TON topups programmatically.
"""

from .client import AsyncFragmentClient
from .exceptions import (
    FragmentAPIError,
    AuthenticationError,
    PriceChangedError,
    InvalidRecipientError,
)
from .utils import (
    decode_payload,
    extract_ref_id,
    extract_transaction_text,
    format_transaction_comment,
    nano_to_ton,
    ton_to_nano,
)

__version__ = "0.2.0"
__all__ = [
    "AsyncFragmentClient",
    "FragmentAPIError",
    "AuthenticationError",
    "PriceChangedError",
    "InvalidRecipientError",
    "decode_payload",
    "extract_ref_id",
    "extract_transaction_text",
    "format_transaction_comment",
    "nano_to_ton",
    "ton_to_nano",
]

