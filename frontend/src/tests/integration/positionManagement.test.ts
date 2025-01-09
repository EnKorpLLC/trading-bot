import { PositionService } from '@/services/trading/positionService';
import { OrderType, OrderSide, Trade } from '@/types/trading';
import { query } from '@/utils/db';

// Mock database queries
jest.mock('@/utils/db', () => ({
    query: jest.fn()
}));

describe('Position Management Integration', () => {
    let positionService: PositionService;
    const mockQuery = query as jest.MockedFunction<typeof query>;
    const testUserId = 'test-user-id';

    beforeEach(() => {
        positionService = new PositionService();
        mockQuery.mockClear();
    });

    describe('Position Creation', () => {
        test('should create new position from market buy', async () => {
            const trade: Trade = {
                id: 'trade-1',
                orderId: 'order-1',
                userId: testUserId,
                symbol: 'BTC-USD',
                side: OrderSide.BUY,
                type: OrderType.MARKET,
                quantity: 1,
                price: 45000,
                executedAt: new Date()
            };

            await positionService.updatePosition(trade);

            expect(mockQuery).toHaveBeenCalledWith(
                expect.stringContaining('INSERT INTO positions'),
                expect.arrayContaining([
                    testUserId,
                    'BTC-USD',
                    1,
                    45000,
                    'OPEN'
                ])
            );
        });

        test('should handle multiple trades for same position', async () => {
            // Mock existing position
            mockQuery.mockImplementationOnce(() => 
                Promise.resolve({
                    rows: [{
                        symbol: 'BTC-USD',
                        quantity: 1,
                        average_entry_price: 45000,
                        status: 'OPEN'
                    }]
                })
            );

            const trade: Trade = {
                id: 'trade-2',
                orderId: 'order-2',
                userId: testUserId,
                symbol: 'BTC-USD',
                side: OrderSide.BUY,
                type: OrderType.MARKET,
                quantity: 0.5,
                price: 46000,
                executedAt: new Date()
            };

            await positionService.updatePosition(trade);

            expect(mockQuery).toHaveBeenCalledWith(
                expect.stringContaining('UPDATE positions'),
                expect.arrayContaining([
                    1.5, // New quantity
                    45333.33, // New average price (approximately)
                    testUserId,
                    'BTC-USD'
                ])
            );
        });
    });

    describe('Position Closure', () => {
        test('should close position on full exit', async () => {
            // Mock existing position
            mockQuery.mockImplementationOnce(() => 
                Promise.resolve({
                    rows: [{
                        symbol: 'BTC-USD',
                        quantity: 1,
                        average_entry_price: 45000,
                        status: 'OPEN'
                    }]
                })
            );

            const trade: Trade = {
                id: 'trade-3',
                orderId: 'order-3',
                userId: testUserId,
                symbol: 'BTC-USD',
                side: OrderSide.SELL,
                type: OrderType.MARKET,
                quantity: 1,
                price: 46000,
                executedAt: new Date()
            };

            await positionService.updatePosition(trade);

            expect(mockQuery).toHaveBeenCalledWith(
                expect.stringContaining('UPDATE positions'),
                expect.arrayContaining([
                    'CLOSED',
                    testUserId,
                    'BTC-USD'
                ])
            );
        });

        test('should handle partial position closure', async () => {
            // Mock existing position
            mockQuery.mockImplementationOnce(() => 
                Promise.resolve({
                    rows: [{
                        symbol: 'BTC-USD',
                        quantity: 2,
                        average_entry_price: 45000,
                        status: 'OPEN'
                    }]
                })
            );

            const trade: Trade = {
                id: 'trade-4',
                orderId: 'order-4',
                userId: testUserId,
                symbol: 'BTC-USD',
                side: OrderSide.SELL,
                type: OrderType.MARKET,
                quantity: 1,
                price: 46000,
                executedAt: new Date()
            };

            await positionService.updatePosition(trade);

            expect(mockQuery).toHaveBeenCalledWith(
                expect.stringContaining('UPDATE positions'),
                expect.arrayContaining([
                    1, // Remaining quantity
                    45000, // Original average price
                    testUserId,
                    'BTC-USD'
                ])
            );
        });
    });

    describe('Position Retrieval', () => {
        test('should get all open positions', async () => {
            mockQuery.mockImplementationOnce(() => 
                Promise.resolve({
                    rows: [
                        {
                            symbol: 'BTC-USD',
                            quantity: 1,
                            average_entry_price: 45000,
                            status: 'OPEN'
                        },
                        {
                            symbol: 'ETH-USD',
                            quantity: 10,
                            average_entry_price: 2000,
                            status: 'OPEN'
                        }
                    ]
                })
            );

            const positions = await positionService.getCurrentPositions(testUserId);

            expect(positions).toHaveLength(2);
            expect(positions[0].symbol).toBe('BTC-USD');
            expect(positions[1].symbol).toBe('ETH-USD');
        });

        test('should calculate position PnL', async () => {
            mockQuery.mockImplementationOnce(() => 
                Promise.resolve({
                    rows: [{
                        symbol: 'BTC-USD',
                        quantity: 1,
                        average_entry_price: 45000,
                        status: 'OPEN',
                        current_price: 46000
                    }]
                })
            );

            const positions = await positionService.getCurrentPositions(testUserId);

            expect(positions[0].unrealizedPnl).toBe(1000);
            expect(positions[0].unrealizedPnlPercentage).toBe(0.0222); // 2.22%
        });
    });

    describe('Position History', () => {
        test('should get closed position history', async () => {
            mockQuery.mockImplementationOnce(() => 
                Promise.resolve({
                    rows: [
                        {
                            symbol: 'BTC-USD',
                            quantity: 1,
                            average_entry_price: 45000,
                            exit_price: 46000,
                            status: 'CLOSED',
                            closed_at: new Date(),
                            realized_pnl: 1000
                        }
                    ]
                })
            );

            const history = await positionService.getPositionHistory(testUserId);

            expect(history[0].status).toBe('CLOSED');
            expect(history[0].realizedPnl).toBe(1000);
        });

        test('should calculate position metrics', async () => {
            mockQuery.mockImplementationOnce(() => 
                Promise.resolve({
                    rows: [
                        {
                            symbol: 'BTC-USD',
                            quantity: 1,
                            average_entry_price: 45000,
                            exit_price: 46000,
                            status: 'CLOSED',
                            closed_at: new Date(),
                            realized_pnl: 1000,
                            holding_period: '2 days'
                        }
                    ]
                })
            );

            const history = await positionService.getPositionHistory(testUserId);

            expect(history[0].realizedPnlPercentage).toBe(0.0222); // 2.22%
            expect(history[0].holdingPeriod).toBe('2 days');
        });
    });
}); 