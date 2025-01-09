import WebSocket from 'ws';
import crypto from 'crypto';
import { BaseExchangeService } from './base';
import {
    ExchangeCredentials,
    MarketData,
    OrderBook,
    ExchangeBalance,
    ExchangeOrder,
    ExchangePosition,
    KlineData,
    TimeFrame
} from './types';
import { logger } from '../../utils/logger';

export class BinanceService extends BaseExchangeService {
    private readonly baseUrl: string;
    private readonly wsBaseUrl: string;

    constructor(credentials: ExchangeCredentials) {
        super(credentials);
        this.baseUrl = credentials.testnet
            ? 'https://testnet.binance.vision/api'
            : 'https://api.binance.com/api';
        this.wsBaseUrl = credentials.testnet
            ? 'wss://testnet.binance.vision/ws'
            : 'wss://stream.binance.com:9443/ws';
    }

    private async makeRequest(
        endpoint: string,
        method: string = 'GET',
        params: any = {},
        signed: boolean = false
    ): Promise<any> {
        try {
            const timestamp = Date.now();
            const queryString = Object.entries(params)
                .filter(([_, value]) => value !== undefined)
                .map(([key, value]) => `${key}=${value}`)
                .join('&');

            let url = `${this.baseUrl}${endpoint}`;
            let headers: Record<string, string> = {
                'X-MBX-APIKEY': this.credentials.apiKey
            };

            if (signed) {
                const signature = crypto
                    .createHmac('sha256', this.credentials.apiSecret)
                    .update(`${queryString}&timestamp=${timestamp}`)
                    .digest('hex');

                url += `?${queryString}&timestamp=${timestamp}&signature=${signature}`;
            } else if (queryString) {
                url += `?${queryString}`;
            }

            const response = await fetch(url, { method, headers });
            if (!response.ok) {
                throw this.handleError({
                    message: `HTTP ${response.status}: ${response.statusText}`,
                    httpCode: response.status,
                    data: await response.json()
                });
            }

            return await response.json();
        } catch (error) {
            logger.error('Binance API request error:', error);
            throw error;
        }
    }

    // Market Data Methods
    async getPrice(symbol: string): Promise<number> {
        const data = await this.makeRequest('/v3/ticker/price', 'GET', { symbol });
        return parseFloat(data.price);
    }

    async getMarketData(symbol: string): Promise<MarketData> {
        const data = await this.makeRequest('/v3/ticker/24hr', 'GET', { symbol });
        return {
            symbol,
            price: parseFloat(data.lastPrice),
            timestamp: data.closeTime,
            bid: parseFloat(data.bidPrice),
            ask: parseFloat(data.askPrice),
            volume: parseFloat(data.volume)
        };
    }

    async getOrderBook(symbol: string, limit: number = 100): Promise<OrderBook> {
        const data = await this.makeRequest('/v3/depth', 'GET', { symbol, limit });
        return {
            symbol,
            timestamp: Date.now(),
            bids: data.bids.map((bid: string[]) => ({
                price: parseFloat(bid[0]),
                quantity: parseFloat(bid[1])
            })),
            asks: data.asks.map((ask: string[]) => ({
                price: parseFloat(ask[0]),
                quantity: parseFloat(ask[1])
            }))
        };
    }

    async getKlines(
        symbol: string,
        timeframe: TimeFrame,
        limit: number = 500
    ): Promise<KlineData[]> {
        const interval = this.convertTimeFrame(timeframe);
        const data = await this.makeRequest('/v3/klines', 'GET', {
            symbol,
            interval,
            limit
        });

        return data.map((kline: any[]) => ({
            timestamp: kline[0],
            open: parseFloat(kline[1]),
            high: parseFloat(kline[2]),
            low: parseFloat(kline[3]),
            close: parseFloat(kline[4]),
            volume: parseFloat(kline[5])
        }));
    }

