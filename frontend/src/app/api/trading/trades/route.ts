import { NextRequest, NextResponse } from 'next/server';
import { query } from '@/utils/db';
import type { NextRequest } from 'next/server';
import { Trade } from '@/types/trading';

// Simulated database for development
let trades: Trade[] = [];

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

        const userTrades = trades.filter(trade => trade.userId === userId);
        
        // Sort trades by timestamp in descending order
        userTrades.sort((a, b) => 
            new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
        );

        return NextResponse.json(userTrades);
    } catch (error) {
        console.error('Error fetching trades:', error);
        return NextResponse.json(
            { message: 'Internal server error' },
            { status: 500 }
        );
    }
}

// This endpoint is called internally when an order is filled
export async function POST(request: NextRequest) {
    try {
        const body = await request.json();
        const { userId, orderId, symbol, side, type, size, price } = body;

        if (!userId || !orderId || !symbol || !side || !type || !size || !price) {
            return NextResponse.json(
                { message: 'Missing required fields' },
                { status: 400 }
            );
        }

        const newTrade: Trade = {
            id: `trade-${Date.now()}`,
            userId,
            orderId,
            symbol,
            side,
            type,
            size,
            price,
            value: size * price,
            fee: size * price * 0.001, // 0.1% fee
            timestamp: new Date().toISOString(),
        };

        trades.push(newTrade);

        return NextResponse.json(newTrade, { status: 201 });
    } catch (error) {
        console.error('Error creating trade:', error);
        return NextResponse.json(
            { message: 'Internal server error' },
            { status: 500 }
        );
    }
} 