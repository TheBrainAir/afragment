"""
afragment - Async Python library for Fragment.com API

Purchase Telegram Stars, Premium subscriptions, and TON topups programmatically.

Quick Start (simplified API):
    async with AsyncFragmentClient(hash="...", cookie="...") as client:
        # Buy Stars - one call, get transaction ready
        result = await client.buy_stars("username", 100, "wallet_address")
        
        # Gift Premium - one call, get transaction ready
        result = await client.buy_premium("username", 12, "wallet_address")
        
        # TON Topup - one call, get transaction ready
        result = await client.buy_ton_topup("username", 10, "wallet_address")
        
        # Access transaction details:
        address = result["transaction"]["messages"][0]["address"]
        amount = result["transaction"]["messages"][0]["amount"]

For advanced usage with more control, use the low-level methods:
    search_stars_recipient(), init_buy_stars_request(), get_buy_stars_link(), etc.
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

__version__ = "0.3.0"
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

