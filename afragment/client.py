"""
Async client for the Fragment.com API.
"""

import json
from typing import Optional

import aiohttp

from .exceptions import (
    FragmentAPIError,
    AuthenticationError,
    PriceChangedError,
    InvalidRecipientError,
)


class AsyncFragmentClient:
    """
    Async client for interacting with the Fragment.com API.

    This client allows you to programmatically purchase Telegram Stars,
    Premium subscriptions, and TON balance topups.

    Each transaction type follows a three-step workflow:
    1. Search - Find the recipient by username
    2. Initialize - Create purchase request and get pricing
    3. Get Link - Retrieve transaction details for payment

    Example:
        async with AsyncFragmentClient(hash="...", cookie="...") as client:
            # Search for recipient
            result = await client.search_stars_recipient("username", 100)
            recipient = result["found"]["recipient"]

            # Initialize purchase
            init = await client.init_buy_stars_request(recipient, 100)
            req_id = init["req_id"]

            # Get transaction details
            tx = await client.get_buy_stars_link(req_id, account, device)
    """

    BASE_URL = "https://fragment.com/api"
    DEFAULT_USER_AGENT = "Mozilla/5.0 (compatible; FragmentAPI/1.0)"
    DEFAULT_CHAIN = "-239"
    DEFAULT_DEVICE = {
        "platform": "android",
        "appName": "Tonkeeper",
        "appVersion": "5.0.18",
        "maxProtocolVersion": 2,
        "features": ["SendTransaction", {"name": "SendTransaction", "maxMessages": 4}]
    }

    def __init__(
        self,
        fragment_hash: str,
        fragment_cookie: str,
        user_agent: Optional[str] = None,
    ):
        """
        Initialize the Fragment API client.

        Args:
            fragment_hash: Session hash for authentication (FRAGMENT_HASH).
            fragment_cookie: Session cookie for authentication (FRAGMENT_COOKIE).
            user_agent: Optional custom User-Agent string.
        """
        self.fragment_hash = fragment_hash
        self.fragment_cookie = fragment_cookie
        self.user_agent = user_agent or self.DEFAULT_USER_AGENT
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def _ensure_session(self):
        """Ensure an aiohttp session exists."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={
                    "Cookie": self.fragment_cookie,
                    "User-Agent": self.user_agent,
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "X-Requested-With": "XMLHttpRequest",
                    "Origin": "https://fragment.com",
                    "Referer": "https://fragment.com/",
                }
            )

    async def close(self):
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def _make_request(self, data: dict) -> dict:
        """
        Make a POST request to the Fragment API.

        Args:
            data: Form data to send in the request body.

        Returns:
            Parsed JSON response as a dictionary.

        Raises:
            FragmentAPIError: If the API returns an error.
            AuthenticationError: If authentication fails.
            PriceChangedError: If price changed during request.
            InvalidRecipientError: If recipient is invalid.
        """
        await self._ensure_session()

        url = f"{self.BASE_URL}?hash={self.fragment_hash}"

        async with self._session.post(url, data=data) as response:
            text = await response.text()

            try:
                result = json.loads(text)
            except json.JSONDecodeError:
                raise FragmentAPIError(f"Invalid JSON response: {text[:200]}")

            # Check for errors in response
            if isinstance(result, dict):
                error = result.get("error")
                if error:
                    error_lower = str(error).lower()
                    if "price was changed" in error_lower:
                        raise PriceChangedError(str(error), result)
                    elif "auth" in error_lower or "unauthorized" in error_lower:
                        raise AuthenticationError(str(error), result)
                    elif any(x in error_lower for x in ["not found", "invalid", "no telegram users", "user not found"]):
                        raise InvalidRecipientError(str(error), result)
                    else:
                        raise FragmentAPIError(str(error), result)

            return result

    # ==================== Telegram Stars Methods ====================

    async def search_stars_recipient(self, query: str, quantity: int = 50) -> dict:
        """
        Search for a Telegram user to send Stars to.

        Args:
            query: Telegram username (without @).
            quantity: Minimum quantity for search (default: 50, minimum: 50).

        Returns:
            Dictionary containing:
                - found: {recipient, name, photo, myself}

        Raises:
            ValueError: If quantity is less than 50.
            InvalidRecipientError: If user not found.
        """
        if quantity < 50:
            raise ValueError("Minimum quantity is 50 stars")

        return await self._make_request({
            "method": "searchStarsRecipient",
            "query": query,
            "quantity": quantity,
        })

    async def init_buy_stars_request(self, recipient: str, quantity: int) -> dict:
        """
        Initialize a Stars purchase request.

        Args:
            recipient: Recipient ID from search_stars_recipient().
            quantity: Number of Stars to purchase (minimum 50).

        Returns:
            Dictionary containing:
                - req_id: Request ID for get_buy_stars_link()
                - amount: Price in TON

        Raises:
            ValueError: If quantity is less than 50.
            PriceChangedError: If price changed, retry recommended.
        """
        if quantity < 50:
            raise ValueError("Minimum quantity is 50 stars")

        return await self._make_request({
            "method": "initBuyStarsRequest",
            "recipient": recipient,
            "quantity": quantity,
        })

    async def get_buy_stars_link(
        self,
        id: str,
        account: dict,
        device: dict = None,
        transaction: str = "1",
        show_sender: bool = False,
    ) -> dict:
        """
        Get transaction details for Stars purchase.

        Args:
            id: Request ID from init_buy_stars_request().
            account: Wallet account details with keys:
                - address: Wallet address (required)
                - chain: Chain ID (optional, default: "-239")
            device: Device information (optional, uses default Tonkeeper config).
            transaction: Transaction ID (default: "1").
            show_sender: Whether to show sender in transaction.

        Returns:
            Dictionary containing transaction details:
                - transaction: {messages: [{address, amount, payload}]}
        """
        # Set default chain if not provided
        account_data = {"chain": self.DEFAULT_CHAIN, **account}
        device_data = device or self.DEFAULT_DEVICE

        return await self._make_request({
            "method": "getBuyStarsLink",
            "id": id,
            "account": json.dumps(account_data),
            "device": json.dumps(device_data),
            "transaction": transaction,
            "show_sender": "1" if show_sender else "0",
        })

    # ==================== Telegram Premium Methods ====================

    async def search_premium_gift_recipient(self, query: str) -> dict:
        """
        Search for a Telegram user to gift Premium to.

        Args:
            query: Telegram username (without @).

        Returns:
            Dictionary containing:
                - found: {recipient, name, photo, myself}

        Raises:
            InvalidRecipientError: If user not found.
        """
        return await self._make_request({
            "method": "searchPremiumGiftRecipient",
            "query": query,
        })

    async def init_gift_premium_request(self, recipient: str, months: int) -> dict:
        """
        Initialize a Premium gift purchase request.

        Args:
            recipient: Recipient ID from search_premium_gift_recipient().
            months: Duration - 3, 6, or 12 months.

        Returns:
            Dictionary containing:
                - req_id: Request ID for get_gift_premium_link()
                - amount: Price in TON

        Raises:
            PriceChangedError: If price changed, retry recommended.
            ValueError: If months is not 3, 6, or 12.
        """
        if months not in (3, 6, 12):
            raise ValueError("months must be 3, 6, or 12")

        return await self._make_request({
            "method": "initGiftPremiumRequest",
            "recipient": recipient,
            "months": months,
        })

    async def get_gift_premium_link(
        self,
        id: str,
        account: dict,
        device: dict = None,
        transaction: str = "1",
        show_sender: bool = False,
    ) -> dict:
        """
        Get transaction details for Premium gift purchase.

        Args:
            id: Request ID from init_gift_premium_request().
            account: Wallet account details (see get_buy_stars_link).
            device: Device information (optional, uses default Tonkeeper config).
            transaction: Transaction ID (default: "1").
            show_sender: Whether to show sender in transaction.

        Returns:
            Dictionary containing transaction details:
                - transaction: {messages: [{address, amount, payload}]}
        """
        account_data = {"chain": self.DEFAULT_CHAIN, **account}
        device_data = device or self.DEFAULT_DEVICE

        return await self._make_request({
            "method": "getGiftPremiumLink",
            "id": id,
            "account": json.dumps(account_data),
            "device": json.dumps(device_data),
            "transaction": transaction,
            "show_sender": "1" if show_sender else "0",
        })

    # ==================== TON Topup Methods ====================

    async def search_ads_topup_recipient(self, query: str) -> dict:
        """
        Search for a Telegram user for TON balance topup.

        Args:
            query: Telegram username (without @).

        Returns:
            Dictionary containing:
                - found: {recipient, name, photo, myself}

        Raises:
            InvalidRecipientError: If user not found.
        """
        return await self._make_request({
            "method": "searchAdsTopupRecipient",
            "hash": self.fragment_hash,
            "query": query,
        })

    async def init_ads_topup_request(self, recipient: str, amount: int) -> dict:
        """
        Initialize a TON topup request.

        Args:
            recipient: Recipient ID from search_ads_topup_recipient().
            amount: Amount in TON (whole number, minimum 1).

        Returns:
            Dictionary containing:
                - ok: True if successful
                - req_id: Request ID for get_ads_topup_link()

        Raises:
            ValueError: If amount is less than 1 or not a whole number.
        """
        # Validate amount is a whole number
        if not isinstance(amount, int):
            if isinstance(amount, float) and not amount.is_integer():
                raise ValueError("Amount must be a whole number (no decimals)")
            amount = int(amount)

        if amount < 1:
            raise ValueError("Minimum topup amount is 1 TON")

        return await self._make_request({
            "method": "initAdsTopupRequest",
            "hash": self.fragment_hash,
            "recipient": recipient,
            "amount": str(amount),
        })

    async def get_ads_topup_link(
        self,
        id: str,
        account: dict,
        device: dict = None,
        transaction: str = "1",
        show_sender: bool = False,
    ) -> dict:
        """
        Get transaction details for TON topup.

        Args:
            id: Request ID from init_ads_topup_request().
            account: Wallet account details (see get_buy_stars_link).
            device: Device information (optional, uses default Tonkeeper config).
            transaction: Transaction ID (default: "1").
            show_sender: Whether to show sender in transaction.

        Returns:
            Dictionary containing transaction details:
                - transaction: {messages: [{address, amount, payload}]}
        """
        account_data = {"chain": self.DEFAULT_CHAIN, **account}
        device_data = device or self.DEFAULT_DEVICE

        return await self._make_request({
            "method": "getAdsTopupLink",
            "id": id,
            "account": json.dumps(account_data),
            "device": json.dumps(device_data),
            "transaction": transaction,
            "show_sender": "1" if show_sender else "0",
        })

    # ==================== High-Level Convenience Methods ====================

    async def buy_stars(
        self,
        username: str,
        quantity: int,
        wallet_address: str,
        show_sender: bool = False,
    ) -> dict:
        """
        Purchase Telegram Stars in one call.

        Combines search_stars_recipient, init_buy_stars_request, and 
        get_buy_stars_link into a single convenient method.

        Args:
            username: Telegram username (without @).
            quantity: Number of Stars to purchase (minimum 50).
            wallet_address: Your TON wallet address for payment.
            show_sender: Whether to show sender in transaction.

        Returns:
            Dictionary containing:
                - recipient: Recipient information (name, photo)
                - amount: Price in TON (nanotons)
                - transaction: Transaction details with messages:
                    - address: Where to send TON
                    - amount: How much to send (nanotons)
                    - payload: Transaction payload

        Example:
            result = await client.buy_stars("durov", 100, "UQ...")
            address = result["transaction"]["messages"][0]["address"]
            amount = result["transaction"]["messages"][0]["amount"]
        """
        # Step 1: Search for recipient
        search_result = await self.search_stars_recipient(username, quantity)
        recipient_id = search_result["found"]["recipient"]
        recipient_info = {
            "name": search_result["found"].get("name"),
            "photo": search_result["found"].get("photo"),
        }

        # Step 2: Initialize purchase request
        init_result = await self.init_buy_stars_request(recipient_id, quantity)
        req_id = init_result["req_id"]
        amount = init_result.get("amount")

        # Step 3: Get transaction details
        account = {"address": wallet_address}
        link_result = await self.get_buy_stars_link(
            req_id, account, show_sender=show_sender
        )

        return {
            "recipient": recipient_info,
            "amount": amount,
            "transaction": link_result.get("transaction"),
        }

    async def buy_premium(
        self,
        username: str,
        months: int,
        wallet_address: str,
        show_sender: bool = False,
    ) -> dict:
        """
        Gift Telegram Premium in one call.

        Combines search_premium_gift_recipient, init_gift_premium_request, 
        and get_gift_premium_link into a single convenient method.

        Args:
            username: Telegram username (without @).
            months: Duration - 3, 6, or 12 months.
            wallet_address: Your TON wallet address for payment.
            show_sender: Whether to show sender in transaction.

        Returns:
            Dictionary containing:
                - recipient: Recipient information (name, photo)
                - amount: Price in TON (nanotons)
                - transaction: Transaction details with messages:
                    - address: Where to send TON
                    - amount: How much to send (nanotons)
                    - payload: Transaction payload

        Example:
            result = await client.buy_premium("durov", 12, "UQ...")
            address = result["transaction"]["messages"][0]["address"]
            amount = result["transaction"]["messages"][0]["amount"]
        """
        # Step 1: Search for recipient
        search_result = await self.search_premium_gift_recipient(username)
        recipient_id = search_result["found"]["recipient"]
        recipient_info = {
            "name": search_result["found"].get("name"),
            "photo": search_result["found"].get("photo"),
        }

        # Step 2: Initialize purchase request
        init_result = await self.init_gift_premium_request(recipient_id, months)
        req_id = init_result["req_id"]
        amount = init_result.get("amount")

        # Step 3: Get transaction details
        account = {"address": wallet_address}
        link_result = await self.get_gift_premium_link(
            req_id, account, show_sender=show_sender
        )

        return {
            "recipient": recipient_info,
            "amount": amount,
            "transaction": link_result.get("transaction"),
        }

    async def buy_ton_topup(
        self,
        username: str,
        amount: int,
        wallet_address: str,
        show_sender: bool = False,
    ) -> dict:
        """
        TON balance topup in one call.

        Combines search_ads_topup_recipient, init_ads_topup_request, 
        and get_ads_topup_link into a single convenient method.

        Args:
            username: Telegram username (without @).
            amount: Amount in TON (whole number, minimum 1).
            wallet_address: Your TON wallet address for payment.
            show_sender: Whether to show sender in transaction.

        Returns:
            Dictionary containing:
                - recipient: Recipient information (name, photo)
                - amount: Requested topup amount in TON
                - transaction: Transaction details with messages:
                    - address: Where to send TON
                    - amount: How much to send (nanotons)
                    - payload: Transaction payload

        Example:
            result = await client.buy_ton_topup("durov", 10, "UQ...")
            address = result["transaction"]["messages"][0]["address"]
            tx_amount = result["transaction"]["messages"][0]["amount"]
        """
        # Step 1: Search for recipient
        search_result = await self.search_ads_topup_recipient(username)
        recipient_id = search_result["found"]["recipient"]
        recipient_info = {
            "name": search_result["found"].get("name"),
            "photo": search_result["found"].get("photo"),
        }

        # Step 2: Initialize topup request
        init_result = await self.init_ads_topup_request(recipient_id, amount)
        req_id = init_result["req_id"]

        # Step 3: Get transaction details
        account = {"address": wallet_address}
        link_result = await self.get_ads_topup_link(
            req_id, account, show_sender=show_sender
        )

        return {
            "recipient": recipient_info,
            "amount": amount,
            "transaction": link_result.get("transaction"),
        }



