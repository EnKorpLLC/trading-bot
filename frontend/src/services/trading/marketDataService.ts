import { MarketData, OrderBook } from '@/types/trading';

type PriceCallback = (price: number, symbol: string) => void;
type OrderBookCallback = (orderBook: OrderBook) => void;

export class MarketDataService {
    private ws: WebSocket | null = null;
    private priceSubscriptions: Map<string, Set<PriceCallback>> = new Map();
    private orderBookSubscriptions: Map<string, Set<OrderBookCallback>> = new Map();
    private reconnectAttempts = 0;
    private maxReconnectAttempts = 5;
    private reconnectDelay = 1000;

    constructor(private wsUrl: string = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:3001/ws') {}

    public connect(): void {
        try {
            this.ws = new WebSocket(this.wsUrl);
            
            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.reconnectAttempts = 0;
                this.resubscribe();
            };

            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleMessage(data);
            };

            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                this.handleDisconnect();
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };
        } catch (error) {
            console.error('Failed to connect WebSocket:', error);
            this.handleDisconnect();
        }
    }

    private handleMessage(data: any): void {
        switch (data.type) {
            case 'price':
                this.handlePriceUpdate(data.symbol, data.price);
                break;
            case 'orderbook':
                this.handleOrderBookUpdate(data.symbol, data.orderBook);
                break;
            case 'error':
                console.error('Market data error:', data.message);
                break;
            default:
                console.warn('Unknown message type:', data.type);
        }
    }

    private handlePriceUpdate(symbol: string, price: number): void {
        const callbacks = this.priceSubscriptions.get(symbol);
        if (callbacks) {
            callbacks.forEach(callback => callback(price, symbol));
        }
    }

    private handleOrderBookUpdate(symbol: string, orderBook: OrderBook): void {
        const callbacks = this.orderBookSubscriptions.get(symbol);
        if (callbacks) {
            callbacks.forEach(callback => callback(orderBook));
        }
    }

    private handleDisconnect(): void {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            setTimeout(() => {
                this.reconnectAttempts++;
                this.connect();
            }, this.reconnectDelay * Math.pow(2, this.reconnectAttempts));
        } else {
            console.error('Max reconnection attempts reached');
        }
    }

    private resubscribe(): void {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return;

        // Resubscribe to all price feeds
        this.priceSubscriptions.forEach((_, symbol) => {
            this.ws!.send(JSON.stringify({
                type: 'subscribe',
                channel: 'price',
                symbol
            }));
        });

        // Resubscribe to all order books
        this.orderBookSubscriptions.forEach((_, symbol) => {
            this.ws!.send(JSON.stringify({
                type: 'subscribe',
                channel: 'orderbook',
                symbol
            }));
        });
    }

    public subscribeToPriceUpdates(symbol: string, callback: PriceCallback): void {
        if (!this.priceSubscriptions.has(symbol)) {
            this.priceSubscriptions.set(symbol, new Set());
        }
        this.priceSubscriptions.get(symbol)!.add(callback);

        if (this.ws?.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'subscribe',
                channel: 'price',
                symbol
            }));
        }
    }

    public subscribeToOrderBook(symbol: string, callback: OrderBookCallback): void {
        if (!this.orderBookSubscriptions.has(symbol)) {
            this.orderBookSubscriptions.set(symbol, new Set());
        }
        this.orderBookSubscriptions.get(symbol)!.add(callback);

        if (this.ws?.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'subscribe',
                channel: 'orderbook',
                symbol
            }));
        }
    }

    public unsubscribeFromPriceUpdates(symbol: string, callback: PriceCallback): void {
        const callbacks = this.priceSubscriptions.get(symbol);
        if (callbacks) {
            callbacks.delete(callback);
            if (callbacks.size === 0) {
                this.priceSubscriptions.delete(symbol);
                if (this.ws?.readyState === WebSocket.OPEN) {
                    this.ws.send(JSON.stringify({
                        type: 'unsubscribe',
                        channel: 'price',
                        symbol
                    }));
                }
            }
        }
    }

    public unsubscribeFromOrderBook(symbol: string, callback: OrderBookCallback): void {
        const callbacks = this.orderBookSubscriptions.get(symbol);
        if (callbacks) {
            callbacks.delete(callback);
            if (callbacks.size === 0) {
                this.orderBookSubscriptions.delete(symbol);
                if (this.ws?.readyState === WebSocket.OPEN) {
                    this.ws.send(JSON.stringify({
                        type: 'unsubscribe',
                        channel: 'orderbook',
                        symbol
                    }));
                }
            }
        }
    }

    public disconnect(): void {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        this.priceSubscriptions.clear();
        this.orderBookSubscriptions.clear();
    }

    public async getHistoricalData(
        symbol: string,
        timeframe: string,
        start: Date,
        end: Date
    ): Promise<MarketData[]> {
        const response = await fetch(
            `${process.env.NEXT_PUBLIC_API_URL}/market-data/historical?` +
            new URLSearchParams({
                symbol,
                timeframe,
                start: start.toISOString(),
                end: end.toISOString()
            })
        );

        if (!response.ok) {
            throw new Error('Failed to fetch historical data');
        }

        return response.json();
    }
} 