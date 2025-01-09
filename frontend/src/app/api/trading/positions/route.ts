import { NextRequest, NextResponse } from 'next/server';
import { PositionService } from '@/services/trading/positionService';

const positionService = new PositionService();

export async function GET(req: NextRequest) {
    try {
        const { searchParams } = new URL(req.url);
        const userId = searchParams.get('userId');

        if (!userId) {
            return NextResponse.json(
                { message: 'User ID is required' },
                { status: 400 }
            );
        }

        // TODO: Validate that the requesting user has access to these positions
        const positions = await positionService.getAllPositions(userId);

        // For each position, calculate current unrealized P/L
        // In a real system, this would use current market prices
        const positionsWithPnL = await Promise.all(
            positions.map(async (position) => {
                const currentPrice = 0; // Replace with actual price
                const unrealizedPnL = await positionService.calculateUnrealizedPnL(
                    position,
                    currentPrice
                );
                return {
                    ...position,
                    unrealized_pnl: unrealizedPnL
                };
            })
        );

        return NextResponse.json({
            positions: positionsWithPnL,
            timestamp: new Date()
        });
    } catch (error) {
        console.error('Error fetching positions:', error);
        return NextResponse.json(
            { message: 'Internal server error' },
            { status: 500 }
        );
    }
} 