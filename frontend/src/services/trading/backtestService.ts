import type { MarketData, TradingStrategy, BacktestResult, Trade, Order, OrderType, OrderSide } from '@/types/trading';
import { IndicatorService } from './indicatorService';

interface Position {
  symbol: string;
  quantity: number;
  entryPrice: number;
  side: OrderSide;
}

interface BacktestState {
  balance: number;
  positions: Map<string, Position>;
  trades: Trade[];
  equity: number[];
  drawdown: number;
  maxDrawdown: number;
  winningTrades: number;
  losingTrades: number;
}

export class BacktestService {
  private strategy: TradingStrategy;
  private data: MarketData[];
  private initialBalance: number;
  private state: BacktestState;
  private indicatorValues: Map<string, number[]>;

  constructor(strategy: TradingStrategy, data: MarketData[], initialBalance: number) {
    this.strategy = strategy;
    this.data = data;
    this.initialBalance = initialBalance;
    this.indicatorValues = new Map();
    this.state = {
      balance: initialBalance,
      positions: new Map(),
      trades: [],
      equity: [initialBalance],
      drawdown: 0,
      maxDrawdown: 0,
      winningTrades: 0,
      losingTrades: 0
    };
  }

  public async run(): Promise<BacktestResult> {
    // Calculate indicators
    await this.calculateIndicators();

    // Run simulation
    for (let i = 50; i < this.data.length; i++) { // Start from 50 to have enough data for indicators
      const candle = this.data[i];
      const timestamp = candle.timestamp;

      // Check for exit conditions
      await this.checkExitConditions(candle, timestamp);

      // Check for entry conditions
      await this.checkEntryConditions(candle, timestamp);

      // Update equity curve and drawdown
      const currentEquity = this.calculateEquity(candle.close);
      this.state.equity.push(currentEquity);
      this.updateDrawdown(currentEquity);
    }

    // Close any remaining positions
    const lastCandle = this.data[this.data.length - 1];
    await this.closeAllPositions(lastCandle.close, lastCandle.timestamp);

    // Calculate final metrics
    const totalTrades = this.state.winningTrades + this.state.losingTrades;
    const winRate = totalTrades > 0 ? (this.state.winningTrades / totalTrades) * 100 : 0;
    const profitFactor = this.calculateProfitFactor();
    const sharpeRatio = this.calculateSharpeRatio();

    return {
      id: `backtest_${Date.now()}`,
      strategyId: this.strategy.id,
      startDate: this.data[0].timestamp,
      endDate: this.data[this.data.length - 1].timestamp,
      initialBalance: this.initialBalance,
      finalBalance: this.state.balance,
      totalTrades,
      winRate,
      profitFactor,
      sharpeRatio,
      maxDrawdown: this.state.maxDrawdown,
      trades: this.state.trades
    };
  }

  private async calculateIndicators() {
    for (const indicator of this.strategy.parameters.indicators) {
      switch (indicator.type) {
        case 'SMA':
          const sma = IndicatorService.calculateSMA(this.data, indicator.parameters.period);
          this.indicatorValues.set(`SMA_${indicator.parameters.period}`, sma.map(v => v.value));
          break;
        case 'EMA':
          const ema = IndicatorService.calculateEMA(this.data, indicator.parameters.period);
          this.indicatorValues.set(`EMA_${indicator.parameters.period}`, ema.map(v => v.value));
          break;
        case 'RSI':
          const rsi = IndicatorService.calculateRSI(this.data, indicator.parameters.period);
          this.indicatorValues.set(`RSI_${indicator.parameters.period}`, rsi.map(v => v.value));
          break;
        // Add more indicators as needed
      }
    }
  }

  private async checkEntryConditions(candle: MarketData, timestamp: Date) {
    if (this.state.positions.has(candle.symbol)) return; // Already in position

    const conditions = this.strategy.parameters.entryConditions;
    const shouldEnter = await this.evaluateConditions(conditions, candle, this.data.indexOf(candle));

    if (shouldEnter) {
      const positionSize = (this.state.balance * this.strategy.parameters.positionSize) / 100;
      const quantity = positionSize / candle.close;

      // Create position
      this.state.positions.set(candle.symbol, {
        symbol: candle.symbol,
        quantity,
        entryPrice: candle.close,
        side: OrderSide.BUY // Simplified to long-only for this example
      });

      // Record trade entry
      this.recordTrade({
        id: `trade_${Date.now()}_${Math.random()}`,
        userId: this.strategy.userId,
        orderId: `order_${Date.now()}`,
        symbol: candle.symbol,
        side: OrderSide.BUY,
        quantity,
        price: candle.close,
        timestamp,
        fee: this.calculateFee(quantity * candle.close),
        totalValue: quantity * candle.close
      });
    }
  }

