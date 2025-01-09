import { OrderExecutionService } from '@/services/trading/orderExecutionService';
import { RiskManagementService } from '@/services/trading/riskManagementService';
import { PositionService } from '@/services/trading/positionService';
import { OrderType, OrderSide } from '@/types/trading';
import { query } from '@/utils/db';

// Mock database queries
jest.mock('@/utils/db', () => ({
    query: jest.fn()
}));

describe('Order Execution Integration', () => {
    let orderExecutionService: OrderExecutionService;
    const mockQuery = query as jest.MockedFunction<typeof query>;
    const testUserId = 'test-user-id';

    beforeEach(() => {
        orderExecutionService = new OrderExecutionService();
        mockQuery.mockClear();
        
        // Mock account balance query
        mockQuery.mockImplementation((sql) => {
            if (sql.includes('SELECT balance FROM accounts')) {
                return Promise.resolve({ rows: [{ balance: 100000 }] });
            }
            return Promise.resolve({ rows: [] });
        });
    });

    describe('Market Order Flow', () => {
        test('should execute valid market order and update position', async () => {
            const marketOrder = {
                symbol: 'BTC-USD',
                type: OrderType.MARKET,
                side: OrderSide.BUY,
                quantity: 1,
                userId: testUserId
            };

            const response = await orderExecutionService.submitOrder(marketOrder, testUserId);

            expect(response.success).toBe(true);
            expect(response.order.status).toBe('FILLED');

            // Verify position update
            expect(mockQuery).toHaveBeenCalledWith(
                expect.stringContaining('INSERT INTO trades'),
                expect.arrayContaining([
                    testUserId,
                    'BTC-USD',
                    'BUY',
                    1
                ])
            );
        });

        test('should reject order exceeding risk limits', async () => {
            const largeOrder = {
                symbol: 'BTC-USD',
                type: OrderType.MARKET,
                side: OrderSide.BUY,
                quantity: 1000, // Exceeds position size limit
                userId: testUserId
            };

            const response = await orderExecutionService.submitOrder(largeOrder, testUserId);

            expect(response.success).toBe(false);
            expect(response.message).toContain('exceeds maximum');
        });
    });

    describe('Limit Order Flow', () => {
        test('should create pending limit order', async () => {
            const limitOrder = {
                symbol: 'BTC-USD',
                type: OrderType.LIMIT,
                side: OrderSide.BUY,
                quantity: 1,
                price: 45000,
                userId: testUserId
            };

            const response = await orderExecutionService.submitOrder(limitOrder, testUserId);

            expect(response.success).toBe(true);
            expect(response.order.status).toBe('PENDING');
            expect(mockQuery).toHaveBeenCalledWith(
                expect.stringContaining('INSERT INTO orders'),
                expect.arrayContaining([
                    'BTC-USD',
                    'BUY',
                    1,
                    'LIMIT',
                    'PENDING',
                    45000
                ])
            );
        });

        test('should execute limit order when price matches', async () => {
            const limitOrder = {
                symbol: 'BTC-USD',
                type: OrderType.LIMIT,
                side: OrderSide.BUY,
                quantity: 1,
                price: 45000,
                userId: testUserId
            };

            // Mock current price check
            mockQuery.mockImplementationOnce(() => 
                Promise.resolve({ rows: [{ price: 45000 }] })
            );

            const response = await orderExecutionService.submitOrder(limitOrder, testUserId);

            expect(response.success).toBe(true);
            expect(response.order.status).toBe('FILLED');
        });
    });

    describe('Stop Order Flow', () => {
        test('should create pending stop order', async () => {
            const stopOrder = {
                symbol: 'BTC-USD',
                type: OrderType.STOP,
                side: OrderSide.SELL,
                quantity: 1,
                stopPrice: 40000,
                userId: testUserId
            };

            const response = await orderExecutionService.submitOrder(stopOrder, testUserId);

            expect(response.success).toBe(true);
            expect(response.order.status).toBe('PENDING');
            expect(mockQuery).toHaveBeenCalledWith(
                expect.stringContaining('INSERT INTO orders'),
                expect.arrayContaining([
                    'BTC-USD',
                    'SELL',
                    1,
                    'STOP',
                    'PENDING',
                    null,
                    40000
                ])
            );
        });

        test('should trigger stop order when price reaches stop level', async () => {
            const stopOrder = {
                symbol: 'BTC-USD',
                type: OrderType.STOP,
                side: OrderSide.SELL,
                quantity: 1,
                stopPrice: 40000,
                userId: testUserId
            };

            await orderExecutionService.submitOrder(stopOrder, testUserId);

            // Simulate price reaching stop level
            await orderExecutionService.executeStopOrder('test-order-id', 39900);

            expect(mockQuery).toHaveBeenCalledWith(
                expect.stringContaining('UPDATE orders'),
                expect.arrayContaining([
                    'MARKET',
                    'PENDING',
                    'test-order-id'
                ])
            );
        });
    });

    describe('Position Management', () => {
        test('should update position after order execution', async () => {
            const marketOrder = {
                symbol: 'BTC-USD',
                type: OrderType.MARKET,
                side: OrderSide.BUY,
                quantity: 1,
                userId: testUserId
            };

            await orderExecutionService.submitOrder(marketOrder, testUserId);

            expect(mockQuery).toHaveBeenCalledWith(
                expect.stringContaining('INSERT INTO positions'),
                expect.arrayContaining([
                    testUserId,
                    'BTC-USD',
                    1,
                    'OPEN'
                ])
            );
        });

        test('should close position when fully exited', async () => {
            // Mock existing position
            mockQuery.mockImplementationOnce(() => 
                Promise.resolve({
                    rows: [{
                        symbol: 'BTC-USD',
                        quantity: 1,
                        status: 'OPEN'
                    }]
                })
            );

            const exitOrder = {
                symbol: 'BTC-USD',
                type: OrderType.MARKET,
                side: OrderSide.SELL,
                quantity: 1,
                userId: testUserId
            };

            await orderExecutionService.submitOrder(exitOrder, testUserId);

            expect(mockQuery).toHaveBeenCalledWith(
                expect.stringContaining('UPDATE positions'),
                expect.arrayContaining([
                    'CLOSED',
                    testUserId,
                    'BTC-USD'
                ])
            );
        });
    });
}); 