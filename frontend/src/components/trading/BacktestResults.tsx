import { useMemo } from 'react';
import type { BacktestResult, Trade } from '@/types/trading';

interface BacktestResultsProps {
  result: BacktestResult;
}

export default function BacktestResults({ result }: BacktestResultsProps) {
  const metrics = useMemo(() => {
    const totalPnL = result.finalBalance - result.initialBalance;
    const returnPercentage = (totalPnL / result.initialBalance) * 100;
    const averageTrade = totalPnL / result.totalTrades;
    
    // Calculate monthly returns
    const monthlyReturns = new Map<string, number>();
    result.trades.forEach(trade => {
      const monthKey = trade.timestamp.toISOString().slice(0, 7); // YYYY-MM
      const pnl = trade.side === 'SELL' ? trade.totalValue : -trade.totalValue;
      monthlyReturns.set(monthKey, (monthlyReturns.get(monthKey) || 0) + pnl);
    });
    
    // Calculate best and worst trades
    const tradePnLs = result.trades.reduce((acc, trade) => {
      if (trade.side === 'SELL') {
        const matchingBuy = result.trades.find(t => 
          t.side === 'BUY' && t.orderId === trade.orderId
        );
        if (matchingBuy) {
          acc.push({
            symbol: trade.symbol,
            pnl: trade.totalValue - matchingBuy.totalValue,
            timestamp: trade.timestamp
          });
        }
      }
      return acc;
    }, [] as { symbol: string; pnl: number; timestamp: Date }[]);
    
    const bestTrade = tradePnLs.reduce((best, current) => 
      current.pnl > best.pnl ? current : best
    , tradePnLs[0]);
    
    const worstTrade = tradePnLs.reduce((worst, current) => 
      current.pnl < worst.pnl ? current : worst
    , tradePnLs[0]);

    return {
      totalPnL,
      returnPercentage,
      averageTrade,
      monthlyReturns: Array.from(monthlyReturns.entries()),
      bestTrade,
      worstTrade
    };
  }, [result]);

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

  const formatDate = (date: Date) => {
    return new Intl.DateTimeFormat('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    }).format(date);
  };

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h2 className="text-xl font-semibold mb-4">Backtest Results</h2>
      
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="p-3 bg-gray-50 rounded">
          <div className="text-sm text-gray-500">Total Return</div>
          <div className={`text-lg font-semibold ${metrics.totalPnL >= 0 ? 'text-green-500' : 'text-red-500'}`}>
            {formatCurrency(metrics.totalPnL)}
          </div>
          <div className={`text-sm ${metrics.returnPercentage >= 0 ? 'text-green-500' : 'text-red-500'}`}>
            {formatPercentage(metrics.returnPercentage)}
          </div>
        </div>
        
        <div className="p-3 bg-gray-50 rounded">
          <div className="text-sm text-gray-500">Win Rate</div>
          <div className="text-lg font-semibold">
            {formatPercentage(result.winRate)}
          </div>
          <div className="text-sm text-gray-500">
            {result.totalTrades} trades
          </div>
        </div>
        
        <div className="p-3 bg-gray-50 rounded">
          <div className="text-sm text-gray-500">Profit Factor</div>
          <div className="text-lg font-semibold">
            {result.profitFactor.toFixed(2)}
          </div>
          <div className="text-sm text-gray-500">
            Gross profit / loss
          </div>
        </div>
        
        <div className="p-3 bg-gray-50 rounded">
          <div className="text-sm text-gray-500">Max Drawdown</div>
          <div className="text-lg font-semibold text-red-500">
            {formatPercentage(result.maxDrawdown)}
          </div>
          <div className="text-sm text-gray-500">
            Peak to trough
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="p-3 bg-gray-50 rounded">
          <div className="text-sm text-gray-500">Sharpe Ratio</div>
          <div className="text-lg font-semibold">
            {result.sharpeRatio.toFixed(2)}
          </div>
          <div className="text-sm text-gray-500">
            Risk-adjusted return
          </div>
        </div>
        
        <div className="p-3 bg-gray-50 rounded">
          <div className="text-sm text-gray-500">Average Trade</div>
          <div className={`text-lg font-semibold ${metrics.averageTrade >= 0 ? 'text-green-500' : 'text-red-500'}`}>
            {formatCurrency(metrics.averageTrade)}
          </div>
          <div className="text-sm text-gray-500">
            Per trade
          </div>
        </div>
        
        <div className="p-3 bg-gray-50 rounded">
          <div className="text-sm text-gray-500">Best Trade</div>
          <div className="text-lg font-semibold text-green-500">
            {metrics.bestTrade ? formatCurrency(metrics.bestTrade.pnl) : 'N/A'}
          </div>
          <div className="text-sm text-gray-500">
            {metrics.bestTrade ? formatDate(metrics.bestTrade.timestamp) : ''}
          </div>
        </div>
        
        <div className="p-3 bg-gray-50 rounded">
          <div className="text-sm text-gray-500">Worst Trade</div>
          <div className="text-lg font-semibold text-red-500">
            {metrics.worstTrade ? formatCurrency(metrics.worstTrade.pnl) : 'N/A'}
          </div>
          <div className="text-sm text-gray-500">
            {metrics.worstTrade ? formatDate(metrics.worstTrade.timestamp) : ''}
          </div>
        </div>
      </div>

      <div className="mb-6">
        <h3 className="text-lg font-semibold mb-2">Monthly Returns</h3>
        <div className="grid grid-cols-3 md:grid-cols-6 gap-2">
          {metrics.monthlyReturns.map(([month, pnl]) => (
            <div key={month} className="p-2 bg-gray-50 rounded">
              <div className="text-sm font-medium">{month}</div>
              <div className={`text-sm ${pnl >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                {formatCurrency(pnl)}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-2">Trade History</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead>
              <tr>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Date
                </th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Symbol
                </th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Side
                </th>
                <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Quantity
                </th>
                <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Price
                </th>
                <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Value
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {result.trades.map((trade) => (
                <tr key={trade.id}>
                  <td className="px-4 py-2 whitespace-nowrap text-sm">
                    {formatDate(trade.timestamp)}
                  </td>
                  <td className="px-4 py-2 whitespace-nowrap text-sm">
                    {trade.symbol}
                  </td>
                  <td className="px-4 py-2 whitespace-nowrap text-sm">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      trade.side === 'BUY' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {trade.side}
                    </span>
                  </td>
                  <td className="px-4 py-2 whitespace-nowrap text-sm text-right">
                    {trade.quantity.toFixed(4)}
                  </td>
                  <td className="px-4 py-2 whitespace-nowrap text-sm text-right">
                    {formatCurrency(trade.price)}
                  </td>
                  <td className="px-4 py-2 whitespace-nowrap text-sm text-right">
                    {formatCurrency(trade.totalValue)}
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