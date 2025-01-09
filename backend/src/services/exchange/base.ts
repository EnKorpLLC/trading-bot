import WebSocket from 'ws';
import { EventEmitter } from 'events';
import {
    ExchangeCredentials,
    MarketData,
    OrderBook,
    ExchangeBalance,
    ExchangeOrder,
    ExchangePosition,
    KlineData,
    TimeFrame,
    ExchangeError
} from './types';
import { logger } from '../../utils/logger';

export abstract class BaseExchangeService extends EventEmitter {
    protected credentials: ExchangeCredentials;
    protected wsConnections: Map<string, WebSocket>;
    protected subscriptions: Map<string, Set<string>>;

    constructor(credentials: ExchangeCredentials) {
        super();
        this.credentials = credentials;
        this.wsConnections = new Map();
        this.subscriptions = new Map();
    }

    // Market Data Methods
    abstract getPrice(symbol: string): Promise<number>;
    abstract getMarketData(symbol: string): Promise<MarketData>;
    abstract getOrderBook(symbol: string, limit?: number): Promise<OrderBook>;
    abstract getKlines(symbol: string, timeframe: TimeFrame, limit?: number): Promise<KlineData[]>;

    // Trading Methods
    abstract createOrder(params: {
        symbol: string;
        side: 'buy' | 'sell';
        type: 'market' | 'limit' | 'stop' | 'take_profit' | 'trailing_stop';
        quantity: number;
        price?: number;
        stopPrice?: number;
    }): Promise<ExchangeOrder>;

    abstract cancelOrder(symbol: string, orderId: string): Promise<boolean>;
    abstract getOrder(symbol: string, orderId: string): Promise<ExchangeOrder>;
    abstract getOpenOrders(symbol?: string): Promise<ExchangeOrder[]>;

    // Account Methods
    abstract getBalances(): Promise<ExchangeBalance[]>;
    abstract getPositions(): Promise<ExchangePosition[]>;
    abstract setLeverage(symbol: string, leverage: number): Promise<boolean>;

    // WebSocket Methods
    protected abstract initializeWebSocket(endpoint: string): WebSocket;
    
    abstract subscribeToTicker(symbol: string, callback: (data: MarketData) => void): void;
    abstract subscribeToOrderBook(symbol: string, callback: (data: OrderBook) => void): void;
    abstract subscribeToTrades(symbol: string, callback: (data: ExchangeOrder) => void): void;
    abstract subscribeToKlines(
        symbol: string,
        timeframe: TimeFrame,
        callback: (data: KlineData) => void
    ): void;

    protected handleWebSocketMessage(data: any): void {
        try {
            // Implementation specific to each exchange
            this.emit('message', data);
        } catch (error) {
            logger.error('WebSocket message handling error:', error);
            this.emit('error', error);
        }
    }

    protected handleWebSocketError(error: Error): void {
        logger.error('WebSocket error:', error);
        this.emit('error', error);
    }

    protected handleWebSocketClose(): void {
        logger.info('WebSocket connection closed');
        this.emit('close');
        // Implement reconnection logic
        setTimeout(() => this.reconnect(), 5000);
    }

    protected async reconnect(): Promise<void> {
        try {
            // Reestablish WebSocket connections
            for (const [endpoint, ws] of this.wsConnections.entries()) {
                ws.terminate();
                const newWs = this.initializeWebSocket(endpoint);
                this.wsConnections.set(endpoint, newWs);

                // Resubscribe to previous subscriptions
                const subs = this.subscriptions.get(endpoint);
                if (subs) {
                    for (const sub of subs) {
                        // Implementation specific to each exchange
                        await this.resubscribe(endpoint, sub);
                    }
                }
            }
        } catch (error) {
            logger.error('WebSocket reconnection error:', error);
            this.emit('error', error);
        }
    }

    protected abstract resubscribe(endpoint: string, subscription: string): Promise<void>;

    protected handleError(error: any): ExchangeError {
        const exchangeError: ExchangeError = new Error(error.message);
        exchangeError.code = error.code;
        exchangeError.httpCode = error.httpCode;
        exchangeError.data = error.data;
        return exchangeError;
    }

    public disconnect(): void {
        for (const ws of this.wsConnections.values()) {
            ws.terminate();
        }
        this.wsConnections.clear();
        this.subscriptions.clear();
    }
} 