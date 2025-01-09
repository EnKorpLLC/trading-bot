# Trading Bot API Documentation

## Authentication

All API endpoints except for authentication endpoints require a valid JWT token in the Authorization header.

```
Authorization: Bearer <token>
```

### Authentication Endpoints

#### POST /api/auth/register
Register a new user.

**Request Body:**
```json
{
    "email": "user@example.com",
    "password": "secure_password"
}
```

**Response:**
```json
{
    "token": "jwt_token",
    "user": {
        "id": "user_id",
        "email": "user@example.com",
        "createdAt": "2024-01-08T00:00:00Z"
    }
}
```

#### POST /api/auth/login
Login with existing credentials.

**Request Body:**
```json
{
    "email": "user@example.com",
    "password": "secure_password"
}
```

**Response:**
```json
{
    "token": "jwt_token",
    "user": {
        "id": "user_id",
        "email": "user@example.com",
        "createdAt": "2024-01-08T00:00:00Z"
    }
}
```

## Trading Endpoints

### Orders

#### POST /api/trading/orders
Place a new order.

**Request Body:**
```json
{
    "symbol": "BTCUSDT",
    "side": "buy",
    "type": "market",
    "quantity": 1.0,
    "price": 50000.00,
    "stopPrice": 49000.00
}
```

**Response:**
```json
{
    "id": "order_id",
    "symbol": "BTCUSDT",
    "side": "buy",
    "type": "market",
    "status": "pending",
    "quantity": 1.0,
    "price": 50000.00,
    "filledQuantity": 0,
    "remainingQuantity": 1.0,
    "timestamp": "2024-01-08T00:00:00Z"
}
```

#### GET /api/trading/orders
Get list of orders.

**Query Parameters:**
- status (optional): Filter by order status (pending, filled, cancelled)

**Response:**
```json
[
    {
        "id": "order_id",
        "symbol": "BTCUSDT",
        "side": "buy",
        "type": "market",
        "status": "filled",
        "quantity": 1.0,
        "price": 50000.00,
        "filledQuantity": 1.0,
        "remainingQuantity": 0,
        "timestamp": "2024-01-08T00:00:00Z"
    }
]
```

#### POST /api/trading/orders/:orderId/cancel
Cancel an existing order.

**Response:**
```json
{
    "id": "order_id",
    "status": "cancelled"
}
```

### Positions

#### GET /api/trading/positions
Get current positions.

**Response:**
```json
[
    {
        "symbol": "BTCUSDT",
        "quantity": 1.0,
        "averagePrice": 50000.00,
        "currentPrice": 51000.00,
        "pnl": 1000.00
    }
]
```

### Trades

#### GET /api/trading/trades
Get trade history.

**Query Parameters:**
- symbol (optional): Filter by trading pair
- limit (optional): Number of trades to return (default: 50)
- offset (optional): Pagination offset

**Response:**
```json
[
    {
        "id": "trade_id",
        "symbol": "BTCUSDT",
        "side": "buy",
        "type": "market",
        "quantity": 1.0,
        "price": 50000.00,
        "timestamp": "2024-01-08T00:00:00Z"
    }
]
```

## Backup Endpoints

### POST /api/backup/create
Create a new backup.

**Request Body:**
```json
{
    "type": "full"
}
```

**Response:**
```json
{
    "id": "backup_id",
    "type": "full",
    "status": "pending",
    "createdAt": "2024-01-08T00:00:00Z"
}
```

### GET /api/backup/list
Get list of backups.

**Response:**
```json
[
    {
        "id": "backup_id",
        "type": "full",
        "status": "completed",
        "sizeBytes": 1024,
        "checksum": "hash",
        "createdAt": "2024-01-08T00:00:00Z",
        "completedAt": "2024-01-08T00:01:00Z"
    }
]
```

### POST /api/backup/schedule
Schedule automated backups.

**Request Body:**
```json
{
    "frequency": "daily",
    "timeOfDay": "00:00",
    "retentionDays": 30
}
```

**Response:**
```json
{
    "id": "schedule_id",
    "frequency": "daily",
    "timeOfDay": "00:00",
    "retentionDays": 30,
    "nextRun": "2024-01-09T00:00:00Z"
}
```

### POST /api/backup/restore/:backupId
Restore from a backup.

**Response:**
```json
{
    "message": "Restore process started"
}
```

## WebSocket API

Connect to WebSocket endpoint: `ws://localhost:3002`

### Subscribe to Market Data
```json
{
    "type": "subscribe",
    "channel": "ticker",
    "symbol": "BTCUSDT"
}
```

### Subscribe to Order Book
```json
{
    "type": "subscribe",
    "channel": "orderbook",
    "symbol": "BTCUSDT"
}
```

### Subscribe to Trades
```json
{
    "type": "subscribe",
    "channel": "trades",
    "symbol": "BTCUSDT"
}
```

### Subscribe to Klines (Candlesticks)
```json
{
    "type": "subscribe",
    "channel": "kline",
    "symbol": "BTCUSDT",
    "interval": "1m"
}
```

### Message Format
All WebSocket messages follow this format:
```json
{
    "type": "message_type",
    "data": {
        // Message specific data
    }
}
```

## Error Handling

All endpoints return errors in the following format:
```json
{
    "error": "Error message",
    "code": "ERROR_CODE" // Optional
}
```

Common HTTP Status Codes:
- 200: Success
- 201: Created
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 500: Internal Server Error 