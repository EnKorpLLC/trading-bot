import { NextRequest, NextResponse } from 'next/server';
import { query } from '@/utils/db';

export async function GET(req: NextRequest) {
    try {
        const { searchParams } = new URL(req.url);
        const symbol = searchParams.get('symbol');
        const interval = searchParams.get('interval') || '1h'; // Default to 1 hour
        const limit = parseInt(searchParams.get('limit') || '100');

        if (!symbol) {
            return NextResponse.json(
                { message: 'Symbol is required' },
                { status: 400 }
            );
        }

        // Fetch price data from the database
        // In a real system, this would fetch from your market data provider
        const result = await query(
            `SELECT 
                time_bucket($1, timestamp) as time,
                first(price, timestamp) as open,
                max(price) as high,
                min(price) as low,
                last(price, timestamp) as close,
                sum(volume) as volume
            FROM market_data
            WHERE symbol = $2
            GROUP BY time_bucket($1, timestamp)
            ORDER BY time DESC
            LIMIT $3`,
            [interval, symbol, limit]
        );

        return NextResponse.json({
            prices: result.rows.map(row => ({
                ...row,
                time: row.time.toISOString(),
            })),
            symbol,
            interval,
            timestamp: new Date()
        });
    } catch (error) {
        console.error('Error fetching prices:', error);
        return NextResponse.json(
            { message: 'Internal server error' },
            { status: 500 }
        );
    }
} 