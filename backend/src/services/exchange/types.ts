export interface ExchangeCredentials {
    apiKey: string;
    apiSecret: string;
    testnet?: boolean;
}

export interface MarketData {
    symbol: string;
    price: number;
    timestamp: number;
    bid?: number;
    ask?: number;
    volume?: number;
}

export interface OrderBookEntry {
    price: number;
    quantity: number;
}

export interface OrderBook {
    symbol: string;
    timestamp: number;
    bids: OrderBookEntry[];
    asks: OrderBookEntry[];
}

export interface ExchangeBalance {
    asset: string;
    free: number;
    locked: number;
    total: number;
}

export interface ExchangeOrder {
    id: string;
    symbol: string;
    side: 'buy' | 'sell';
    type: 'market' | 'limit' | 'stop' | 'take_profit' | 'trailing_stop';
    status: 'new' | 'filled' | 'partially_filled' | 'canceled' | 'rejected';
    price: number;
    quantity: number;
    filledQuantity: number;
    remainingQuantity: number;
    timestamp: number;
}

export interface ExchangePosition {
    symbol: string;
    side: 'long' | 'short';
    quantity: number;
    entryPrice: number;
    markPrice: number;
    liquidationPrice?: number;
    margin?: number;
    leverage?: number;
    unrealizedPnl: number;
    timestamp: number;
}

export interface KlineData {
    timestamp: number;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
}

export type TimeFrame = '1m' | '5m' | '15m' | '30m' | '1h' | '4h' | '1d' | '1w';

export interface ExchangeError extends Error {
    code?: string;
    httpCode?: number;
    data?: any;
} 