import { useState, useEffect } from 'react';
import { OrderEntryForm } from './OrderEntryForm';
import { PositionDisplay } from './PositionDisplay';
import { TradeHistory } from './TradeHistory';
import { RiskManagement } from './RiskManagement';
import { tradingService } from '@/services/trading/tradingService';
import { Order, Position, Trade, RiskSettings } from '@/types/trading';

interface TradingDashboardProps {
    userId: string;
}

export function TradingDashboard({ userId }: TradingDashboardProps) {
    const [positions, setPositions] = useState<Position[]>([]);
    const [trades, setTrades] = useState<Trade[]>([]);
    const [riskSettings, setRiskSettings] = useState<RiskSettings | null>(null);
    const [isSubmittingOrder, setIsSubmittingOrder] = useState(false);
    const [isClosingPosition, setIsClosingPosition] = useState<{ [key: string]: boolean }>({});
    const [isUpdatingRisk, setIsUpdatingRisk] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Fetch initial data
    useEffect(() => {
        const fetchData = async () => {
            try {
                const [positionsData, tradesData, riskData] = await Promise.all([
                    tradingService.getPositions(userId),
                    tradingService.getTrades(userId),
                    tradingService.getRiskSettings(userId),
                ]);

                setPositions(positionsData);
                setTrades(tradesData);
                setRiskSettings(riskData);
            } catch (error) {
                console.error('Error fetching data:', error);
                setError('Failed to load trading data');
            }
        };

        fetchData();

        // Set up polling for real-time updates
        const intervalId = setInterval(fetchData, 5000);
        return () => clearInterval(intervalId);
    }, [userId]);

    const handleOrderSubmit = async (order: Partial<Order>) => {
        setError(null);
        setIsSubmittingOrder(true);

        try {
            await tradingService.submitOrder({
                ...order,
                userId,
            });

            // Refresh positions and trades
            const [positionsData, tradesData] = await Promise.all([
                tradingService.getPositions(userId),
                tradingService.getTrades(userId),
            ]);

            setPositions(positionsData);
            setTrades(tradesData);
        } catch (error) {
            console.error('Error submitting order:', error);
            setError('Failed to submit order');
        } finally {
            setIsSubmittingOrder(false);
        }
    };

    const handleClosePosition = async (positionId: string) => {
        setError(null);
        setIsClosingPosition(prev => ({ ...prev, [positionId]: true }));

        try {
            await tradingService.closePosition(positionId);

            // Refresh positions and trades
            const [positionsData, tradesData] = await Promise.all([
                tradingService.getPositions(userId),
                tradingService.getTrades(userId),
            ]);

            setPositions(positionsData);
            setTrades(tradesData);
        } catch (error) {
            console.error('Error closing position:', error);
            setError('Failed to close position');
        } finally {
            setIsClosingPosition(prev => ({ ...prev, [positionId]: false }));
        }
    };

    const handleUpdateRiskSettings = async (settings: RiskSettings) => {
        setError(null);
        setIsUpdatingRisk(true);

        try {
            const updatedSettings = await tradingService.updateRiskSettings(userId, settings);
            setRiskSettings(updatedSettings);
        } catch (error) {
            console.error('Error updating risk settings:', error);
            setError('Failed to update risk settings');
        } finally {
            setIsUpdatingRisk(false);
        }
    };

    return (
        <div className="container mx-auto px-4 py-8">
            {error && (
                <div className="mb-4 bg-red-50 border border-red-200 rounded-md p-4">
                    <p className="text-red-800">{error}</p>
                </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Order Entry */}
                <div className="lg:col-span-1">
                    <div className="bg-white rounded-lg shadow-lg p-6">
                        <h2 className="text-xl font-semibold mb-4">New Order</h2>
                        <OrderEntryForm
                            onSubmit={handleOrderSubmit}
                            isSubmitting={isSubmittingOrder}
                        />
                    </div>
                </div>

                {/* Risk Management */}
                <div className="lg:col-span-2">
                    <div className="bg-white rounded-lg shadow-lg p-6">
                        <h2 className="text-xl font-semibold mb-4">Risk Management</h2>
                        {riskSettings && (
                            <RiskManagement
                                initialSettings={riskSettings}
                                onSave={handleUpdateRiskSettings}
                                isSubmitting={isUpdatingRisk}
                            />
                        )}
                    </div>
                </div>
            </div>

            {/* Positions */}
            <div className="mt-8">
                <div className="bg-white rounded-lg shadow-lg p-6">
                    <h2 className="text-xl font-semibold mb-4">Open Positions</h2>
                    <PositionDisplay
                        positions={positions}
                        onClosePosition={handleClosePosition}
                        isClosing={isClosingPosition}
                    />
                </div>
            </div>

            {/* Trade History */}
            <div className="mt-8">
                <div className="bg-white rounded-lg shadow-lg p-6">
                    <h2 className="text-xl font-semibold mb-4">Trade History</h2>
                    <TradeHistory trades={trades} />
                </div>
            </div>
        </div>
    );
} 