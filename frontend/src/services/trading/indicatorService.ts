import type { MarketData } from '@/types/trading';

export interface IndicatorValue {
  time: number;
  value: number;
}

export class IndicatorService {
  // Simple Moving Average (SMA)
  static calculateSMA(data: MarketData[], period: number): IndicatorValue[] {
    const result: IndicatorValue[] = [];
    
    for (let i = period - 1; i < data.length; i++) {
      const sum = data
        .slice(i - period + 1, i + 1)
        .reduce((acc, candle) => acc + candle.close, 0);
      
      result.push({
        time: data[i].timestamp.getTime() / 1000,
        value: sum / period
      });
    }
    
    return result;
  }

  // Exponential Moving Average (EMA)
  static calculateEMA(data: MarketData[], period: number): IndicatorValue[] {
    const result: IndicatorValue[] = [];
    const multiplier = 2 / (period + 1);
    
    // First EMA uses SMA as initial value
    const sma = data
      .slice(0, period)
      .reduce((acc, candle) => acc + candle.close, 0) / period;
    
    result.push({
      time: data[period - 1].timestamp.getTime() / 1000,
      value: sma
    });
    
    for (let i = period; i < data.length; i++) {
      const currentClose = data[i].close;
      const previousEMA = result[result.length - 1].value;
      const currentEMA = (currentClose - previousEMA) * multiplier + previousEMA;
      
      result.push({
        time: data[i].timestamp.getTime() / 1000,
        value: currentEMA
      });
    }
    
    return result;
  }

  // Relative Strength Index (RSI)
  static calculateRSI(data: MarketData[], period: number = 14): IndicatorValue[] {
    const result: IndicatorValue[] = [];
    const gains: number[] = [];
    const losses: number[] = [];
    
    // Calculate price changes and separate gains/losses
    for (let i = 1; i < data.length; i++) {
      const change = data[i].close - data[i - 1].close;
      gains.push(change > 0 ? change : 0);
      losses.push(change < 0 ? -change : 0);
    }
    
    // Calculate initial averages
    let avgGain = gains.slice(0, period).reduce((a, b) => a + b) / period;
    let avgLoss = losses.slice(0, period).reduce((a, b) => a + b) / period;
    
    // Calculate initial RSI
    result.push({
      time: data[period].timestamp.getTime() / 1000,
      value: 100 - (100 / (1 + avgGain / avgLoss))
    });
    
    // Calculate subsequent RSI values
    for (let i = period; i < data.length - 1; i++) {
      avgGain = (avgGain * (period - 1) + gains[i]) / period;
      avgLoss = (avgLoss * (period - 1) + losses[i]) / period;
      
      result.push({
        time: data[i + 1].timestamp.getTime() / 1000,
        value: 100 - (100 / (1 + avgGain / avgLoss))
      });
    }
    
    return result;
  }

  // Moving Average Convergence Divergence (MACD)
  static calculateMACD(
    data: MarketData[],
    fastPeriod: number = 12,
    slowPeriod: number = 26,
    signalPeriod: number = 9
  ): { macd: IndicatorValue[]; signal: IndicatorValue[]; histogram: IndicatorValue[] } {
    const fastEMA = this.calculateEMA(data, fastPeriod);
    const slowEMA = this.calculateEMA(data, slowPeriod);
    const macdLine: IndicatorValue[] = [];
    
    // Calculate MACD line
    for (let i = slowPeriod - 1; i < data.length; i++) {
      const fastValue = fastEMA[i - (slowPeriod - fastPeriod)].value;
      const slowValue = slowEMA[i - (slowPeriod - 1)].value;
      
      macdLine.push({
        time: data[i].timestamp.getTime() / 1000,
        value: fastValue - slowValue
      });
    }
    
    // Calculate Signal line (EMA of MACD line)
    const signalLine: IndicatorValue[] = [];
    const multiplier = 2 / (signalPeriod + 1);
    
    // Initial signal value (SMA of MACD)
    const initialSignal = macdLine
      .slice(0, signalPeriod)
      .reduce((acc, val) => acc + val.value, 0) / signalPeriod;
    
    signalLine.push({
      time: macdLine[signalPeriod - 1].time,
      value: initialSignal
    });
    
    // Calculate subsequent signal values
    for (let i = signalPeriod; i < macdLine.length; i++) {
      const currentMACD = macdLine[i].value;
      const previousSignal = signalLine[signalLine.length - 1].value;
      const currentSignal = (currentMACD - previousSignal) * multiplier + previousSignal;
      
      signalLine.push({
        time: macdLine[i].time,
        value: currentSignal
      });
    }
    
    // Calculate histogram
    const histogram = macdLine.slice(signalPeriod - 1).map((macd, i) => ({
      time: macd.time,
      value: macd.value - signalLine[i].value
    }));
    
    return {
      macd: macdLine,
      signal: signalLine,
      histogram
    };
  }

