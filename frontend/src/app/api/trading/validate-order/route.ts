import { NextRequest, NextResponse } from 'next/server';
import { RiskManagementService } from '@/services/trading/riskManagementService';

const riskManagementService = new RiskManagementService();

export async function POST(req: NextRequest) {
    try {
        const body = await req.json();
        const { order, accountBalance } = body;

        // TODO: Get actual user ID from session/auth
        const userId = 'test-user-id';

        const validation = await riskManagementService.validateOrder(
            order,
            accountBalance,
            userId
        );

        return NextResponse.json(validation);
    } catch (error) {
        console.error('Error validating order:', error);
        return NextResponse.json(
            {
                isValid: false,
                messages: [(error as Error).message || 'Internal server error'],
                metrics: {
                    currentRisk: 0,
                    exposurePercentage: 0,
                    marginUsage: 0,
                    availableMargin: 0
                }
            },
            { status: 500 }
        );
    }
} 