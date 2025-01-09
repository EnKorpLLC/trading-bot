import { 
    Order, 
    OrderRequest, 
    OrderResponse, 
    OrderStatus, 
    OrderType,
    MarketOrder,
    LimitOrder,
    Trade
} from '@/types/trading';
import { query } from '@/utils/db';
import { PositionService } from './positionService';
import { RiskManagementService } from './riskManagementService';

class OrderValidationError extends Error {
    constructor(message: string) {
        super(message);
        this.name = 'OrderValidationError';
    }
}

export class OrderExecutionService {
    private positionService: PositionService;
    private riskManagementService: RiskManagementService;

    constructor() {
        this.positionService = new PositionService();
        this.riskManagementService = new RiskManagementService();
    }

    private async validateOrder(order: OrderRequest, userId: string): Promise<void> {
        if (!order.symbol) {
            throw new OrderValidationError('Symbol is required');
        }
        if (!order.side) {
            throw new OrderValidationError('Order side is required');
        }
        if (!order.quantity || order.quantity <= 0) {
            throw new OrderValidationError('Invalid quantity');
        }
        if (!order.type) {
            throw new OrderValidationError('Order type is required');
        }

        // Get account balance
        const accountInfo = await this.getAccountInfo(userId);
        
        // Validate against risk management rules
        const riskValidation = await this.riskManagementService.validateOrder(
            order,
            accountInfo.balance,
            userId
        );

        if (!riskValidation.isValid) {
            throw new OrderValidationError(riskValidation.messages.join('. '));
        }

        // Validate price for limit orders
        if ((order.type === OrderType.LIMIT || order.type === OrderType.STOP_LIMIT) && !order.price) {
            throw new OrderValidationError('Price is required for limit orders');
        }

        // Validate stop price for stop orders
        if ((order.type === OrderType.STOP || order.type === OrderType.STOP_LIMIT) && !order.stopPrice) {
            throw new OrderValidationError('Stop price is required for stop orders');
        }
    }

    private async getAccountInfo(userId: string): Promise<{ balance: number }> {
        const result = await query(
            'SELECT balance FROM accounts WHERE user_id = $1',
            [userId]
        );
        return result.rows[0] || { balance: 0 };
    }

    private async createOrderRecord(order: Order): Promise<string> {
        const result = await query(
            `INSERT INTO orders (
                symbol, side, quantity, type, status, 
                time_in_force, user_id, client_order_id,
                price, stop_price
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            RETURNING id`,
            [
                order.symbol,
                order.side,
                order.quantity,
                order.type,
                order.status,
                order.timeInForce,
                order.userId,
                order.clientOrderId,
                'price' in order ? order.price : null,
                'stopPrice' in order ? order.stopPrice : null
            ]
        );

        return result.rows[0].id;
    }

    private async createTradeRecord(order: Order, orderId: string, executionPrice: number): Promise<Trade> {
        const result = await query(
            `INSERT INTO trades (
                order_id, user_id, symbol, side, 
                type, quantity, price, executed_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
            RETURNING *`,
            [
                orderId,
                order.userId,
                order.symbol,
                order.side,
                order.type,
                order.quantity,
                executionPrice
            ]
        );

        const trade = result.rows[0];
        
        // Update position
        await this.positionService.updatePosition(trade);

        return trade;
    }

    private async executeMarketOrder(order: MarketOrder): Promise<OrderResponse> {
        try {
            // Create the order record
            const orderId = await this.createOrderRecord({
                ...order,
                status: OrderStatus.PENDING
            });

            // In a real system, we would get the actual market price
            const executionPrice = 0; // Replace with actual price

            // Create trade record and update position
            const trade = await this.createTradeRecord(order, orderId, executionPrice);

            // Update order status
            await query(
                `UPDATE orders 
                SET status = $1, updated_at = NOW() 
                WHERE id = $2`,
                [OrderStatus.FILLED, orderId]
            );

            return {
                order: {
                    ...order,
                    id: orderId,
                    status: OrderStatus.FILLED,
                    createdAt: new Date(),
                    updatedAt: new Date()
                },
                message: 'Order executed successfully',
                success: true,
                timestamp: new Date()
            };
        } catch (error) {
            console.error('Error executing market order:', error);
            throw error;
        }
    }

