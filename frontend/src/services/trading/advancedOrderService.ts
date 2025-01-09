import { MarketDataService } from './marketDataService';
import { OrderType, OrderSide, Order, Position } from '@/types/trading';

interface StopLossConfig {
    price: number;
    quantity?: number; // If not provided, close entire position
}

interface TakeProfitConfig {
    price: number;
    quantity?: number; // If not provided, close entire position
}

interface TrailingStopConfig {
    offset: number; // Price distance or percentage
    isPercentage?: boolean;
    quantity?: number;
}

export class AdvancedOrderService {
    private marketDataService: MarketDataService;
    private trailingStops: Map<string, Map<string, TrailingStopConfig>> = new Map(); // positionId -> orderId -> config

    constructor(marketDataService: MarketDataService) {
        this.marketDataService = marketDataService;
    }

    public async createStopLossOrder(
        position: Position,
        config: StopLossConfig
    ): Promise<Order> {
        const quantity = config.quantity || position.quantity;
        const side = position.side === OrderSide.BUY ? OrderSide.SELL : OrderSide.BUY;

        const order: Partial<Order> = {
            symbol: position.symbol,
            type: OrderType.STOP,
            side,
            quantity,
            stopPrice: config.price,
            timeInForce: 'GTC',
            parentOrderId: position.id
        };

        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/trading/orders`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(order)
        });

        if (!response.ok) {
            throw new Error('Failed to create stop-loss order');
        }

        return response.json();
    }

    public async createTakeProfitOrder(
        position: Position,
        config: TakeProfitConfig
    ): Promise<Order> {
        const quantity = config.quantity || position.quantity;
        const side = position.side === OrderSide.BUY ? OrderSide.SELL : OrderSide.BUY;

        const order: Partial<Order> = {
            symbol: position.symbol,
            type: OrderType.LIMIT,
            side,
            quantity,
            price: config.price,
            timeInForce: 'GTC',
            parentOrderId: position.id
        };

        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/trading/orders`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(order)
        });

        if (!response.ok) {
            throw new Error('Failed to create take-profit order');
        }

        return response.json();
    }

    public async createTrailingStopOrder(
        position: Position,
        config: TrailingStopConfig
    ): Promise<Order> {
        const quantity = config.quantity || position.quantity;
        const side = position.side === OrderSide.BUY ? OrderSide.SELL : OrderSide.BUY;

        const order: Partial<Order> = {
            symbol: position.symbol,
            type: OrderType.TRAILING_STOP,
            side,
            quantity,
            trailingOffset: config.offset,
            timeInForce: 'GTC',
            parentOrderId: position.id
        };

        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/trading/orders`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(order)
        });

        if (!response.ok) {
            throw new Error('Failed to create trailing stop order');
        }

        const createdOrder = await response.json();

        // Start tracking the trailing stop
        if (!this.trailingStops.has(position.id)) {
            this.trailingStops.set(position.id, new Map());
        }
        this.trailingStops.get(position.id)!.set(createdOrder.id, config);

        // Subscribe to price updates for this symbol
        this.marketDataService.subscribeToPriceUpdates(
            position.symbol,
            this.handlePriceUpdate.bind(this, position.id, createdOrder.id)
        );

        return createdOrder;
    }

    private handlePriceUpdate(positionId: string, orderId: string, price: number): void {
        const stopConfig = this.trailingStops.get(positionId)?.get(orderId);
        if (!stopConfig) return;

        // Update trailing stop price based on current market price
        this.updateTrailingStop(positionId, orderId, price, stopConfig);
    }

    private async updateTrailingStop(
        positionId: string,
        orderId: string,
        currentPrice: number,
        config: TrailingStopConfig
    ): Promise<void> {
        const offset = config.isPercentage
            ? currentPrice * (config.offset / 100)
            : config.offset;

        const response = await fetch(
            `${process.env.NEXT_PUBLIC_API_URL}/trading/orders/${orderId}`,
            {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    stopPrice: currentPrice - offset
                })
            }
        );

        if (!response.ok) {
            console.error('Failed to update trailing stop:', await response.text());
        }
    }

    public async createBracketOrder(
        position: Position,
        stopLoss: StopLossConfig,
        takeProfit: TakeProfitConfig
    ): Promise<Order[]> {
        const orders: Order[] = [];

        // Create stop-loss order
        const stopLossOrder = await this.createStopLossOrder(position, stopLoss);
        orders.push(stopLossOrder);

        // Create take-profit order
        const takeProfitOrder = await this.createTakeProfitOrder(position, takeProfit);
        orders.push(takeProfitOrder);

        return orders;
    }

    public async cancelOrder(orderId: string): Promise<void> {
        const response = await fetch(
            `${process.env.NEXT_PUBLIC_API_URL}/trading/orders/${orderId}`,
            {
                method: 'DELETE'
            }
        );

        if (!response.ok) {
            throw new Error('Failed to cancel order');
        }

        // Clean up trailing stop tracking if necessary
        this.trailingStops.forEach((orderMap, positionId) => {
            if (orderMap.has(orderId)) {
                orderMap.delete(orderId);
                if (orderMap.size === 0) {
                    this.trailingStops.delete(positionId);
                }
            }
        });
    }

    public async modifyOrder(
        orderId: string,
        updates: Partial<Order>
    ): Promise<Order> {
        const response = await fetch(
            `${process.env.NEXT_PUBLIC_API_URL}/trading/orders/${orderId}`,
            {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updates)
            }
        );

        if (!response.ok) {
            throw new Error('Failed to modify order');
        }

        return response.json();
    }
} 