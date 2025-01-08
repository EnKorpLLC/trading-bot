# API Documentation

## Overview
This document details the API structure for the Trading Bot platform, including both TradeLocker integration and internal APIs.

## TradeLocker Integration API

### Authentication
```typescript
POST /api/auth/login
{
    "email": string,
    "password": string,
    "server": string
}
```

### Market Data
```typescript
GET /api/market/quotes
GET /api/market/depth
GET /api/market/history
WebSocket: ws://api/market/stream
```

### Trading Operations
```typescript
POST /api/trade/order
GET /api/trade/orders
PUT /api/trade/order/{id}
DELETE /api/trade/order/{id}
GET /api/trade/positions
```

### Account Management
```typescript
GET /api/account/info
GET /api/account/balance
GET /api/account/history
```

## Internal APIs

### AI Trading System
```typescript
POST /api/ai/analyze
POST /api/ai/strategy/select
POST /api/ai/trade/approve
GET /api/ai/performance
```

### Risk Management
```typescript
POST /api/risk/validate
GET /api/risk/limits
PUT /api/risk/settings
GET /api/risk/analysis
```

### System Management
```typescript
GET /api/system/status
GET /api/system/performance
POST /api/system/config
```

## WebSocket Events

### Market Data
```typescript
{
    type: "MARKET_UPDATE",
    data: {
        symbol: string,
        bid: number,
        ask: number,
        timestamp: number
    }
}
```

### Trading Updates
```typescript
{
    type: "TRADE_UPDATE",
    data: {
        orderId: string,
        status: string,
        fillPrice?: number,
        timestamp: number
    }
}
```

### AI System Events
```typescript
{
    type: "AI_DECISION",
    data: {
        strategy: string,
        action: string,
        confidence: number,
        analysis: object
    }
}
```

## Rate Limiting
- Market Data: 100 requests per minute
- Trading Operations: 50 requests per minute
- Account Operations: 30 requests per minute
- AI Operations: 20 requests per minute

## Error Handling
```typescript
{
    "error": {
        "code": string,
        "message": string,
        "details": object
    }
}
```

## Authentication
- JWT-based authentication
- Token refresh mechanism
- Session management
- API key support for automated trading

## Security
- TLS encryption required
- API key rotation policy
- IP whitelisting support
- Request signing for sensitive operations 