    private async executeLimitOrder(order: LimitOrder): Promise<OrderResponse> {
        try {
            const orderId = await this.createOrderRecord({
                ...order,
                status: OrderStatus.PENDING
            });

            // Simulate checking current price
            const currentPrice = 0; // Replace with actual price check
            const canExecute = order.side === 'BUY' ? 
                currentPrice <= order.price : 
                currentPrice >= order.price;

            if (canExecute) {
                // Create trade record and update position
                const trade = await this.createTradeRecord(order, orderId, order.price);

                // Update order status
                await query(
                    `UPDATE orders 
                    SET status = $1, updated_at = NOW() 
                    WHERE id = $2`,
                    [OrderStatus.FILLED, orderId]
                );

                return {
                    order: {
                        ...order,
                        id: orderId,
                        status: OrderStatus.FILLED,
                        createdAt: new Date(),
                        updatedAt: new Date()
                    },
                    message: 'Limit order executed successfully',
                    success: true,
                    timestamp: new Date()
                };
            } else {
                return {
                    order: {
                        ...order,
                        id: orderId,
                        status: OrderStatus.PENDING,
                        createdAt: new Date(),
                        updatedAt: new Date()
                    },
                    message: 'Limit order accepted and pending',
                    success: true,
                    timestamp: new Date()
                };
            }
        } catch (error) {
            console.error('Error executing limit order:', error);
            throw error;
        }
    }

    async executeStopOrder(orderId: string, currentPrice: number): Promise<void> {
        const order = (await query(
            'SELECT * FROM orders WHERE id = $1',
            [orderId]
        )).rows[0];

        if (!order) {
            throw new Error('Order not found');
        }

        // Check if stop price is triggered
        const isTriggered = order.side === 'BUY' 
            ? currentPrice >= order.stopPrice
            : currentPrice <= order.stopPrice;

        if (isTriggered) {
            // Convert to market order and execute
            await query(
                `UPDATE orders 
                SET type = $1, status = $2 
                WHERE id = $3`,
                [OrderType.MARKET, OrderStatus.PENDING, orderId]
            );
            await this.executeMarketOrder(order);
        }
    }

    public async submitOrder(orderRequest: OrderRequest, userId: string): Promise<OrderResponse> {
        try {
            // Validate the order
            await this.validateOrder(orderRequest, userId);

            // Get account info for risk calculations
            const accountInfo = await this.getAccountInfo(userId);

            // Calculate position size if not specified
            if (!orderRequest.quantity && orderRequest.stopPrice) {
                orderRequest.quantity = await this.riskManagementService.calculatePositionSize(
                    accountInfo.balance,
                    orderRequest.price || 0,
                    orderRequest.stopPrice
                );
            }

            // Create base order
            const baseOrder = {
                ...orderRequest,
                userId,
                status: OrderStatus.PENDING,
                createdAt: new Date(),
                updatedAt: new Date()
            };

            // Process based on order type
            switch (orderRequest.type) {
                case OrderType.MARKET:
                    return this.executeMarketOrder(baseOrder as MarketOrder);
                case OrderType.LIMIT:
                    return this.executeLimitOrder(baseOrder as LimitOrder);
                case OrderType.STOP:
                    return this.executeStopOrder(baseOrder);
                case OrderType.STOP_LIMIT:
                    return this.executeStopLimitOrder(baseOrder);
                default:
                    throw new OrderValidationError('Invalid order type');
            }
        } catch (error) {
            if (error instanceof OrderValidationError) {
                return {
                    order: null,
                    message: error.message,
                    success: false,
                    timestamp: new Date()
                };
            }
            throw error;
        }
    }
} 