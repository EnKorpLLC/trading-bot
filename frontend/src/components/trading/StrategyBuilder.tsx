import { useState, useEffect } from 'react';
import type { TradingStrategy, BacktestResult } from '@/types/trading';
import { tradingService } from '@/services/trading/tradingService';

interface StrategyBuilderProps {
  userId: string;
  onStrategyCreate?: (strategy: TradingStrategy) => void;
  onStrategyUpdate?: (strategy: TradingStrategy) => void;
  onBacktestComplete?: (result: BacktestResult) => void;
}

interface StrategyFormData {
  name: string;
  description: string;
  parameters: {
    symbol: string;
    timeframe: string;
    indicators: {
      type: string;
      parameters: Record<string, number>;
    }[];
    entryConditions: string[];
    exitConditions: string[];
    positionSize: number;
    stopLoss: number;
    takeProfit: number;
  };
}

export default function StrategyBuilder({
  userId,
  onStrategyCreate,
  onStrategyUpdate,
  onBacktestComplete
}: StrategyBuilderProps) {
  const [strategies, setStrategies] = useState<TradingStrategy[]>([]);
  const [selectedStrategy, setSelectedStrategy] = useState<TradingStrategy | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [isBacktesting, setIsBacktesting] = useState(false);
  const [formData, setFormData] = useState<StrategyFormData>({
    name: '',
    description: '',
    parameters: {
      symbol: 'BTCUSDT',
      timeframe: '1h',
      indicators: [],
      entryConditions: [],
      exitConditions: [],
      positionSize: 1.0,
      stopLoss: 1.0,
      takeProfit: 2.0
    }
  });

  useEffect(() => {
    loadStrategies();
  }, [userId]);

  const loadStrategies = async () => {
    try {
      const data = await tradingService.getStrategies(userId);
      setStrategies(data);
    } catch (error) {
      console.error('Failed to load strategies:', error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (selectedStrategy) {
        const updated = await tradingService.updateStrategy(selectedStrategy.id, {
          ...selectedStrategy,
          name: formData.name,
          description: formData.description,
          parameters: formData.parameters
        });
        onStrategyUpdate?.(updated);
        setSelectedStrategy(updated);
      } else {
        const created = await tradingService.createStrategy({
          userId,
          name: formData.name,
          description: formData.description,
          parameters: formData.parameters,
          active: false
        });
        onStrategyCreate?.(created);
        setStrategies([...strategies, created]);
      }
      setIsEditing(false);
    } catch (error) {
      console.error('Failed to save strategy:', error);
    }
  };

  const handleBacktest = async () => {
    if (!selectedStrategy) return;

    try {
      setIsBacktesting(true);
      const endDate = new Date();
      const startDate = new Date();
      startDate.setMonth(startDate.getMonth() - 3); // 3 months backtest

      const result = await tradingService.runBacktest(
        selectedStrategy.id,
        startDate,
        endDate,
        10000 // Initial balance
      );

      onBacktestComplete?.(result);
    } catch (error) {
      console.error('Failed to run backtest:', error);
    } finally {
      setIsBacktesting(false);
    }
  };

  const handleAddIndicator = () => {
    setFormData(prev => ({
      ...prev,
      parameters: {
        ...prev.parameters,
        indicators: [
          ...prev.parameters.indicators,
          {
            type: 'SMA',
            parameters: { period: 14 }
          }
        ]
      }
    }));
  };

  const handleAddCondition = (type: 'entry' | 'exit') => {
    setFormData(prev => ({
      ...prev,
      parameters: {
        ...prev.parameters,
        [type === 'entry' ? 'entryConditions' : 'exitConditions']: [
          ...(type === 'entry' ? prev.parameters.entryConditions : prev.parameters.exitConditions),
          'price > sma'
        ]
      }
    }));
  };

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold">Strategy Builder</h2>
        <div className="space-x-2">
          <button
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
            onClick={() => setIsEditing(true)}
          >
            {selectedStrategy ? 'Edit Strategy' : 'New Strategy'}
          </button>
          {selectedStrategy && (
            <button
              className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
              onClick={handleBacktest}
              disabled={isBacktesting}
            >
              {isBacktesting ? 'Running Backtest...' : 'Run Backtest'}
            </button>
          )}
        </div>
      </div>

      {isEditing ? (
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Name</label>
            <input
              type="text"
              value={formData.name}
              onChange={e => setFormData(prev => ({ ...prev, name: e.target.value }))}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Description</label>
            <textarea
              value={formData.description}
              onChange={e => setFormData(prev => ({ ...prev, description: e.target.value }))}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              rows={3}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Symbol</label>
            <input
              type="text"
              value={formData.parameters.symbol}
              onChange={e => setFormData(prev => ({
                ...prev,
                parameters: { ...prev.parameters, symbol: e.target.value }
              }))}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Timeframe</label>
            <select
              value={formData.parameters.timeframe}
              onChange={e => setFormData(prev => ({
                ...prev,
                parameters: { ...prev.parameters, timeframe: e.target.value }
              }))}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            >
              <option value="1m">1 minute</option>
              <option value="5m">5 minutes</option>
              <option value="15m">15 minutes</option>
              <option value="1h">1 hour</option>
              <option value="4h">4 hours</option>
              <option value="1d">1 day</option>
            </select>
          </div>

          <div>
            <div className="flex justify-between items-center mb-2">
              <label className="block text-sm font-medium text-gray-700">Indicators</label>
              <button
                type="button"
                onClick={handleAddIndicator}
                className="text-sm text-blue-500 hover:text-blue-600"
              >
                + Add Indicator
              </button>
            </div>
            {formData.parameters.indicators.map((indicator, index) => (
              <div key={index} className="flex gap-2 mb-2">
                <select
                  value={indicator.type}
                  onChange={e => {
                    const newIndicators = [...formData.parameters.indicators];
                    newIndicators[index] = {
                      ...newIndicators[index],
                      type: e.target.value
                    };
                    setFormData(prev => ({
                      ...prev,
                      parameters: { ...prev.parameters, indicators: newIndicators }
                    }));
                  }}
                  className="block w-1/3 rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                >
                  <option value="SMA">SMA</option>
                  <option value="EMA">EMA</option>
                  <option value="RSI">RSI</option>
                  <option value="MACD">MACD</option>
                </select>
                <input
                  type="number"
                  value={indicator.parameters.period}
                  onChange={e => {
                    const newIndicators = [...formData.parameters.indicators];
                    newIndicators[index] = {
                      ...newIndicators[index],
                      parameters: { period: parseInt(e.target.value) }
                    };
                    setFormData(prev => ({
                      ...prev,
                      parameters: { ...prev.parameters, indicators: newIndicators }
                    }));
                  }}
                  className="block w-1/3 rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  placeholder="Period"
                />
                <button
                  type="button"
                  onClick={() => {
                    const newIndicators = formData.parameters.indicators.filter((_, i) => i !== index);
                    setFormData(prev => ({
                      ...prev,
                      parameters: { ...prev.parameters, indicators: newIndicators }
                    }));
                  }}
                  className="text-red-500 hover:text-red-600"
                >
                  Remove
                </button>
              </div>
            ))}
          </div>

          <div>
            <div className="flex justify-between items-center mb-2">
              <label className="block text-sm font-medium text-gray-700">Entry Conditions</label>
              <button
                type="button"
                onClick={() => handleAddCondition('entry')}
                className="text-sm text-blue-500 hover:text-blue-600"
              >
                + Add Condition
              </button>
            </div>
            {formData.parameters.entryConditions.map((condition, index) => (
              <div key={index} className="flex gap-2 mb-2">
                <input
                  type="text"
                  value={condition}
                  onChange={e => {
                    const newConditions = [...formData.parameters.entryConditions];
                    newConditions[index] = e.target.value;
                    setFormData(prev => ({
                      ...prev,
                      parameters: { ...prev.parameters, entryConditions: newConditions }
                    }));
                  }}
                  className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
                <button
                  type="button"
                  onClick={() => {
                    const newConditions = formData.parameters.entryConditions.filter((_, i) => i !== index);
                    setFormData(prev => ({
                      ...prev,
                      parameters: { ...prev.parameters, entryConditions: newConditions }
                    }));
                  }}
                  className="text-red-500 hover:text-red-600"
                >
                  Remove
                </button>
              </div>
            ))}
          </div>

          <div>
            <div className="flex justify-between items-center mb-2">
              <label className="block text-sm font-medium text-gray-700">Exit Conditions</label>
              <button
                type="button"
                onClick={() => handleAddCondition('exit')}
                className="text-sm text-blue-500 hover:text-blue-600"
              >
                + Add Condition
              </button>
            </div>
            {formData.parameters.exitConditions.map((condition, index) => (
              <div key={index} className="flex gap-2 mb-2">
                <input
                  type="text"
                  value={condition}
                  onChange={e => {
                    const newConditions = [...formData.parameters.exitConditions];
                    newConditions[index] = e.target.value;
                    setFormData(prev => ({
                      ...prev,
                      parameters: { ...prev.parameters, exitConditions: newConditions }
                    }));
                  }}
                  className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
                <button
                  type="button"
                  onClick={() => {
                    const newConditions = formData.parameters.exitConditions.filter((_, i) => i !== index);
                    setFormData(prev => ({
                      ...prev,
                      parameters: { ...prev.parameters, exitConditions: newConditions }
                    }));
                  }}
                  className="text-red-500 hover:text-red-600"
                >
                  Remove
                </button>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Position Size (%)</label>
              <input
                type="number"
                value={formData.parameters.positionSize}
                onChange={e => setFormData(prev => ({
                  ...prev,
                  parameters: { ...prev.parameters, positionSize: parseFloat(e.target.value) }
                }))}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                min="0.1"
                max="100"
                step="0.1"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Stop Loss (%)</label>
              <input
                type="number"
                value={formData.parameters.stopLoss}
                onChange={e => setFormData(prev => ({
                  ...prev,
                  parameters: { ...prev.parameters, stopLoss: parseFloat(e.target.value) }
                }))}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                min="0.1"
                max="100"
                step="0.1"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Take Profit (%)</label>
              <input
                type="number"
                value={formData.parameters.takeProfit}
                onChange={e => setFormData(prev => ({
                  ...prev,
                  parameters: { ...prev.parameters, takeProfit: parseFloat(e.target.value) }
                }))}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                min="0.1"
                max="100"
                step="0.1"
              />
            </div>
          </div>

          <div className="flex justify-end space-x-2">
            <button
              type="button"
              onClick={() => setIsEditing(false)}
              className="px-4 py-2 border border-gray-300 rounded text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              Save Strategy
            </button>
          </div>
        </form>
      ) : (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {strategies.map(strategy => (
              <div
                key={strategy.id}
                className={`p-4 border rounded cursor-pointer hover:border-blue-500 ${
                  selectedStrategy?.id === strategy.id ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
                }`}
                onClick={() => setSelectedStrategy(strategy)}
              >
                <h3 className="font-semibold">{strategy.name}</h3>
                <p className="text-sm text-gray-500">{strategy.description}</p>
                <div className="mt-2 text-sm">
                  <div>Symbol: {strategy.parameters.symbol}</div>
                  <div>Timeframe: {strategy.parameters.timeframe}</div>
                  <div>Indicators: {strategy.parameters.indicators.length}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
} 