    // Trading Methods
    async createOrder(params: {
        symbol: string;
        side: 'buy' | 'sell';
        type: 'market' | 'limit' | 'stop' | 'take_profit' | 'trailing_stop';
        quantity: number;
        price?: number;
        stopPrice?: number;
    }): Promise<ExchangeOrder> {
        const orderParams = {
            symbol: params.symbol,
            side: params.side.toUpperCase(),
            type: this.convertOrderType(params.type),
            quantity: params.quantity,
            price: params.price,
            stopPrice: params.stopPrice,
            timeInForce: params.type === 'limit' ? 'GTC' : undefined
        };

        const data = await this.makeRequest(
            '/v3/order',
            'POST',
            orderParams,
            true
        );

        return this.convertOrder(data);
    }

    async cancelOrder(symbol: string, orderId: string): Promise<boolean> {
        await this.makeRequest(
            '/v3/order',
            'DELETE',
            { symbol, orderId },
            true
        );
        return true;
    }

    async getOrder(symbol: string, orderId: string): Promise<ExchangeOrder> {
        const data = await this.makeRequest(
            '/v3/order',
            'GET',
            { symbol, orderId },
            true
        );
        return this.convertOrder(data);
    }

    async getOpenOrders(symbol?: string): Promise<ExchangeOrder[]> {
        const data = await this.makeRequest(
            '/v3/openOrders',
            'GET',
            { symbol },
            true
        );
        return data.map(this.convertOrder);
    }

    // Account Methods
    async getBalances(): Promise<ExchangeBalance[]> {
        const data = await this.makeRequest('/v3/account', 'GET', {}, true);
        return data.balances.map((balance: any) => ({
            asset: balance.asset,
            free: parseFloat(balance.free),
            locked: parseFloat(balance.locked),
            total: parseFloat(balance.free) + parseFloat(balance.locked)
        }));
    }

    async getPositions(): Promise<ExchangePosition[]> {
        const data = await this.makeRequest('/v3/account', 'GET', {}, true);
        return data.positions
            .filter((pos: any) => parseFloat(pos.positionAmt) !== 0)
            .map((pos: any) => ({
                symbol: pos.symbol,
                side: parseFloat(pos.positionAmt) > 0 ? 'long' : 'short',
                quantity: Math.abs(parseFloat(pos.positionAmt)),
                entryPrice: parseFloat(pos.entryPrice),
                markPrice: parseFloat(pos.markPrice),
                liquidationPrice: parseFloat(pos.liquidationPrice),
                leverage: parseFloat(pos.leverage),
                unrealizedPnl: parseFloat(pos.unrealizedProfit),
                timestamp: Date.now()
            }));
    }

    async setLeverage(symbol: string, leverage: number): Promise<boolean> {
        await this.makeRequest(
            '/v3/leverage',
            'POST',
            { symbol, leverage },
            true
        );
        return true;
    }

    // WebSocket Methods
    protected initializeWebSocket(endpoint: string): WebSocket {
        const ws = new WebSocket(`${this.wsBaseUrl}${endpoint}`);

        ws.on('message', (data: string) => {
            this.handleWebSocketMessage(JSON.parse(data));
        });

        ws.on('error', (error: Error) => {
            this.handleWebSocketError(error);
        });

        ws.on('close', () => {
            this.handleWebSocketClose();
        });

        return ws;
    }

    subscribeToTicker(symbol: string, callback: (data: MarketData) => void): void {
        const endpoint = `/${symbol.toLowerCase()}@ticker`;
        const ws = this.initializeWebSocket(endpoint);
        this.wsConnections.set(endpoint, ws);
        this.subscriptions.set(endpoint, new Set([symbol]));

        this.on('message', (data: any) => {
            if (data.e === '24hrTicker') {
                callback({
                    symbol: data.s,
                    price: parseFloat(data.c),
                    timestamp: data.E,
                    bid: parseFloat(data.b),
                    ask: parseFloat(data.a),
                    volume: parseFloat(data.v)
                });
            }
        });
    }

    subscribeToOrderBook(symbol: string, callback: (data: OrderBook) => void): void {
        const endpoint = `/${symbol.toLowerCase()}@depth20`;
        const ws = this.initializeWebSocket(endpoint);
        this.wsConnections.set(endpoint, ws);
        this.subscriptions.set(endpoint, new Set([symbol]));

        this.on('message', (data: any) => {
            if (data.e === 'depth') {
                callback({
                    symbol: symbol,
                    timestamp: data.E,
                    bids: data.b.map((bid: string[]) => ({
                        price: parseFloat(bid[0]),
                        quantity: parseFloat(bid[1])
                    })),
                    asks: data.a.map((ask: string[]) => ({
                        price: parseFloat(ask[0]),
                        quantity: parseFloat(ask[1])
                    }))
                });
            }
        });
    }

