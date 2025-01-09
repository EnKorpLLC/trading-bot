# TradeLocker Integration

## Overview
TradeLocker provides the core trading functionality for our application, handling order execution, market data, and position management.

## Authentication
```typescript
interface TradeLockerCredentials {
  email: string;
  password: string;
  server: string;  // TradeLocker server identifier
}
```

Environment variables:
```env
TRADELOCKER_SERVER=your-server-url  # Default server if not specified by user
```

Authentication Flow:
1. User provides their TradeLocker credentials (email, password, server)
2. Application securely transmits credentials to TradeLocker
3. TradeLocker validates credentials and returns session token
4. Application stores encrypted session token for subsequent requests
5. Regular session refresh to maintain connection

Security Notes:
- Credentials are never stored locally
- Only encrypted session tokens are persisted
- Automatic session renewal before expiration
- Immediate token invalidation on logout

## API Endpoints
Base URL: `https://{server}.tradelocker.com`  // Server URL is dynamic based on user's server

### Authentication
```http
POST /auth/login
{
    "email": "user@example.com",
    "password": "secure_password",
    "server": "server_identifier"
}
```

### Market Data
```http
GET /market/prices/{symbol}
GET /market/orderbook/{symbol}
GET /market/historical/{symbol}/{timeframe}
```

### Trading
```http
POST /orders/place
POST /orders/cancel/{order_id}
GET /orders/status/{order_id}
GET /positions/current
```

### Account
```http
GET /account/info
GET /account/balance
GET /account/trades
```

## WebSocket Streams
WebSocket URL: `wss://stream.tradelocker.com`

### Available Streams
1. Market Data
   ```
   market.{symbol}.price
   market.{symbol}.orderbook
   market.{symbol}.trades
   ```

2. Account Updates
   ```
   account.orders
   account.positions
   account.balance
   ```

## Rate Limits
- REST API: 10 requests per second, 100 requests per minute
- WebSocket: Maximum 100 subscriptions per connection
- Connections: 10 concurrent WebSocket connections per account

## Error Handling
```typescript
interface TradeLockerError {
  code: number;
  message: string;
  data?: any;
}
```

Common error codes:
- 1001: Authentication failed
- 1002: Rate limit exceeded
- 1003: Invalid parameters
- 1004: Insufficient balance
- 1005: Order not found

## Implementation Details

### Client Configuration
The `TradeLockerClient` class handles all interactions with TradeLocker:
```python
client = TradeLockerClient(api_key, api_secret)
await client.connect()
```

### Request Queue
Requests are prioritized and rate-limited:
- Priority 0: Critical operations (order management)
- Priority 1: Account operations
- Priority 2: Market data requests

### WebSocket Management
- Automatic reconnection with exponential backoff
- Heartbeat every 30 seconds
- Subscription management and message routing

## Database Schema
```sql
CREATE TABLE tradelocker_accounts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    api_key VARCHAR(255) NOT NULL,
    api_secret_encrypted VARCHAR(255) NOT NULL,
    label VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP
);

CREATE TABLE tradelocker_orders (
    id SERIAL PRIMARY KEY,
    account_id INTEGER REFERENCES tradelocker_accounts(id),
    order_id VARCHAR(255) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(4) NOT NULL,
    type VARCHAR(10) NOT NULL,
    quantity DECIMAL NOT NULL,
    price DECIMAL,
    status VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Monitoring
Key metrics tracked:
- API response times
- WebSocket connection status
- Error rates by endpoint
- Order execution latency
- Market data latency

## Recovery Procedures
1. Connection Loss
   - Automatic reconnection with exponential backoff
   - Order status reconciliation on reconnect
   - Position verification

2. Rate Limit Exceeded
   - Request queuing with priorities
   - Exponential backoff
   - Alert on sustained rate limit issues

3. Data Inconsistency
   - Position reconciliation
   - Order status verification
   - Balance confirmation

## Security Considerations
1. API Key Storage
   - Keys stored encrypted in database
   - Secrets never logged or exposed
   - Regular key rotation recommended

2. Connection Security
   - TLS required for all connections
   - API key authentication
   - WebSocket connection authentication

3. Request Signing
   - All requests signed with API secret
   - Timestamp validation
   - Nonce tracking for replay protection 