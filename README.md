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

### Purchasing Telegram Stars

```python
import asyncio
from afragment import AsyncFragmentClient

# Wallet configuration (only address required, chain defaults to "-239")
WALLET_ACCOUNT = {
    "address": "your_wallet_address",
}

async def buy_stars():
    async with AsyncFragmentClient(
        fragment_hash="your_hash",
        fragment_cookie="your_cookie"
    ) as client:
        # Step 1: Search for recipient
        search = await client.search_stars_recipient("username", quantity=100)
        recipient = search["found"]["recipient"]
        print(f"Found: {search['found']['name']}")

        # Step 2: Initialize purchase (minimum 50 stars)
        init = await client.init_buy_stars_request(recipient, quantity=100)
        req_id = init["req_id"]
        print(f"Price: {init['amount']} TON")

        # Step 3: Get transaction details (device info is optional)
        tx = await client.get_buy_stars_link(req_id, WALLET_ACCOUNT)
        print(f"Send to: {tx['transaction']['messages'][0]['address']}")
        print(f"Amount: {tx['transaction']['messages'][0]['amount']} nanoTON")

asyncio.run(buy_stars())
```

### Gifting Telegram Premium

```python
async def gift_premium():
    async with AsyncFragmentClient(
        fragment_hash="your_hash",
        fragment_cookie="your_cookie"
    ) as client:
        # Step 1: Search for recipient
        search = await client.search_premium_gift_recipient("username")
        recipient = search["found"]["recipient"]

        # Step 2: Initialize purchase (3, 6, or 12 months)
        init = await client.init_gift_premium_request(recipient, months=3)
        req_id = init["req_id"]

        # Step 3: Get transaction details
        tx = await client.get_gift_premium_link(req_id, WALLET_ACCOUNT)
```

### TON Balance Topup

```python
async def topup_ton():
    async with AsyncFragmentClient(
        fragment_hash="your_hash",
        fragment_cookie="your_cookie"
    ) as client:
        # Step 1: Search for recipient
        search = await client.search_ads_topup_recipient("username")
        recipient = search["found"]["recipient"]

        # Step 2: Initialize topup (minimum 1 TON, whole numbers only)
        init = await client.init_ads_topup_request(recipient, amount=100)
        req_id = init["req_id"]

        # Step 3: Get transaction details
        tx = await client.get_ads_topup_link(req_id, WALLET_ACCOUNT)
```

## Validation Rules

The library validates input before making API requests:

| Method | Parameter | Validation |
|--------|-----------|------------|
| `search_stars_recipient` | `quantity` | Minimum 50 |
| `init_buy_stars_request` | `quantity` | Minimum 50 |
| `init_gift_premium_request` | `months` | Must be 3, 6, or 12 |
| `init_ads_topup_request` | `amount` | Minimum 1, whole numbers only |

## Utility Functions

### Payload Decoding

```python
from afragment import decode_payload, extract_ref_id, format_transaction_comment

# Decode base64 payload from transaction
payload = tx["transaction"]["messages"][0]["payload"]
decoded = decode_payload(payload)

# Extract reference ID
ref_id = extract_ref_id(payload)
print(f"Reference: {ref_id}")

# Format transaction comments
comment = format_transaction_comment("stars", quantity=100, ref_id=ref_id)
# Output: "100 Telegram Stars\n\nRef#abc123"

comment = format_transaction_comment("premium", months=3, ref_id=ref_id)
# Output: "Telegram Premium for 3 months\n\nRef#abc123"

comment = format_transaction_comment("topup", ref_id=ref_id)
# Output: "Telegram account top up\n\nRef#abc123"
```

### Amount Conversion

```python
from afragment import nano_to_ton, ton_to_nano

# Convert between TON and nanoTON
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
            # Validation error if quantity < 50
            search = await client.search_stars_recipient("username", 100)
        except ValueError as e:
            print(f"Validation error: {e}")
            return
        except InvalidRecipientError:
            print("User not found!")
            return

        # Retry on price change
        for attempt in range(3):
            try:
                init = await client.init_buy_stars_request(
                    search["found"]["recipient"], 100
                )
                break
            except PriceChangedError:
                print(f"Price changed, retrying... ({attempt + 1}/3)")
                await asyncio.sleep(1)
        else:
            print("Failed after 3 attempts")
            return

        try:
            tx = await client.get_buy_stars_link(init["req_id"], WALLET_ACCOUNT)
        except AuthenticationError:
            print("Session expired, please refresh credentials")
            return
```

## API Reference

### Client Methods

| Method | Description | Validation |
|--------|-------------|------------|
| `search_stars_recipient(query, quantity)` | Find user for Stars purchase | quantity >= 50 |
| `init_buy_stars_request(recipient, quantity)` | Initialize Stars purchase | quantity >= 50 |
| `get_buy_stars_link(id, account, [device])` | Get Stars transaction details | account required, device optional |
| `search_premium_gift_recipient(query)` | Find user for Premium gift | - |
| `init_gift_premium_request(recipient, months)` | Initialize Premium purchase | months in (3, 6, 12) |
| `get_gift_premium_link(id, account, [device])` | Get Premium transaction details | account required, device optional |
| `search_ads_topup_recipient(query)` | Find user for TON topup | - |
| `init_ads_topup_request(recipient, amount)` | Initialize TON topup | amount >= 1, int only |
| `get_ads_topup_link(id, account, [device])` | Get TON topup transaction details | account required, device optional |

### Exceptions

| Exception | Description |
|-----------|-------------|
| `FragmentAPIError` | Base exception for all API errors |
| `AuthenticationError` | Invalid or expired credentials |
| `PriceChangedError` | Price changed during request (retry recommended) |
| `InvalidRecipientError` | User not found or not eligible |
| `ValueError` | Invalid input (validation failed) |

### Wallet Account Format

```python
{
    "address": "UQ...",  # Your TON wallet address (required)
    # "chain": "-239",   # Optional, defaults to "-239" (TON mainnet)
}
```

### Device Info Format (Optional)

Device info is optional. The library uses Tonkeeper defaults:

```python
{
    "platform": "android",
    "appName": "Tonkeeper",
    "appVersion": "5.0.18",
    "maxProtocolVersion": 2,
    "features": ["SendTransaction", {"name": "SendTransaction", "maxMessages": 4}]
}
```

You can pass custom device info if needed:

```python
tx = await client.get_buy_stars_link(req_id, WALLET_ACCOUNT, custom_device_info)
```


## Contact

- Telegram: [@thebraina1r](https://t.me/thebraina1r)

## Donate

If you find this library useful, you can support the development:

- TON Wallet: `thebrainair.ton`
