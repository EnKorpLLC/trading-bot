import { TradingDashboard } from '@/components/trading/TradingDashboard';

export default function TradingPage() {
    // TODO: Get actual user ID from auth
    const testUserId = 'test-user-id';

    return (
        <main className="min-h-screen bg-gray-50">
            <div data-testid="trading-dashboard">
                <TradingDashboard userId={testUserId} />
            </div>
        </main>
    );
} 