  // Bollinger Bands
  static calculateBollingerBands(
    data: MarketData[],
    period: number = 20,
    stdDev: number = 2
  ): { upper: IndicatorValue[]; middle: IndicatorValue[]; lower: IndicatorValue[] } {
    const sma = this.calculateSMA(data, period);
    const upper: IndicatorValue[] = [];
    const lower: IndicatorValue[] = [];
    
    for (let i = period - 1; i < data.length; i++) {
      const slice = data.slice(i - period + 1, i + 1);
      const mean = sma[i - (period - 1)].value;
      
      // Calculate standard deviation
      const squaredDiffs = slice.map(candle => Math.pow(candle.close - mean, 2));
      const variance = squaredDiffs.reduce((a, b) => a + b) / period;
      const standardDeviation = Math.sqrt(variance);
      
      upper.push({
        time: data[i].timestamp.getTime() / 1000,
        value: mean + (standardDeviation * stdDev)
      });
      
      lower.push({
        time: data[i].timestamp.getTime() / 1000,
        value: mean - (standardDeviation * stdDev)
      });
    }
    
    return {
      upper,
      middle: sma,
      lower
    };
  }

  // Volume Weighted Average Price (VWAP)
  static calculateVWAP(data: MarketData[]): IndicatorValue[] {
    const result: IndicatorValue[] = [];
    let cumulativeTPV = 0; // Total Price * Volume
    let cumulativeVolume = 0;
    
    for (let i = 0; i < data.length; i++) {
      const typicalPrice = (data[i].high + data[i].low + data[i].close) / 3;
      const volume = data[i].volume;
      
      cumulativeTPV += typicalPrice * volume;
      cumulativeVolume += volume;
      
      result.push({
        time: data[i].timestamp.getTime() / 1000,
        value: cumulativeTPV / cumulativeVolume
      });
    }
    
    return result;
  }

  // Average True Range (ATR)
  static calculateATR(data: MarketData[], period: number = 14): IndicatorValue[] {
    const trueRanges: number[] = [];
    const result: IndicatorValue[] = [];
    
    // Calculate True Ranges
    for (let i = 1; i < data.length; i++) {
      const high = data[i].high;
      const low = data[i].low;
      const prevClose = data[i - 1].close;
      
      const tr1 = high - low;
      const tr2 = Math.abs(high - prevClose);
      const tr3 = Math.abs(low - prevClose);
      
      trueRanges.push(Math.max(tr1, tr2, tr3));
    }
    
    // Calculate initial ATR
    const initialATR = trueRanges
      .slice(0, period)
      .reduce((a, b) => a + b) / period;
    
    result.push({
      time: data[period].timestamp.getTime() / 1000,
      value: initialATR
    });
    
    // Calculate subsequent ATR values
    for (let i = period; i < data.length - 1; i++) {
      const previousATR = result[result.length - 1].value;
      const currentATR = (previousATR * (period - 1) + trueRanges[i]) / period;
      
      result.push({
        time: data[i + 1].timestamp.getTime() / 1000,
        value: currentATR
      });
    }
    
    return result;
  }
} 