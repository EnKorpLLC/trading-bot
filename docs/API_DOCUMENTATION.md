# API Documentation

## Database Configuration
- Platform: Neon (Serverless PostgreSQL)
- Connection: Environment variable based
- Status: Pending setup

## Environment Variables
```env
# Database
DATABASE_URL=postgresql://user:password@host:port/database

# API Endpoints
NEXT_PUBLIC_API_URL=https://api.example.com
NEXT_PUBLIC_WS_URL=wss://ws.example.com

# Authentication
JWT_SECRET=your-secret-key

# TradeLocker Integration
TRADELOCKER_SERVER=default-server.tradelocker.com  # Default server
```

## API Endpoints

### 1. Trading (via TradeLocker)
```http
# Authentication
POST /api/tradelocker/auth/login    # Login to TradeLocker
{
    "email": "user@example.com",
    "password": "secure_password",
    "server": "server_identifier"
}

# Trading Operations
POST /api/trading/order          # Submit new order
GET /api/trading/positions       # Get current positions
GET /api/trading/history         # Get trade history
GET /api/trading/prices          # Get price data

# TradeLocker Account Management
POST /api/tradelocker/connect    # Connect TradeLocker account
GET /api/tradelocker/status     # Get connection status
POST /api/tradelocker/logout    # Logout from TradeLocker
GET /api/tradelocker/session    # Get session status
```

### 2. Order Types Supported
```typescript
enum OrderType {
  MARKET = 'MARKET',
  LIMIT = 'LIMIT',
  STOP = 'STOP',
  STOP_LIMIT = 'STOP_LIMIT',
  TRAILING_STOP = 'TRAILING_STOP'
}
```

### 3. Position Management
```http
GET /api/positions/current      # Get current positions
GET /api/positions/history      # Get position history
POST /api/positions/close      # Close position
```

### 4. Market Data
```http
GET /api/market/prices         # Get real-time prices
GET /api/market/chart          # Get chart data
GET /api/market/orderbook     # Get order book data
GET /api/market/trades        # Get recent trades
```

## Risk Management Endpoints

### Get User Risk Settings
```http
GET /api/trading/risk-settings
```
Returns the current risk management settings for the authenticated user.

Response:
```json
{
    "maxPositionSize": 0.1,     // 10% of account balance
    "maxDailyLoss": 0.02,       // 2% max daily loss
    "maxDrawdown": 0.1,         // 10% max drawdown
    "maxLeverage": 3,           // 3x max leverage
    "positionLimit": 5,         // Maximum open positions
    "maxCorrelation": 0.7,      // 70% correlation limit
    "riskPerTrade": 0.01        // 1% risk per trade
}
```

### Update User Risk Settings
```http
PUT /api/trading/risk-settings
```
Updates the risk management settings for the authenticated user.

Request Body:
```json
{
    "maxPositionSize": 0.15,    // Optional: Update to 15%
    "maxDailyLoss": 0.03,       // Optional: Update to 3%
    "riskPerTrade": 0.02        // Optional: Update to 2%
    // Any subset of risk parameters can be updated
}
```

Response:
```json
{
    "success": true,
    "message": "Risk settings updated successfully",
    "settings": {
        // Updated risk settings object
    }
}
```

### Validate Order Risk
```http
POST /api/trading/validate-order
```
Validates an order against the user's risk management settings.

Request Body:
```json
{
    "order": {
        "symbol": "BTC-USD",
        "side": "BUY",
        "type": "LIMIT",
        "quantity": 1.0,
        "price": 45000,
        "stopPrice": 44000
    },
    "accountBalance": 100000
}
```

Response:
```json
{
    "isValid": true,
    "messages": [],
    "metrics": {
        "currentRisk": 0.01,          // 1% current risk
        "exposurePercentage": 0.05,   // 5% exposure
        "marginUsage": 5000,          // $5000 margin used
        "availableMargin": 95000      // $95000 available
    }
}
```

## WebSocket Events

### 1. Market Updates
```typescript
// TradeLocker market data
market.price.{symbol}           // Real-time price updates
market.orderbook.{symbol}       // Order book updates
market.trades.{symbol}          // Recent trades

// Aggregated market data
market:price
market:indicator
market:alert
```

### 2. Trading Events
```typescript
// TradeLocker events
tradelocker.order.{accountId}   // Order status updates
tradelocker.position.{accountId} // Position updates
tradelocker.balance.{accountId} // Balance updates

// General trading events
trade:executed
trade:pending
trade:cancelled
```

### 3. System Events
```typescript
system:status
system:error
system:maintenance
tradelocker:connection         // TradeLocker connection status
```

## Error Handling
```typescript
interface ApiError {
  code: number;
  message: string;
  details?: any;
}

// TradeLocker specific errors
interface TradeLockerError extends ApiError {
  tradelocker_code: string;
  retry_after?: number;
}
```

## Rate Limiting
- Standard API: 100 requests per minute
- TradeLocker API: 10 requests per second, 100 per minute
- WebSocket: 10 connections per user
- Database: Connection pooling configured

## Security
- JWT Authentication
- TradeLocker API key encryption
- HTTPS Only
- CORS Configuration
- Rate Limiting
- Input Validation

## Database Schema
```sql
-- Users
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trading History
CREATE TABLE trades (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id),
  symbol VARCHAR(10) NOT NULL,
  type VARCHAR(4) NOT NULL,
  amount DECIMAL NOT NULL,
  price DECIMAL NOT NULL,
  status VARCHAR(10) NOT NULL,
  executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Settings
CREATE TABLE user_settings (
  user_id INTEGER REFERENCES users(id),
  setting_key VARCHAR(50) NOT NULL,
  setting_value JSON NOT NULL,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (user_id, setting_key)
);

-- TradeLocker Integration
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

## Next Steps
1. Database Setup
   - Initialize Neon instance
   - Configure connection pooling
   - Set up migrations
   - Create initial schemas

2. API Implementation
   - Set up Next.js API routes
   - Implement authentication
   - Add WebSocket support
   - Configure error handling
   - Complete TradeLocker integration

3. Testing
   - Unit tests for API routes
   - Integration tests with TradeLocker
   - Load testing
   - Security testing 