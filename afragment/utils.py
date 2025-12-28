"""
Utility functions for payload decoding and transaction formatting.
"""

import base64
import re


def decode_payload(payload: str) -> bytes:
    """
    Decode a base64-encoded transaction payload.

    Args:
        payload: Base64-encoded payload string from API response.

    Returns:
        Decoded payload as bytes.
    """
    return base64.b64decode(payload)


def extract_ref_id(payload: str) -> str:
    """
    Extract the reference ID from a base64-encoded payload.

    The reference ID is typically found in the format "Ref#<id>" within
    the decoded payload.

    Args:
        payload: Base64-encoded payload string from API response.

    Returns:
        The extracted reference ID, or empty string if not found.
    """
    try:
        decoded = decode_payload(payload)
        # Try to decode as UTF-8 text
        text = decoded.decode("utf-8", errors="ignore")
        # Look for Ref# pattern
        match = re.search(r"Ref#(\w+)", text)
        if match:
            return match.group(1)
        return ""
    except Exception:
        return ""


def format_transaction_comment(transaction_type: str, **kwargs) -> str:
    """
    Generate the proper transaction comment format for each purchase type.

    Args:
        transaction_type: One of "stars", "premium", or "topup".
        **kwargs: Additional parameters:
            - quantity (int): Required for "stars" type
            - months (int): Required for "premium" type
            - ref_id (str): Reference ID to include in comment

    Returns:
        Formatted transaction comment string.

    Raises:
        ValueError: If required kwargs are missing for the transaction type.

    Examples:
        >>> format_transaction_comment("stars", quantity=100, ref_id="abc123")
        '100 Telegram Stars\\n\\nRef#abc123'

        >>> format_transaction_comment("premium", months=3, ref_id="xyz789")
        'Telegram Premium for 3 months\\n\\nRef#xyz789'

        >>> format_transaction_comment("topup", ref_id="def456")
        'Telegram account top up\\n\\nRef#def456'
    """
    ref_id = kwargs.get("ref_id", "")

    if transaction_type == "stars":
        quantity = kwargs.get("quantity")
        if quantity is None:
            raise ValueError("quantity is required for stars transaction")
        comment = f"{quantity} Telegram Stars"

    elif transaction_type == "premium":
        months = kwargs.get("months")
        if months is None:
            raise ValueError("months is required for premium transaction")
        comment = f"Telegram Premium for {months} months"

    elif transaction_type == "topup":
        comment = "Telegram account top up"

    else:
        raise ValueError(f"Unknown transaction type: {transaction_type}")

    if ref_id:
        comment += f"\n\nRef#{ref_id}"

    return comment


def nano_to_ton(nano_ton: int) -> float:
    """
    Convert nanoTON to TON.

    Args:
        nano_ton: Amount in nanoTON (1 TON = 1,000,000,000 nanoTON).

    Returns:
        Amount in TON.
    """
    return nano_ton / 1_000_000_000


def ton_to_nano(ton: float) -> int:
    """
    Convert TON to nanoTON.

    Args:
        ton: Amount in TON.

    Returns:
        Amount in nanoTON (1 TON = 1,000,000,000 nanoTON).
    """
    return int(ton * 1_000_000_000)



