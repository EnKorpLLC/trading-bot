import { OrderSide, OrderType } from './orders';

export interface Trade {
    id: string;
    orderId: string;
    userId: string;
    symbol: string;
    side: OrderSide;
    type: OrderType;
    quantity: number;
    price: number;
    commission: number;
    pnl: number;
    executedAt: Date;
}

export interface TradeHistory {
    trades: Trade[];
    totalTrades: number;
    totalPnL: number;
    totalCommission: number;
    startDate: Date;
    endDate: Date;
}

export interface TradeMetrics {
    winningTrades: number;
    losingTrades: number;
    winRate: number;
    averageWin: number;
    averageLoss: number;
    largestWin: number;
    largestLoss: number;
    profitFactor: number;
    sharpeRatio: number;
    maxDrawdown: number;
    recoveryFactor: number;
}

export interface TradeRequest {
    startDate?: Date;
    endDate?: Date;
    symbol?: string;
    limit?: number;
    offset?: number;
}

export interface TradeResponse {
    trades: Trade[];
    metrics: TradeMetrics;
    message: string;
    success: boolean;
    timestamp: Date;
} 