    subscribeToTrades(symbol: string, callback: (data: ExchangeOrder) => void): void {
        const endpoint = `/${symbol.toLowerCase()}@trade`;
        const ws = this.initializeWebSocket(endpoint);
        this.wsConnections.set(endpoint, ws);
        this.subscriptions.set(endpoint, new Set([symbol]));

        this.on('message', (data: any) => {
            if (data.e === 'trade') {
                callback({
                    id: data.t.toString(),
                    symbol: data.s,
                    side: data.m ? 'sell' : 'buy',
                    type: 'market',
                    status: 'filled',
                    price: parseFloat(data.p),
                    quantity: parseFloat(data.q),
                    filledQuantity: parseFloat(data.q),
                    remainingQuantity: 0,
                    timestamp: data.T
                });
            }
        });
    }

    subscribeToKlines(
        symbol: string,
        timeframe: TimeFrame,
        callback: (data: KlineData) => void
    ): void {
        const interval = this.convertTimeFrame(timeframe);
        const endpoint = `/${symbol.toLowerCase()}@kline_${interval}`;
        const ws = this.initializeWebSocket(endpoint);
        this.wsConnections.set(endpoint, ws);
        this.subscriptions.set(endpoint, new Set([symbol]));

        this.on('message', (data: any) => {
            if (data.e === 'kline') {
                callback({
                    timestamp: data.k.t,
                    open: parseFloat(data.k.o),
                    high: parseFloat(data.k.h),
                    low: parseFloat(data.k.l),
                    close: parseFloat(data.k.c),
                    volume: parseFloat(data.k.v)
                });
            }
        });
    }

    protected async resubscribe(endpoint: string, symbol: string): Promise<void> {
        const type = endpoint.split('@')[1];
        switch (type) {
            case 'ticker':
                this.subscribeToTicker(symbol, () => {});
                break;
            case 'depth20':
                this.subscribeToOrderBook(symbol, () => {});
                break;
            case 'trade':
                this.subscribeToTrades(symbol, () => {});
                break;
            default:
                if (type.startsWith('kline_')) {
                    const timeframe = this.convertBinanceInterval(
                        type.replace('kline_', '')
                    );
                    this.subscribeToKlines(symbol, timeframe, () => {});
                }
        }
    }

    private convertTimeFrame(timeframe: TimeFrame): string {
        const map: Record<TimeFrame, string> = {
            '1m': '1m',
            '5m': '5m',
            '15m': '15m',
            '30m': '30m',
            '1h': '1h',
            '4h': '4h',
            '1d': '1d',
            '1w': '1w'
        };
        return map[timeframe];
    }

    private convertBinanceInterval(interval: string): TimeFrame {
        const map: Record<string, TimeFrame> = {
            '1m': '1m',
            '5m': '5m',
            '15m': '15m',
            '30m': '30m',
            '1h': '1h',
            '4h': '4h',
            '1d': '1d',
            '1w': '1w'
        };
        return map[interval] || '1m';
    }

    private convertOrderType(type: string): string {
        const map: Record<string, string> = {
            market: 'MARKET',
            limit: 'LIMIT',
            stop: 'STOP_LOSS',
            take_profit: 'TAKE_PROFIT',
            trailing_stop: 'TRAILING_STOP_MARKET'
        };
        return map[type] || type.toUpperCase();
    }

    private convertOrder(data: any): ExchangeOrder {
        return {
            id: data.orderId.toString(),
            symbol: data.symbol,
            side: data.side.toLowerCase(),
            type: data.type.toLowerCase(),
            status: data.status.toLowerCase(),
            price: parseFloat(data.price),
            quantity: parseFloat(data.origQty),
            filledQuantity: parseFloat(data.executedQty),
            remainingQuantity:
                parseFloat(data.origQty) - parseFloat(data.executedQty),
            timestamp: data.time
        };
    }
} 