import { RiskManagementService } from '@/services/trading/riskManagementService';
import { OrderType, OrderSide } from '@/types/trading';
import { query } from '@/utils/db';

// Mock database queries
jest.mock('@/utils/db', () => ({
    query: jest.fn()
}));

describe('Risk Management Integration', () => {
    let riskManagementService: RiskManagementService;
    const mockQuery = query as jest.MockedFunction<typeof query>;
    const testUserId = 'test-user-id';
    const testAccountBalance = 100000;

    beforeEach(() => {
        riskManagementService = new RiskManagementService();
        mockQuery.mockClear();

        // Mock user risk settings
        mockQuery.mockImplementation((sql) => {
            if (sql.includes('SELECT * FROM user_risk_settings')) {
                return Promise.resolve({
                    rows: [{
                        max_position_size: 0.1,
                        max_daily_loss: 0.02,
                        max_drawdown: 0.1,
                        max_leverage: 3,
                        position_limit: 5,
                        max_correlation: 0.7,
                        risk_per_trade: 0.01
                    }]
                });
            }
            return Promise.resolve({ rows: [] });
        });
    });

    describe('Order Validation', () => {
        test('should validate order within risk limits', async () => {
            const validOrder = {
                symbol: 'BTC-USD',
                type: OrderType.LIMIT,
                side: OrderSide.BUY,
                quantity: 1,
                price: 45000,
                stopPrice: 44000
            };

            const validation = await riskManagementService.validateOrder(
                validOrder,
                testAccountBalance,
                testUserId
            );

            expect(validation.isValid).toBe(true);
            expect(validation.metrics.currentRisk).toBeLessThanOrEqual(0.01);
        });

        test('should reject order exceeding position size limit', async () => {
            const largeOrder = {
                symbol: 'BTC-USD',
                type: OrderType.MARKET,
                side: OrderSide.BUY,
                quantity: 3,
                price: 45000
            };

            const validation = await riskManagementService.validateOrder(
                largeOrder,
                testAccountBalance,
                testUserId
            );

            expect(validation.isValid).toBe(false);
            expect(validation.messages).toContain(expect.stringContaining('exceeds maximum'));
        });

        test('should reject order when daily loss limit reached', async () => {
            // Mock daily PnL at loss limit
            mockQuery.mockImplementationOnce(() => 
                Promise.resolve({
                    rows: [{ daily_pnl: -2000 }] // 2% of account balance
                })
            );

            const newOrder = {
                symbol: 'BTC-USD',
                type: OrderType.MARKET,
                side: OrderSide.BUY,
                quantity: 1,
                price: 45000
            };

            const validation = await riskManagementService.validateOrder(
                newOrder,
                testAccountBalance,
                testUserId
            );

            expect(validation.isValid).toBe(false);
            expect(validation.messages).toContain('Daily loss limit reached');
        });

        test('should reject order when position limit reached', async () => {
            // Mock existing positions at limit
            mockQuery.mockImplementationOnce(() => 
                Promise.resolve({
                    rows: Array(5).fill({ symbol: 'BTC-USD', status: 'OPEN' })
                })
            );

            const newOrder = {
                symbol: 'ETH-USD',
                type: OrderType.MARKET,
                side: OrderSide.BUY,
                quantity: 1,
                price: 2000
            };

            const validation = await riskManagementService.validateOrder(
                newOrder,
                testAccountBalance,
                testUserId
            );

            expect(validation.isValid).toBe(false);
            expect(validation.messages).toContain(expect.stringContaining('Maximum number of positions'));
        });
    });

    describe('Risk Metrics Management', () => {
        test('should load user risk settings', async () => {
            const metrics = await riskManagementService.getRiskMetricsForUser(testUserId);

            expect(metrics.maxPositionSize).toBe(0.1);
            expect(metrics.maxDailyLoss).toBe(0.02);
            expect(metrics.riskPerTrade).toBe(0.01);
        });

        test('should create default settings for new user', async () => {
            // Mock no existing settings
            mockQuery.mockImplementationOnce(() => Promise.resolve({ rows: [] }));

            const metrics = await riskManagementService.getRiskMetricsForUser('new-user');

            expect(metrics).toEqual(expect.objectContaining({
                maxPositionSize: 0.1,
                maxDailyLoss: 0.02,
                riskPerTrade: 0.01
            }));
        });

        test('should update user risk settings', async () => {
            const updates = {
                maxPositionSize: 0.15,
                maxDailyLoss: 0.03,
                riskPerTrade: 0.02
            };

            await riskManagementService.updateRiskMetrics(testUserId, updates);

            expect(mockQuery).toHaveBeenCalledWith(
                expect.stringContaining('UPDATE user_risk_settings'),
                expect.arrayContaining([
                    0.15,
                    0.03,
                    0.02
                ])
            );
        });
    });

    describe('Position Size Calculation', () => {
        test('should calculate position size based on risk per trade', async () => {
            const entryPrice = 45000;
            const stopPrice = 44000;
            const riskAmount = testAccountBalance * 0.01; // 1% risk
            const expectedSize = riskAmount / Math.abs(entryPrice - stopPrice);

            const size = await riskManagementService.calculatePositionSize(
                testAccountBalance,
                entryPrice,
                stopPrice
            );

            expect(size).toBe(expectedSize);
        });

        test('should limit position size to maximum allowed', async () => {
            const entryPrice = 45000;
            const stopPrice = 44900; // Small stop distance
            const maxSize = testAccountBalance * 0.1 / entryPrice; // 10% of account

            const size = await riskManagementService.calculatePositionSize(
                testAccountBalance,
                entryPrice,
                stopPrice
            );

            expect(size).toBeLessThanOrEqual(maxSize);
        });
    });
}); 