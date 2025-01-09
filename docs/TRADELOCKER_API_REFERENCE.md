# TradeLocker API Reference

## Authentication
Base URL: `https://{server}.tradelocker.com`

### Login
```http
POST /auth/login
Content-Type: application/json

{
    "email": "user@example.com",
    "password": "your_password",
    "server": "server_identifier"
}
```

Response:
```json
{
    "success": true,
    "sessionToken": "your_session_token",
    "expiresAt": 1704838800000,
    "permissions": ["trade", "view", "manage"]
}
```

## Market Data

### Get Real-time Prices
```http
GET /market/prices/{symbol}
Authorization: Bearer {session_token}
```

### Get Order Book
```http
GET /market/orderbook/{symbol}
Authorization: Bearer {session_token}
```

### Get Historical Data
```http
GET /market/historical/{symbol}/{timeframe}
Authorization: Bearer {session_token}
```

Parameters:
- timeframe: 1m, 5m, 15m, 30m, 1h, 4h, 1d

## Trading

### Place Order
```http
POST /orders/place
Authorization: Bearer {session_token}
Content-Type: application/json

{
    "symbol": "BTCUSD",
    "side": "BUY",
    "type": "LIMIT",
    "quantity": 1.0,
    "price": 45000,
    "timeInForce": "GTC"
}
```

### Cancel Order
```http
POST /orders/cancel/{order_id}
Authorization: Bearer {session_token}
```

### Get Order Status
```http
GET /orders/status/{order_id}
Authorization: Bearer {session_token}
```

## Account

### Get Account Info
```http
GET /account/info
Authorization: Bearer {session_token}
```

### Get Balance
```http
GET /account/balance
Authorization: Bearer {session_token}
```

### Get Trade History
```http
GET /account/trades
Authorization: Bearer {session_token}
```

## WebSocket API

### Connection
```
wss://{server}.tradelocker.com/ws/{session_token}
```

### Subscribe to Market Data
```json
{
    "action": "subscribe",
    "channel": "market",
    "symbol": "BTCUSD",
    "type": "price"  // or "orderbook" or "trades"
}
```

### Subscribe to Account Updates
```json
{
    "action": "subscribe",
    "channel": "account",
    "type": "orders"  // or "positions" or "balance"
}
```

## Rate Limits
- REST API: 10 requests/second, burst up to 100 requests/minute
- WebSocket: 100 subscriptions per connection
- Maximum 10 concurrent WebSocket connections

## Error Codes
- 1001: Authentication failed
- 1002: Rate limit exceeded
- 1003: Invalid parameters
- 1004: Insufficient balance
- 1005: Order not found
- 1006: Invalid session
- 1007: Server maintenance
- 1008: Market closed
- 1009: Invalid symbol
- 1010: Trading suspended

## Best Practices
1. Session Management
   - Store session token securely
   - Refresh before expiration
   - Handle session invalidation

2. Rate Limiting
   - Implement exponential backoff
   - Queue non-critical requests
   - Monitor rate limit headers

3. Error Handling
   - Implement retry logic
   - Log all errors
   - Handle connection loss

4. WebSocket Usage
   - Maintain heartbeat
   - Implement auto-reconnection
   - Buffer during reconnection

5. Security
   - Use HTTPS/WSS only
   - Never log credentials
   - Validate all responses 