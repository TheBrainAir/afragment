"""
Utility functions for payload decoding and transaction formatting.
"""

import base64
import re


def fix_base64_padding(b64_string: str) -> str:
    """Add missing '=' padding characters to base64 string."""
    missing_padding = len(b64_string) % 4
    if missing_padding:
        b64_string += '=' * (4 - missing_padding)
    return b64_string


def decode_payload(payload: str) -> bytes:
    """
    Decode a base64-encoded transaction payload.

    Args:
        payload: Base64-encoded payload string from API response.

    Returns:
        Decoded payload as bytes.
    """
    return base64.b64decode(fix_base64_padding(payload))


def extract_ref_id(payload: str) -> str:
    """
    Extract the reference ID from a base64-encoded payload.

    The reference ID is found in the decoded payload text, typically
    in the format "Ref#<id>" or "Ref #<id>".

    Args:
        payload: Base64-encoded payload string from API response.

    Returns:
        The extracted reference ID, or empty string if not found.
    """
    try:
        # Decode base64 with padding fix
        decoded_bytes = decode_payload(payload)
        
        # Decode only printable ASCII (32-126) and newline chars (10, 13)
        # Same approach as extract_transaction_text for topup
        readable = ''.join(
            chr(b) if (32 <= b <= 126 or b in (10, 13)) else '' 
            for b in decoded_bytes
        )
        
        # Extract ref_id from "Ref#" or "Ref" - take everything until whitespace/newline
        if "Ref#" in readable:
            match = re.search(r'Ref#([^\s\n\r]+)', readable)
            if match:
                return match.group(1)
        elif "Ref" in readable:
            match = re.search(r'Ref([^\s\n\r#]+)', readable)
            if match:
                return match.group(1).strip()
        
        return ""
    except Exception:
        return ""


def extract_transaction_text(payload: str, transaction_type: str = None, **kwargs) -> str:
    """
    Extract transaction text from payload (for Stars, Premium, or Topup).

    Args:
        payload: Base64-encoded payload string from API response.
        transaction_type: "stars", "premium", or "topup".
        **kwargs: Additional parameters:
            - quantity (int): For stars transactions

    Returns:
        Extracted transaction text with Ref ID.
    """
    try:
        # Decode base64 with padding fix
        decoded_bytes = decode_payload(payload)
        
        # Convert bytes to string, replacing non-readable characters with spaces
        decoded_text = ''.join(chr(b) if 32 <= b < 127 else ' ' for b in decoded_bytes)
        
        # Remove extra whitespace
        clean_text = re.sub(r'\s+', ' ', decoded_text).strip()
        
        if transaction_type == "stars":
            quantity = kwargs.get("quantity")
            if quantity:
                # Look for "{quantity} Telegram Stars" pattern
                match = re.search(rf"{quantity} Telegram Stars.*", clean_text)
                if match:
                    final_text = match.group(0).replace('Ref #', 'Ref#')
                    return final_text
        
        elif transaction_type == "premium":
            # Look for "Telegram.*?Ref\s*#\S+" pattern (same as BuyPremium)
            match = re.search(r'(Telegram.*?Ref\s*#\S+)', clean_text)
            if match:
                final_text = match.group(1).replace('Ref #', 'Ref#')
                return final_text
            # Fallback: return cleaned text (same as BuyPremium)
            return clean_text.replace('Ref #', 'Ref#')
        
        elif transaction_type == "topup":
            # For topup, extract ref_id and format comment (same approach as otherproject.md)
            # Decode only printable ASCII (32-126) and newline chars (10, 13)
            readable = ''.join(
                chr(b) if (32 <= b <= 126 or b in (10, 13)) else '' 
                for b in decoded_bytes
            )
            
            # Extract ref_id from "Ref#" or "Ref" - take everything until whitespace/newline
            ref_id = ""
            if "Ref#" in readable:
                # Find Ref# and extract everything after it until whitespace/newline
                match = re.search(r'Ref#([^\s\n\r]+)', readable)
                if match:
                    ref_id = match.group(1)
            elif "Ref" in readable:
                # Fallback: find Ref and extract everything after it until whitespace/newline
                match = re.search(r'Ref([^\s\n\r#]+)', readable)
                if match:
                    ref_id = match.group(1).strip()
            
            # Format comment: "Telegram account top up Ref#{ref_id}" (one space)
            if ref_id:
                return f"Telegram account top up Ref#{ref_id}"
            else:
                # Fallback: try to find pattern in cleaned text
                match = re.search(r'Telegram account top up.*', clean_text)
                if match:
                    final_text = match.group(0).replace('Ref #', 'Ref#').strip()
                    final_text = re.sub(r'\s+', ' ', final_text)
                    return final_text
                return "Telegram account top up"
        
        # Fallback for other types: return cleaned text
        return clean_text.replace('Ref #', 'Ref#')
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



