export enum OrderType {
    MARKET = 'MARKET',
    LIMIT = 'LIMIT',
    STOP = 'STOP',
    STOP_LIMIT = 'STOP_LIMIT',
    TRAILING_STOP = 'TRAILING_STOP',
    OCO = 'OCO',
    BRACKET = 'BRACKET',
    ICEBERG = 'ICEBERG'
}

export enum OrderSide {
    BUY = 'BUY',
    SELL = 'SELL'
}

export enum OrderStatus {
    PENDING = 'PENDING',
    OPEN = 'OPEN',
    FILLED = 'FILLED',
    CANCELLED = 'CANCELLED',
    REJECTED = 'REJECTED',
    EXPIRED = 'EXPIRED'
}

export enum TimeInForce {
    GTC = 'GTC', // Good Till Cancelled
    IOC = 'IOC', // Immediate or Cancel
    FOK = 'FOK', // Fill or Kill
    GTD = 'GTD'  // Good Till Date
}

export interface Order {
    id: string;
    userId: string;
    symbol: string;
    type: OrderType;
    side: OrderSide;
    quantity: number;
    price?: number;
    stopPrice?: number;
    trailingOffset?: number;
    timeInForce: TimeInForce;
    status: OrderStatus;
    filledQuantity: number;
    averagePrice?: number;
    createdAt: Date;
    updatedAt: Date;
    expiresAt?: Date;
    parentOrderId?: string;
    childOrders?: string[];
}

export interface Position {
    id: string;
    userId: string;
    symbol: string;
    quantity: number;
    averageEntryPrice: number;
    currentPrice: number;
    unrealizedPnL: number;
    realizedPnL: number;
    createdAt: Date;
    updatedAt: Date;
}

export interface Trade {
    id: string;
    userId: string;
    orderId: string;
    symbol: string;
    side: OrderSide;
    quantity: number;
    price: number;
    timestamp: Date;
    fee: number;
    totalValue: number;
}

export interface RiskSettings {
    id: string;
    userId: string;
    maxPositionSize: number;
    maxLeverage: number;
    maxDailyLoss: number;
    maxDrawdown: number;
    stopLossPercentage: number;
    trailingStopPercentage?: number;
    updatedAt: Date;
}

export interface TechnicalIndicator {
    id: string;
    name: string;
    type: string;
    parameters: Record<string, any>;
    color: string;
    visible: boolean;
}

export interface ChartSettings {
    id: string;
    userId: string;
    timeframe: string;
    indicators: TechnicalIndicator[];
    theme: 'light' | 'dark';
    showVolume: boolean;
    showGrid: boolean;
    updatedAt: Date;
}

export interface MarketData {
    symbol: string;
    timestamp: Date;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
    trades: number;
}

export interface OrderBook {
    symbol: string;
    timestamp: Date;
    bids: [number, number][]; // [price, quantity][]
    asks: [number, number][]; // [price, quantity][]
}

export interface PortfolioMetrics {
    totalValue: number;
    dailyPnL: number;
    totalPnL: number;
    margin: number;
    marginUsage: number;
    leverage: number;
    drawdown: number;
    sharpeRatio: number;
    positions: Position[];
}

export interface TradingStrategy {
    id: string;
    userId: string;
    name: string;
    description: string;
    parameters: Record<string, any>;
    active: boolean;
    createdAt: Date;
    updatedAt: Date;
}

export interface BacktestResult {
    id: string;
    strategyId: string;
    startDate: Date;
    endDate: Date;
    initialBalance: number;
    finalBalance: number;
    totalTrades: number;
    winRate: number;
    profitFactor: number;
    sharpeRatio: number;
    maxDrawdown: number;
    trades: Trade[];
} 