  private async checkExitConditions(candle: MarketData, timestamp: Date) {
    const position = this.state.positions.get(candle.symbol);
    if (!position) return; // No position to exit

    const conditions = this.strategy.parameters.exitConditions;
    const shouldExit = await this.evaluateConditions(conditions, candle, this.data.indexOf(candle));

    // Check stop loss and take profit
    const unrealizedPnL = (candle.close - position.entryPrice) * position.quantity;
    const unrealizedPnLPercent = (unrealizedPnL / (position.entryPrice * position.quantity)) * 100;

    if (shouldExit ||
        unrealizedPnLPercent <= -this.strategy.parameters.stopLoss ||
        unrealizedPnLPercent >= this.strategy.parameters.takeProfit) {
      await this.closePosition(position, candle.close, timestamp);
    }
  }

  private async closePosition(position: Position, price: number, timestamp: Date) {
    const pnl = (price - position.entryPrice) * position.quantity;
    this.state.balance += pnl;

    // Record trade exit
    this.recordTrade({
      id: `trade_${Date.now()}_${Math.random()}`,
      userId: this.strategy.userId,
      orderId: `order_${Date.now()}`,
      symbol: position.symbol,
      side: OrderSide.SELL,
      quantity: position.quantity,
      price,
      timestamp,
      fee: this.calculateFee(position.quantity * price),
      totalValue: position.quantity * price
    });

    // Update win/loss count
    if (pnl > 0) {
      this.state.winningTrades++;
    } else {
      this.state.losingTrades++;
    }

    // Remove position
    this.state.positions.delete(position.symbol);
  }

  private async closeAllPositions(price: number, timestamp: Date) {
    for (const position of this.state.positions.values()) {
      await this.closePosition(position, price, timestamp);
    }
  }

  private calculateEquity(currentPrice: number): number {
    let equity = this.state.balance;
    for (const position of this.state.positions.values()) {
      const marketValue = position.quantity * currentPrice;
      equity += marketValue - (position.quantity * position.entryPrice);
    }
    return equity;
  }

  private updateDrawdown(currentEquity: number) {
    const peak = Math.max(...this.state.equity);
    const drawdown = ((peak - currentEquity) / peak) * 100;
    this.state.drawdown = drawdown;
    this.state.maxDrawdown = Math.max(this.state.maxDrawdown, drawdown);
  }

  private calculateProfitFactor(): number {
    let grossProfit = 0;
    let grossLoss = 0;

    for (const trade of this.state.trades) {
      const pnl = (trade.side === OrderSide.SELL ? 1 : -1) * trade.totalValue;
      if (pnl > 0) {
        grossProfit += pnl;
      } else {
        grossLoss += Math.abs(pnl);
      }
    }

    return grossLoss === 0 ? grossProfit : grossProfit / grossLoss;
  }

  private calculateSharpeRatio(): number {
    const returns: number[] = [];
    for (let i = 1; i < this.state.equity.length; i++) {
      const returnPct = (this.state.equity[i] - this.state.equity[i - 1]) / this.state.equity[i - 1];
      returns.push(returnPct);
    }

    const avgReturn = returns.reduce((sum, r) => sum + r, 0) / returns.length;
    const stdDev = Math.sqrt(
      returns.reduce((sum, r) => sum + Math.pow(r - avgReturn, 2), 0) / returns.length
    );

    const annualizedReturn = avgReturn * 252; // Assuming daily returns
    const annualizedStdDev = stdDev * Math.sqrt(252);

    return annualizedStdDev === 0 ? 0 : annualizedReturn / annualizedStdDev;
  }

  private calculateFee(value: number): number {
    return value * 0.001; // 0.1% fee
  }

  private recordTrade(trade: Trade) {
    this.state.trades.push(trade);
  }

  private async evaluateConditions(conditions: string[], candle: MarketData, index: number): Promise<boolean> {
    // Simple condition evaluation - replace with more sophisticated parser
    for (const condition of conditions) {
      const [indicator, operator, value] = condition.split(' ');
      const indicatorValue = this.getIndicatorValue(indicator, index);
      
      if (!this.evaluateCondition(indicatorValue, operator, parseFloat(value))) {
        return false;
      }
    }
    return true;
  }

  private getIndicatorValue(indicator: string, index: number): number {
    const [name, period] = indicator.split('_');
    const values = this.indicatorValues.get(`${name}_${period}`);
    return values ? values[index] : 0;
  }

  private evaluateCondition(a: number, operator: string, b: number): boolean {
    switch (operator) {
      case '>': return a > b;
      case '<': return a < b;
      case '>=': return a >= b;
      case '<=': return a <= b;
      case '==': return a === b;
      default: return false;
    }
  }
} 