# afragment

[![PyPI version](https://img.shields.io/pypi/v/afragment.svg)](https://pypi.org/project/afragment/)
[![Python](https://img.shields.io/pypi/pyversions/afragment.svg)](https://pypi.org/project/afragment/)
[![License](https://img.shields.io/github/license/TheBrainAir/afragment.svg)](https://github.com/TheBrainAir/afragment/blob/main/LICENSE)
[![Downloads](https://img.shields.io/pypi/dm/afragment.svg)](https://pypi.org/project/afragment/)

Async Python library for the Fragment.com API. Purchase Telegram Stars, Premium subscriptions, and TON balance topups programmatically.

## Installation

```bash
pip install afragment
```

## Authentication

You need two credentials from Fragment.com:
- `FRAGMENT_HASH` - Session hash (from URL parameter)
- `FRAGMENT_COOKIE` - Session cookie (from browser)

### How to get credentials

1. Go to [Fragment.com](https://fragment.com) and log in
2. Complete KYC verification if you haven't already
3. Open Developer Tools (F12 or Right-click → Inspect)
4. Go to the **Network** tab
5. Select **Fetch/XHR** filter
6. Perform any action on the site (e.g., search for a username)
7. Click on any API request and find the credentials as shown below:

![How to get Fragment credentials](https://github.com/TheBrainAir/afragment/blob/main/photo.png?raw=true)

- **FRAGMENT_HASH**: Found in the request URL as `?hash=...` parameter
- **FRAGMENT_COOKIE**: Found in the Request Headers under `Cookie`

## Quick Start

**One call = ready transaction!** Just pass username, value, and wallet address.

### 🌟 Buy Telegram Stars

```python
import asyncio
from afragment import AsyncFragmentClient, nano_to_ton

async def main():
    async with AsyncFragmentClient(
        fragment_hash="your_hash",
        fragment_cookie="your_cookie"
    ) as client:
        result = await client.buy_stars("username", 100, "your_wallet_address")
        
        # Get transaction details
        tx = result["transaction"]["messages"][0]
        print(f"Recipient: {result['recipient']['name']}")
        print(f"Price: {result['amount']} TON")
        print(f"Send to: {tx['address']}")
        print(f"Amount: {nano_to_ton(int(tx['amount']))} TON")

asyncio.run(main())
```

### ⭐ Gift Telegram Premium

```python
async def gift_premium():
    async with AsyncFragmentClient(
        fragment_hash="your_hash",
        fragment_cookie="your_cookie"
    ) as client:
        # Gift 12 months of Premium
        result = await client.buy_premium("username", 12, "your_wallet_address")
        
        tx = result["transaction"]["messages"][0]
        print(f"Send to: {tx['address']}")
        print(f"Amount: {tx['amount']} nanoTON")
```

### 💎 TON Balance Topup

```python
async def topup_ton():
    async with AsyncFragmentClient(
        fragment_hash="your_hash",
        fragment_cookie="your_cookie"
    ) as client:
        # Topup 10 TON
        result = await client.buy_ton_topup("username", 10, "your_wallet_address")
        
        tx = result["transaction"]["messages"][0]
        print(f"Send to: {tx['address']}")
        print(f"Amount: {tx['amount']} nanoTON")
```

## API Reference

### Main Methods

| Method | Parameters | Description |
|--------|------------|-------------|
| `buy_stars(username, quantity, wallet_address)` | quantity >= 50 | Purchase Telegram Stars |
| `buy_premium(username, months, wallet_address)` | months: 3, 6, or 12 | Gift Telegram Premium |
| `buy_ton_topup(username, amount, wallet_address)` | amount >= 1 (whole number) | TON balance topup |

### Return Value

All methods return a dictionary:

```python
{
    "recipient": {
        "name": "User Name",
        "photo": "photo_url"
    },
    "amount": "2.5",  # Price in TON
    "transaction": {
        "messages": [{
            "address": "EQ...",      # Where to send TON
            "amount": "2500000000",  # Amount in nanoTON
            "payload": "base64..."   # Transaction payload
        }]
    }
}
```

## Utility Functions

### Payload Decoding

```python
from afragment import decode_payload, extract_ref_id, extract_transaction_text

payload = result["transaction"]["messages"][0]["payload"]

# Extract reference ID
ref_id = extract_ref_id(payload)

# Extract human-readable comment
comment = extract_transaction_text(payload, "stars", quantity=100)
# Output: "100 Telegram Stars\n\nRef#abc123"
```

### Amount Conversion

```python
from afragment import nano_to_ton, ton_to_nano

ton = nano_to_ton(1500000000)  # 1.5 TON
nano = ton_to_nano(1.5)        # 1500000000 nanoTON
```

## Error Handling

```python
from afragment import (
    AsyncFragmentClient,
    FragmentAPIError,
    AuthenticationError,
    PriceChangedError,
    InvalidRecipientError,
)

async def safe_purchase():
    async with AsyncFragmentClient(
        fragment_hash="your_hash",
        fragment_cookie="your_cookie"
    ) as client:
        try:
            result = await client.buy_stars("username", 100, "wallet_address")
        except InvalidRecipientError:
            print("User not found!")
        except PriceChangedError:
            print("Price changed, try again")
        except AuthenticationError:
            print("Session expired, refresh credentials")
        except ValueError as e:
            print(f"Validation error: {e}")
```

### Exceptions

| Exception | Description |
|-----------|-------------|
| `FragmentAPIError` | Base exception for all API errors |
| `AuthenticationError` | Invalid or expired credentials |
| `PriceChangedError` | Price changed during request (retry recommended) |
| `InvalidRecipientError` | User not found or not eligible |
| `ValueError` | Invalid input (validation failed) |

## Validation Rules

| Method | Parameter | Validation |
|--------|-----------|------------|
| `buy_stars` | `quantity` | Minimum 50 |
| `buy_premium` | `months` | Must be 3, 6, or 12 |
| `buy_ton_topup` | `amount` | Minimum 1, whole numbers only |

## Contact

- Telegram: [@thebraina1r](https://t.me/thebraina1r)

## Donate

If you find this library useful, you can support the development:

- TON Wallet: `thebrainair.ton`
