from typing import Dict, List, Optional, Callable
import aiohttp
import requests
import logging
import pandas as pd
from datetime import datetime
import websockets
import asyncio
import json
import time
from collections import deque
from .interfaces import TradeClient
import random

logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiter implementation with token bucket algorithm."""
    
    def __init__(self, rate: int, max_tokens: int):
        self.rate = rate  # tokens per second
        self.max_tokens = max_tokens
        self.tokens = max_tokens
        self.last_update = time.monotonic()
        self.lock = asyncio.Lock()
    
    async def acquire(self):
        """Acquire a token, waiting if necessary."""
        async with self.lock:
            now = time.monotonic()
            time_passed = now - self.last_update
            self.tokens = min(
                self.max_tokens,
                self.tokens + time_passed * self.rate
            )
            self.last_update = now
            
            if self.tokens < 1:
                wait_time = (1 - self.tokens) / self.rate
                await asyncio.sleep(wait_time)
                self.tokens = 0
                self.last_update = time.monotonic()
            else:
                self.tokens -= 1

class RequestQueue:
    """Async request queue with prioritization."""
    
    def __init__(self, max_size: int = 1000):
        self.queue = deque(maxlen=max_size)
        self.lock = asyncio.Lock()
        self.not_empty = asyncio.Event()
    
    async def put(self, request: Dict, priority: int = 0):
        """Add request to queue with priority (lower number = higher priority)."""
        async with self.lock:
            self.queue.append((priority, time.monotonic(), request))
            self.queue = deque(sorted(self.queue, key=lambda x: (x[0], x[1])), 
                             maxlen=self.queue.maxlen)
            self.not_empty.set()
    
    async def get(self) -> Dict:
        """Get next request from queue."""
        await self.not_empty.wait()
        async with self.lock:
            if not self.queue:
                self.not_empty.clear()
                raise asyncio.QueueEmpty()
            return self.queue.popleft()[2]

class RetryConfig:
    """Configuration for request retry behavior."""
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0,
                 max_delay: float = 10.0, jitter: float = 0.1):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.jitter = jitter

class TradeLockerClient(TradeClient):
    """TradeLocker API client implementation with real-time data streaming support."""
    
    def __init__(self, api_key: str, api_secret: str):
        """Initialize TradeLocker client."""
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api.tradelocker.com"  # Replace with actual API URL
        self.ws_url = "wss://stream.tradelocker.com"   # Replace with actual WebSocket URL
        self.session = requests.Session()
        self.token = None
        self.is_connected = False
        self.account_info = {}
        
        # WebSocket related
        self.ws = None
        self.ws_task = None
        self.ws_keepalive_task = None
        self.market_data_callbacks = []
        self.order_update_callbacks = []
        self._ws_reconnect_delay = 1
        self._ws_max_reconnect_delay = 60
        self._ws_last_msg_time = 0
        self._ws_heartbeat_interval = 30
        self._ws_subscriptions = set()
        
        # Rate limiting and request queuing
        self.rate_limiter = RateLimiter(rate=10, max_tokens=100)
        self.request_queue = RequestQueue()
        self.request_processor_task = None
        
        # Error tracking
        self.error_counts = {}
        self.last_error_reset = time.monotonic()
        self.ERROR_THRESHOLD = 50
        self.ERROR_RESET_INTERVAL = 3600
        
        # Add retry configuration
        self.retry_config = RetryConfig()
        
        # Add session refresh configuration
        self.token_refresh_task = None
        self.token_refresh_interval = 3600  # 1 hour
        self.token_expires_at = None
        
    async def _process_request_queue(self):
        """Process queued requests with rate limiting."""
        while True:
            try:
                request = await self.request_queue.get()
                await self.rate_limiter.acquire()
                
                method = request.get("method", "GET")
                url = request.get("url")
                kwargs = request.get("kwargs", {})
                
                async with aiohttp.ClientSession() as session:
                    async with session.request(method, url, **kwargs) as response:
                        if response.status == 429:  # Too Many Requests
                            retry_after = int(response.headers.get("Retry-After", 5))
                            logger.warning(f"Rate limit hit, waiting {retry_after} seconds")
                            await asyncio.sleep(retry_after)
                            await self.request_queue.put(request, priority=0)  # Retry with high priority
                        else:
                            return await response.json()
                            
            except Exception as e:
                logger.error(f"Error processing request: {str(e)}")
                await asyncio.sleep(1)
    
    async def _make_request(self, method: str, endpoint: str, priority: int = 1, **kwargs) -> Dict:
        """Make an API request with retries and error handling."""
        if not self.is_connected and endpoint != "/auth/login":
            raise Exception("Not connected to TradeLocker")
            
        url = f"{self.base_url}{endpoint}"
        request = {
            "method": method,
            "url": url,
            "kwargs": kwargs
        }
        
        # Track error rates
        current_time = time.monotonic()
        if current_time - self.last_error_reset > self.ERROR_RESET_INTERVAL:
            self.error_counts.clear()
            self.last_error_reset = current_time
            
        endpoint_errors = self.error_counts.get(endpoint, 0)
        if endpoint_errors >= self.ERROR_THRESHOLD:
            raise Exception(f"Endpoint {endpoint} temporarily suspended due to high error rate")
        
        retries = 0
        last_exception = None
        
        while retries <= self.retry_config.max_retries:
            try:
                await self.request_queue.put(request, priority)
                response = await self._process_request_queue()
                
                # Reset error count on success
                if endpoint in self.error_counts:
                    self.error_counts[endpoint] = max(0, self.error_counts[endpoint] - 1)
                    
                return self._process_response(response)
                
            except aiohttp.ClientError as e:
                last_exception = e
                if isinstance(e, aiohttp.ClientResponseError):
                    if e.status == 401 and endpoint != "/auth/login":
                        # Token might be expired, try to refresh
                        try:
                            await self._refresh_token()
                            continue  # Retry with new token
                        except Exception as refresh_error:
                            logger.error(f"Token refresh failed: {str(refresh_error)}")
                            
                    elif e.status == 429:  # Rate limit hit
                        retry_after = int(e.headers.get("Retry-After", 5))
                        await asyncio.sleep(retry_after)
                        continue
                        
                    elif e.status >= 500:  # Server error, retry
                        pass
                    else:
                        # Client error, don't retry
                        raise
                        
            except Exception as e:
                last_exception = e
                
            # Calculate retry delay with exponential backoff and jitter
            delay = min(
                self.retry_config.base_delay * (2 ** retries),
                self.retry_config.max_delay
            )
            jitter = random.uniform(
                -self.retry_config.jitter * delay,
                self.retry_config.jitter * delay
            )
            await asyncio.sleep(delay + jitter)
            
            retries += 1
            
        # Update error count after all retries failed
        self.error_counts[endpoint] = endpoint_errors + 1
        
        if last_exception:
            raise last_exception
        raise Exception("Max retries exceeded")

    def _process_response(self, response: Dict) -> Dict:
        """Process and validate API response."""
        if not isinstance(response, dict):
            raise ValueError("Invalid response format")
            
        if "error" in response:
            error_msg = response["error"]
            if isinstance(error_msg, dict):
                error_msg = error_msg.get("message", str(error_msg))
            raise Exception(f"API error: {error_msg}")
            
        return response

    async def _refresh_token(self):
        """Refresh authentication token."""
        if not self.token:
            raise ValueError("No token to refresh")
            
        try:
            response = await self._make_request(
                "POST",
                "/auth/refresh",
                priority=0,  # High priority for token refresh
                json={"refresh_token": self.token}
            )
            
            if "access_token" in response:
                self.token = response["access_token"]
                self.token_expires_at = time.monotonic() + self.token_refresh_interval
                logger.info("Successfully refreshed authentication token")
            else:
                raise ValueError("Invalid token refresh response")
                
        except Exception as e:
            logger.error(f"Failed to refresh token: {str(e)}")
            raise

    async def _start_token_refresh_task(self):
        """Start background task for token refresh."""
        while True:
            try:
                if self.token_expires_at:
                    time_until_refresh = self.token_expires_at - time.monotonic()
                    if time_until_refresh > 0:
                        await asyncio.sleep(time_until_refresh)
                    await self._refresh_token()
                else:
                    await asyncio.sleep(60)  # Check every minute if no expiry set
                    
            except Exception as e:
                logger.error(f"Error in token refresh task: {str(e)}")
                await asyncio.sleep(60)  # Wait before retrying

    async def connect(self, credentials: Dict) -> bool:
        """Connect to TradeLocker platform."""
        try:
            # Authenticate
            response = await self._make_request(
                "POST",
                "/auth/login",
                json={
                    "api_key": self.api_key,
                    "api_secret": self.api_secret,
                    **credentials
                }
            )
            
            if "access_token" not in response:
                raise ValueError("Authentication failed")
                
            self.token = response["access_token"]
            self.token_expires_at = time.monotonic() + self.token_refresh_interval
            
            # Start background tasks
            self.request_processor_task = asyncio.create_task(self._process_request_queue())
            self.token_refresh_task = asyncio.create_task(self._start_token_refresh_task())
            
            # Initialize WebSocket connection
            self.ws_task = asyncio.create_task(self._maintain_websocket_connection())
            
            self.is_connected = True
            logger.info("Successfully connected to TradeLocker")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to TradeLocker: {str(e)}")
            return False

    async def get_account_info(self) -> Dict:
        """Get account information."""
        try:
            response = await self._make_request("GET", "/account/info")
            self.account_info = response
            return response
            
        except Exception as e:
            logger.error(f"Error getting account info: {str(e)}")
            return {}

    async def get_positions(self) -> List[Dict]:
        """Get current positions."""
        try:
            response = await self._make_request("GET", "/positions")
            return response.get("positions", [])
            
        except Exception as e:
            logger.error(f"Error getting positions: {str(e)}")
            return []

    async def place_order(self, order: Dict) -> Dict:
        """Place a new order."""
        try:
            # Validate order parameters
            required_fields = ["symbol", "type", "side", "size"]
            if not all(field in order for field in required_fields):
                raise ValueError("Missing required order fields")
                
            response = await self._make_request(
                "POST",
                "/orders",
                priority=0,  # High priority for order placement
                json=order
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error placing order: {str(e)}")
            return {"error": str(e)}

    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an existing order."""
        try:
            await self._make_request(
                "DELETE",
                f"/orders/{order_id}",
                priority=0  # High priority for order cancellation
            )
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {str(e)}")
            return False

    async def get_order_status(self, order_id: str) -> Dict:
        """Get order status."""
        try:
            response = await self._make_request(
                "GET",
                f"/orders/{order_id}"
            )
            return response
            
        except Exception as e:
            logger.error(f"Error getting order status for {order_id}: {str(e)}")
            return {}

    async def get_historical_data(self, symbol: str, timeframe: str, limit: int = 100) -> pd.DataFrame:
        """Get historical market data."""
        try:
            response = await self._make_request(
                "GET",
                "/market/history",
                params={
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "limit": limit
                }
            )
            
            if "data" in response:
                df = pd.DataFrame(response["data"])
                df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
                df.set_index("timestamp", inplace=True)
                return df
                
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Error getting historical data: {str(e)}")
            return pd.DataFrame()

    async def get_server_time(self) -> Optional[datetime]:
        """Get server time for synchronization."""
        try:
            response = await self._make_request(
                "GET",
                "/time"
            )
            
            if "timestamp" in response:
                return datetime.fromtimestamp(response["timestamp"] / 1000)
            return None
            
        except Exception as e:
            logger.error(f"Error getting server time: {str(e)}")
            return None

    async def get_order_book(self, symbol: str) -> Dict:
        """Get order book data."""
        try:
            response = await self._make_request(
                "GET",
                "/market/orderbook",
                params={"symbol": symbol}
            )
            
            if "bids" in response and "asks" in response:
                return {
                    "bids": [
                        {"price": float(bid[0]), "size": float(bid[1])}
                        for bid in response["bids"]
                    ],
                    "asks": [
                        {"price": float(ask[0]), "size": float(ask[1])}
                        for ask in response["asks"]
                    ],
                    "timestamp": datetime.fromtimestamp(
                        response.get("timestamp", time.time() * 1000) / 1000
                    )
                }
                
            return {}
            
        except Exception as e:
            logger.error(f"Error getting order book for {symbol}: {str(e)}")
            return {}

    async def _maintain_websocket_connection(self):
        """Maintain WebSocket connection with automatic reconnection."""
        while True:
            try:
                async with websockets.connect(self.ws_url) as websocket:
                    self.ws = websocket
                    self._ws_reconnect_delay = 1  # Reset reconnect delay
                    
                    # Authenticate WebSocket
                    await self._ws_authenticate()
                    
                    # Start keepalive task
                    self.ws_keepalive_task = asyncio.create_task(self._ws_keepalive())
                    
                    # Resubscribe to previous subscriptions
                    for subscription in self._ws_subscriptions:
                        await self._ws_subscribe(subscription)
                        
                    # Handle messages
                    await self._handle_ws_messages()
                    
            except Exception as e:
                logger.error(f"WebSocket error: {str(e)}")
                
                if self.ws_keepalive_task:
                    self.ws_keepalive_task.cancel()
                    
                # Exponential backoff for reconnection
                await asyncio.sleep(self._ws_reconnect_delay)
                self._ws_reconnect_delay = min(
                    self._ws_reconnect_delay * 2,
                    self._ws_max_reconnect_delay
                )

    async def _ws_authenticate(self):
        """Authenticate WebSocket connection."""
        if not self.token:
            raise ValueError("No authentication token available")
            
        auth_message = {
            "type": "auth",
            "token": self.token
        }
        
        await self.ws.send(json.dumps(auth_message))
        response = await self.ws.recv()
        
        if not json.loads(response).get("authenticated"):
            raise Exception("WebSocket authentication failed")

    async def _ws_keepalive(self):
        """Send keepalive messages to maintain WebSocket connection."""
        while True:
            try:
                if time.monotonic() - self._ws_last_msg_time > self._ws_heartbeat_interval:
                    await self.ws.send(json.dumps({"type": "ping"}))
                await asyncio.sleep(self._ws_heartbeat_interval)
                
            except Exception as e:
                logger.error(f"WebSocket keepalive error: {str(e)}")
                break

    async def _handle_ws_messages(self):
        """Handle incoming WebSocket messages."""
        while True:
            try:
                message = await self.ws.recv()
                self._ws_last_msg_time = time.monotonic()
                
                data = json.loads(message)
                message_type = data.get("type")
                
                if message_type == "market_data":
                    for callback in self.market_data_callbacks:
                        await callback(data["data"])
                        
                elif message_type == "order_update":
                    for callback in self.order_update_callbacks:
                        await callback(data["data"])
                        
                elif message_type == "pong":
                    continue
                    
                else:
                    logger.warning(f"Unknown message type: {message_type}")
                    
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {str(e)}")
                break

    async def subscribe_market_data(self, symbol: str, callback: Callable):
        """Subscribe to market data updates."""
        self.market_data_callbacks.append(callback)
        await self._ws_subscribe(f"market_data_{symbol}")

    async def _ws_subscribe(self, subscription: str):
        """Send subscription message over WebSocket."""
        if self.ws:
            await self.ws.send(json.dumps({
                "type": "subscribe",
                "channel": subscription
            }))
            self._ws_subscriptions.add(subscription) 