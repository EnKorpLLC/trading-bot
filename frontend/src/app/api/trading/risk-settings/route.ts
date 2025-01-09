import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { RiskSettings } from '@/types/trading';

// Simulated database for development
const riskSettings: { [key: string]: RiskSettings } = {};

const defaultSettings: RiskSettings = {
    maxPositionSize: 5, // 5% of account
    maxDailyLoss: 2, // 2% of account
    riskPerTrade: 1, // 1% of account
    maxDrawdown: 10, // 10% of account
    leverageLimit: 10, // 10x leverage
};

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

        const settings = riskSettings[userId] || defaultSettings;
        return NextResponse.json(settings);
    } catch (error) {
        console.error('Error fetching risk settings:', error);
        return NextResponse.json(
            { message: 'Internal server error' },
            { status: 500 }
        );
    }
}

export async function PUT(request: NextRequest) {
    try {
        const userId = request.url.split('/').pop();
        const body = await request.json();

        if (!userId) {
            return NextResponse.json(
                { message: 'User ID is required' },
                { status: 400 }
            );
        }

        // Validate settings
        if (body.maxPositionSize <= 0 || body.maxPositionSize > 100) {
            return NextResponse.json(
                { message: 'Maximum position size must be between 0 and 100%' },
                { status: 400 }
            );
        }

        if (body.maxDailyLoss <= 0 || body.maxDailyLoss > 100) {
            return NextResponse.json(
                { message: 'Maximum daily loss must be between 0 and 100%' },
                { status: 400 }
            );
        }

        if (body.riskPerTrade <= 0 || body.riskPerTrade > body.maxDailyLoss) {
            return NextResponse.json(
                { message: 'Risk per trade must be between 0 and maximum daily loss' },
                { status: 400 }
            );
        }

        if (body.maxDrawdown <= 0 || body.maxDrawdown > 100) {
            return NextResponse.json(
                { message: 'Maximum drawdown must be between 0 and 100%' },
                { status: 400 }
            );
        }

        if (body.leverageLimit <= 0) {
            return NextResponse.json(
                { message: 'Leverage limit must be greater than 0' },
                { status: 400 }
            );
        }

        // Update settings
        riskSettings[userId] = {
            ...defaultSettings,
            ...body,
        };

        return NextResponse.json(riskSettings[userId]);
    } catch (error) {
        console.error('Error updating risk settings:', error);
        return NextResponse.json(
            { message: 'Internal server error' },
            { status: 500 }
        );
    }
} 