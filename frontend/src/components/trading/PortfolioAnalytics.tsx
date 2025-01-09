import { useEffect, useState } from 'react';
import type { PortfolioMetrics, Position } from '@/types/trading';
import { tradingService } from '@/services/trading/tradingService';

interface PortfolioAnalyticsProps {
  userId: string;
  onPositionSelect?: (position: Position) => void;
}

export default function PortfolioAnalytics({ userId, onPositionSelect }: PortfolioAnalyticsProps) {
  const [metrics, setMetrics] = useState<PortfolioMetrics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadMetrics = async () => {
      try {
        setIsLoading(true);
        const data = await tradingService.getPortfolioMetrics(userId);
        setMetrics(data);
        setError(null);
      } catch (err) {
        setError('Failed to load portfolio metrics');
        console.error('Error loading portfolio metrics:', err);
      } finally {
        setIsLoading(false);
      }
    };

    loadMetrics();
    const interval = setInterval(loadMetrics, 60000); // Refresh every minute

    return () => clearInterval(interval);
  }, [userId]);

  if (isLoading) {
    return (
      <div className="p-4 text-center">
        Loading portfolio metrics...
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 text-center text-red-500">
        {error}
      </div>
    );
  }

  if (!metrics) {
    return (
      <div className="p-4 text-center">
        No portfolio data available
      </div>
    );
  }

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value);
  };

  const formatPercentage = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'percent',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value / 100);
  };

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h2 className="text-xl font-semibold mb-4">Portfolio Analytics</h2>
      
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="p-3 bg-gray-50 rounded">
          <div className="text-sm text-gray-500">Total Value</div>
          <div className="text-lg font-semibold">{formatCurrency(metrics.totalValue)}</div>
        </div>
        
        <div className="p-3 bg-gray-50 rounded">
          <div className="text-sm text-gray-500">Daily P&L</div>
          <div className={`text-lg font-semibold ${metrics.dailyPnL >= 0 ? 'text-green-500' : 'text-red-500'}`}>
            {formatCurrency(metrics.dailyPnL)}
          </div>
        </div>
        
        <div className="p-3 bg-gray-50 rounded">
          <div className="text-sm text-gray-500">Total P&L</div>
          <div className={`text-lg font-semibold ${metrics.totalPnL >= 0 ? 'text-green-500' : 'text-red-500'}`}>
            {formatCurrency(metrics.totalPnL)}
          </div>
        </div>
        
        <div className="p-3 bg-gray-50 rounded">
          <div className="text-sm text-gray-500">Margin Usage</div>
          <div className="text-lg font-semibold">{formatPercentage(metrics.marginUsage)}</div>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="p-3 bg-gray-50 rounded">
          <div className="text-sm text-gray-500">Leverage</div>
          <div className="text-lg font-semibold">{metrics.leverage.toFixed(2)}x</div>
        </div>
        
        <div className="p-3 bg-gray-50 rounded">
          <div className="text-sm text-gray-500">Drawdown</div>
          <div className="text-lg font-semibold text-red-500">
            {formatPercentage(metrics.drawdown)}
          </div>
        </div>
        
        <div className="p-3 bg-gray-50 rounded">
          <div className="text-sm text-gray-500">Sharpe Ratio</div>
          <div className="text-lg font-semibold">{metrics.sharpeRatio.toFixed(2)}</div>
        </div>
        
        <div className="p-3 bg-gray-50 rounded">
          <div className="text-sm text-gray-500">Margin</div>
          <div className="text-lg font-semibold">{formatCurrency(metrics.margin)}</div>
        </div>
      </div>

      <div className="mb-4">
        <h3 className="text-lg font-semibold mb-2">Open Positions</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead>
              <tr>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Symbol
                </th>
                <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Quantity
                </th>
                <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Entry Price
                </th>
                <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Current Price
                </th>
                <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Unrealized P&L
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {metrics.positions.map((position) => (
                <tr
                  key={position.id}
                  className="hover:bg-gray-50 cursor-pointer"
                  onClick={() => onPositionSelect?.(position)}
                >
                  <td className="px-4 py-2 whitespace-nowrap">
                    {position.symbol}
                  </td>
                  <td className="px-4 py-2 text-right whitespace-nowrap">
                    {position.quantity.toFixed(4)}
                  </td>
                  <td className="px-4 py-2 text-right whitespace-nowrap">
                    {formatCurrency(position.averageEntryPrice)}
                  </td>
                  <td className="px-4 py-2 text-right whitespace-nowrap">
                    {formatCurrency(position.currentPrice)}
                  </td>
                  <td className={`px-4 py-2 text-right whitespace-nowrap ${
                    position.unrealizedPnL >= 0 ? 'text-green-500' : 'text-red-500'
                  }`}>
                    {formatCurrency(position.unrealizedPnL)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
} 