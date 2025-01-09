export enum OrderType {
    MARKET = 'MARKET',
    LIMIT = 'LIMIT',
    STOP = 'STOP',
    STOP_LIMIT = 'STOP_LIMIT'
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
    GTC = 'GOOD_TILL_CANCEL',
    IOC = 'IMMEDIATE_OR_CANCEL',
    FOK = 'FILL_OR_KILL',
    GTD = 'GOOD_TILL_DATE'
}

export interface BaseOrder {
    id?: string;
    symbol: string;
    side: OrderSide;
    quantity: number;
    type: OrderType;
    status: OrderStatus;
    timeInForce: TimeInForce;
    createdAt?: Date;
    updatedAt?: Date;
    userId: string;
    clientOrderId?: string;
}

export interface MarketOrder extends BaseOrder {
    type: OrderType.MARKET;
}

export interface LimitOrder extends BaseOrder {
    type: OrderType.LIMIT;
    price: number;
}

export interface StopOrder extends BaseOrder {
    type: OrderType.STOP;
    stopPrice: number;
}

export interface StopLimitOrder extends BaseOrder {
    type: OrderType.STOP_LIMIT;
    price: number;
    stopPrice: number;
}

export type Order = MarketOrder | LimitOrder | StopOrder | StopLimitOrder;

export interface OrderResponse {
    order: Order;
    message: string;
    success: boolean;
    timestamp: Date;
}

export interface OrderRequest {
    symbol: string;
    side: OrderSide;
    quantity: number;
    type: OrderType;
    price?: number;
    stopPrice?: number;
    timeInForce?: TimeInForce;
    clientOrderId?: string;
} 