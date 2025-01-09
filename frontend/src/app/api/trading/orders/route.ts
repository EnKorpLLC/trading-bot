import { NextRequest, NextResponse } from 'next/server';
import { OrderExecutionService } from '@/services/trading/orderExecutionService';
import { OrderRequest } from '@/types/trading';
import { Order, OrderStatus } from '@/types/trading';

const orderService = new OrderExecutionService();

// Simulated database for development
let orders: Order[] = [];

export async function POST(req: NextRequest) {
    try {
        const body = await req.json();
        const orderRequest = body as OrderRequest;

        // TODO: Get actual user ID from session/auth
        const userId = 'test-user-id';

        const response = await orderService.submitOrder(orderRequest, userId);

        if (!response.success) {
            return NextResponse.json(response, { status: 400 });
        }

        return NextResponse.json(response);
    } catch (error) {
        console.error('Error processing order:', error);
        return NextResponse.json({
            order: null,
            message: 'Internal server error',
            success: false,
            timestamp: new Date()
        }, { status: 500 });
    }
}

export async function GET(request: NextRequest) {
    try {
        const { searchParams } = new URL(request.url);
        const userId = searchParams.get('userId');

        if (!userId) {
            return NextResponse.json(
                { message: 'User ID is required' },
                { status: 400 }
            );
        }

        const userOrders = orders.filter(order => order.userId === userId);
        return NextResponse.json(userOrders);
    } catch (error) {
        console.error('Error fetching orders:', error);
        return NextResponse.json(
            { message: 'Internal server error' },
            { status: 500 }
        );
    }
}

export async function DELETE(request: NextRequest) {
    try {
        const orderId = request.url.split('/').pop();

        if (!orderId) {
            return NextResponse.json(
                { message: 'Order ID is required' },
                { status: 400 }
            );
        }

        const orderIndex = orders.findIndex(order => order.id === orderId);

        if (orderIndex === -1) {
            return NextResponse.json(
                { message: 'Order not found' },
                { status: 404 }
            );
        }

        // Update order status to cancelled
        orders[orderIndex] = {
            ...orders[orderIndex],
            status: OrderStatus.CANCELLED,
        };

        return NextResponse.json({ message: 'Order cancelled successfully' });
    } catch (error) {
        console.error('Error cancelling order:', error);
        return NextResponse.json(
            { message: 'Internal server error' },
            { status: 500 }
        );
    }
} 