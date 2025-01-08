# Database Schema Documentation

## Overview
PostgreSQL database schema for the Trading Bot platform using Neon.

## Tables

### Users
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    subscription_status VARCHAR(50),
    subscription_expires TIMESTAMP WITH TIME ZONE
);
```

### TradeLocker_Accounts
```sql
CREATE TABLE tradelocker_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    account_number VARCHAR(100) NOT NULL,
    server VARCHAR(100) NOT NULL,
    api_key VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    last_sync TIMESTAMP WITH TIME ZONE,
    UNIQUE(user_id, account_number)
);
```

### Trading_Sessions
```sql
CREATE TABLE trading_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id UUID REFERENCES tradelocker_accounts(id),
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP WITH TIME ZONE,
    initial_balance DECIMAL(20,8),
    final_balance DECIMAL(20,8),
    pnl DECIMAL(20,8),
    trades_count INTEGER DEFAULT 0
);
```

### Trades
```sql
CREATE TABLE trades (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES trading_sessions(id),
    symbol VARCHAR(20) NOT NULL,
    direction VARCHAR(10) NOT NULL,
    entry_price DECIMAL(20,8) NOT NULL,
    exit_price DECIMAL(20,8),
    size DECIMAL(20,8) NOT NULL,
    entry_time TIMESTAMP WITH TIME ZONE NOT NULL,
    exit_time TIMESTAMP WITH TIME ZONE,
    pnl DECIMAL(20,8),
    status VARCHAR(20) NOT NULL,
    strategy_id UUID,
    ai_confidence DECIMAL(5,4)
);
```

### AI_Strategies
```sql
CREATE TABLE ai_strategies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    parameters JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    performance_score DECIMAL(5,4),
    is_active BOOLEAN DEFAULT true
);
```

### Strategy_Performance
```sql
CREATE TABLE strategy_performance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    strategy_id UUID REFERENCES ai_strategies(id),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    win_rate DECIMAL(5,4),
    profit_factor DECIMAL(10,4),
    sharpe_ratio DECIMAL(10,4),
    trades_count INTEGER,
    period_start TIMESTAMP WITH TIME ZONE,
    period_end TIMESTAMP WITH TIME ZONE
);
```

### Risk_Settings
```sql
CREATE TABLE risk_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id UUID REFERENCES tradelocker_accounts(id),
    max_daily_loss DECIMAL(20,8),
    max_position_size DECIMAL(20,8),
    max_open_positions INTEGER,
    risk_per_trade DECIMAL(5,4),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### System_Logs
```sql
CREATE TABLE system_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    level VARCHAR(20) NOT NULL,
    component VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    details JSONB
);
```

## Indexes
```sql
CREATE INDEX idx_trades_session ON trades(session_id);
CREATE INDEX idx_trades_strategy ON trades(strategy_id);
CREATE INDEX idx_strategy_performance_strategy ON strategy_performance(strategy_id);
CREATE INDEX idx_system_logs_timestamp ON system_logs(timestamp);
CREATE INDEX idx_system_logs_level ON system_logs(level);
```

## Views

### Active_Strategies_Performance
```sql
CREATE VIEW active_strategies_performance AS
SELECT 
    s.id,
    s.name,
    s.performance_score,
    sp.win_rate,
    sp.profit_factor,
    sp.sharpe_ratio,
    sp.trades_count
FROM ai_strategies s
JOIN strategy_performance sp ON s.id = sp.strategy_id
WHERE s.is_active = true;
```

### Account_Performance
```sql
CREATE VIEW account_performance AS
SELECT 
    ta.account_number,
    ts.started_at,
    ts.ended_at,
    ts.initial_balance,
    ts.final_balance,
    ts.pnl,
    ts.trades_count
FROM tradelocker_accounts ta
JOIN trading_sessions ts ON ta.id = ts.account_id;
```

## Backup and Recovery
- Daily automated backups
- Point-in-time recovery enabled
- 30-day backup retention
- Continuous replication to standby 