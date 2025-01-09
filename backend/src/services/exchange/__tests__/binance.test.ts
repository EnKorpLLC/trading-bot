import { BinanceService } from '../binance';
import { ExchangeCredentials } from '../types';
import WebSocket from 'ws';

// Mock WebSocket
jest.mock('ws');

// Mock fetch
global.fetch = jest.fn();

describe('BinanceService', () => {
    let service: BinanceService;
    const mockCredentials: ExchangeCredentials = {
        apiKey: 'test-api-key',
        apiSecret: 'test-api-secret',
        testnet: true
    };

    beforeEach(() => {
        service = new BinanceService(mockCredentials);
        (WebSocket as jest.Mock).mockClear();
        (global.fetch as jest.Mock).mockClear();
    });

    describe('Market Data Methods', () => {
        it('should get price for a symbol', async () => {
            const mockResponse = { price: '50000.00' };
            (global.fetch as jest.Mock).mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve(mockResponse)
            });

            const price = await service.getPrice('BTCUSDT');
            expect(price).toBe(50000.00);
            expect(global.fetch).toHaveBeenCalledWith(
                expect.stringContaining('/v3/ticker/price?symbol=BTCUSDT'),
                expect.any(Object)
            );
        });

        it('should get market data for a symbol', async () => {
            const mockResponse = {
                lastPrice: '50000.00',
                bidPrice: '49990.00',
                askPrice: '50010.00',
                volume: '100.00',
                closeTime: 1234567890
            };
            (global.fetch as jest.Mock).mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve(mockResponse)
            });

            const marketData = await service.getMarketData('BTCUSDT');
            expect(marketData).toEqual({
                symbol: 'BTCUSDT',
                price: 50000.00,
                bid: 49990.00,
                ask: 50010.00,
                volume: 100.00,
                timestamp: 1234567890
            });
        });

        it('should get order book for a symbol', async () => {
            const mockResponse = {
                bids: [['50000.00', '1.00']],
                asks: [['50100.00', '1.00']]
            };
            (global.fetch as jest.Mock).mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve(mockResponse)
            });

            const orderBook = await service.getOrderBook('BTCUSDT');
            expect(orderBook.bids[0]).toEqual({
                price: 50000.00,
                quantity: 1.00
            });
            expect(orderBook.asks[0]).toEqual({
                price: 50100.00,
                quantity: 1.00
            });
        });
    });

    describe('Trading Methods', () => {
        it('should create a market order', async () => {
            const mockResponse = {
                orderId: '12345',
                symbol: 'BTCUSDT',
                side: 'BUY',
                type: 'MARKET',
                status: 'FILLED',
                price: '50000.00',
                origQty: '1.00',
                executedQty: '1.00',
                time: 1234567890
            };
            (global.fetch as jest.Mock).mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve(mockResponse)
            });

            const order = await service.createOrder({
                symbol: 'BTCUSDT',
                side: 'buy',
                type: 'market',
                quantity: 1.0
            });

            expect(order.id).toBe('12345');
            expect(order.status).toBe('filled');
            expect(order.filledQuantity).toBe(1.0);
        });

        it('should cancel an order', async () => {
            (global.fetch as jest.Mock).mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve({})
            });

            const result = await service.cancelOrder('BTCUSDT', '12345');
            expect(result).toBe(true);
            expect(global.fetch).toHaveBeenCalledWith(
                expect.stringContaining('/v3/order'),
                expect.objectContaining({
                    method: 'DELETE'
                })
            );
        });
    });

    describe('WebSocket Methods', () => {
        let mockWs: any;

        beforeEach(() => {
            mockWs = {
                on: jest.fn(),
                terminate: jest.fn()
            };
            (WebSocket as jest.Mock).mockImplementation(() => mockWs);
        });

        it('should subscribe to ticker updates', () => {
            const callback = jest.fn();
            service.subscribeToTicker('BTCUSDT', callback);

            expect(WebSocket).toHaveBeenCalledWith(
                expect.stringContaining('/btcusdt@ticker')
            );
            expect(mockWs.on).toHaveBeenCalledWith('message', expect.any(Function));
        });

        it('should handle ticker message correctly', () => {
            const callback = jest.fn();
            service.subscribeToTicker('BTCUSDT', callback);

            // Get the message handler
            const messageHandler = mockWs.on.mock.calls.find(
                call => call[0] === 'message'
            )[1];

            // Simulate a ticker message
            const mockTickerData = {
                e: '24hrTicker',
                s: 'BTCUSDT',
                c: '50000.00',
                b: '49990.00',
                a: '50010.00',
                v: '100.00',
                E: 1234567890
            };

            messageHandler(JSON.stringify(mockTickerData));

            expect(callback).toHaveBeenCalledWith({
                symbol: 'BTCUSDT',
                price: 50000.00,
                bid: 49990.00,
                ask: 50010.00,
                volume: 100.00,
                timestamp: 1234567890
            });
        });
    });

    describe('Error Handling', () => {
        it('should handle API errors correctly', async () => {
            const mockError = {
                code: -1121,
                msg: 'Invalid symbol'
            };
            (global.fetch as jest.Mock).mockResolvedValueOnce({
                ok: false,
                status: 400,
                statusText: 'Bad Request',
                json: () => Promise.resolve(mockError)
            });

            await expect(service.getPrice('INVALID')).rejects.toThrow();
        });

        it('should handle network errors correctly', async () => {
            (global.fetch as jest.Mock).mockRejectedValueOnce(
                new Error('Network error')
            );

            await expect(service.getPrice('BTCUSDT')).rejects.toThrow('Network error');
        });
    });
}); 