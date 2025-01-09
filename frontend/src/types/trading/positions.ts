import { OrderSide } from './orders';

export enum PositionStatus {
    OPEN = 'OPEN',
    CLOSED = 'CLOSED',
    PARTIALLY_CLOSED = 'PARTIALLY_CLOSED'
}

export interface Position {
    id: string;
    userId: string;
    symbol: string;
    side: OrderSide;
    quantity: number;
    averageEntryPrice: number;
    currentPrice: number;
    unrealizedPnL: number;
    realizedPnL: number;
    status: PositionStatus;
    openedAt: Date;
    updatedAt: Date;
    closedAt?: Date;
}

export interface PositionUpdate {
    symbol: string;
    currentPrice: number;
    unrealizedPnL: number;
    timestamp: Date;
}

export interface PositionSummary {
    totalPositions: number;
    totalUnrealizedPnL: number;
    totalRealizedPnL: number;
    openPositions: number;
    closedPositions: number;
}

export interface PositionMetrics {
    winRate: number;
    averageWin: number;
    averageLoss: number;
    profitFactor: number;
    sharpeRatio: number;
    maxDrawdown: number;
}

export interface PositionRequest {
    symbol: string;
    side: OrderSide;
    quantity: number;
    price: number;
}

export interface PositionResponse {
    position: Position;
    message: string;
    success: boolean;
    timestamp: Date;
} 