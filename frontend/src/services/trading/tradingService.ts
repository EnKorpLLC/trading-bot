import axios from 'axios';
import type {
  Order,
  Position,
  Trade,
  RiskSettings,
  MarketData,
  OrderBook,
  PortfolioMetrics,
  TradingStrategy,
  BacktestResult,
  ChartSettings
} from '@/types/trading';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001/api'
});

export const tradingService = {
  // Order Management
  async submitOrder(order: Omit<Order, 'id' | 'status' | 'filledQuantity' | 'createdAt' | 'updatedAt'>) {
    const { data } = await api.post<Order>('/trading/orders', order);
    return data;
  },

  async getOrders(userId: string) {
    const { data } = await api.get<Order[]>(`/trading/orders?userId=${userId}`);
    return data;
  },

  async cancelOrder(orderId: string) {
    const { data } = await api.delete<Order>(`/trading/orders/${orderId}`);
    return data;
  },

  // Position Management
  async getPositions(userId: string) {
    const { data } = await api.get<Position[]>(`/trading/positions?userId=${userId}`);
    return data;
  },

  async closePosition(positionId: string) {
    const { data } = await api.post<Order>(`/trading/positions/${positionId}/close`);
    return data;
  },

  // Trade History
  async getTrades(userId: string) {
    const { data } = await api.get<Trade[]>(`/trading/trades?userId=${userId}`);
    return data;
  },

  // Risk Management
  async getRiskSettings(userId: string) {
    const { data } = await api.get<RiskSettings>(`/trading/risk-settings?userId=${userId}`);
    return data;
  },

  async updateRiskSettings(userId: string, settings: Partial<RiskSettings>) {
    const { data } = await api.put<RiskSettings>(`/trading/risk-settings/${userId}`, settings);
    return data;
  },

  // Market Data
  async getMarketData(symbol: string, timeframe: string, limit: number = 1000) {
    const { data } = await api.get<MarketData[]>(`/trading/market-data/${symbol}`, {
      params: { timeframe, limit }
    });
    return data;
  },

  async getOrderBook(symbol: string) {
    const { data } = await api.get<OrderBook>(`/trading/order-book/${symbol}`);
    return data;
  },

  // Portfolio Analytics
  async getPortfolioMetrics(userId: string) {
    const { data } = await api.get<PortfolioMetrics>(`/trading/portfolio/${userId}/metrics`);
    return data;
  },

  // Trading Strategies
  async getStrategies(userId: string) {
    const { data } = await api.get<TradingStrategy[]>(`/trading/strategies?userId=${userId}`);
    return data;
  },

  async createStrategy(strategy: Omit<TradingStrategy, 'id' | 'createdAt' | 'updatedAt'>) {
    const { data } = await api.post<TradingStrategy>('/trading/strategies', strategy);
    return data;
  },

  async updateStrategy(strategyId: string, updates: Partial<TradingStrategy>) {
    const { data } = await api.put<TradingStrategy>(`/trading/strategies/${strategyId}`, updates);
    return data;
  },

  async deleteStrategy(strategyId: string) {
    await api.delete(`/trading/strategies/${strategyId}`);
  },

  // Backtesting
  async runBacktest(strategyId: string, startDate: Date, endDate: Date, initialBalance: number) {
    const { data } = await api.post<BacktestResult>('/trading/backtest', {
      strategyId,
      startDate,
      endDate,
      initialBalance
    });
    return data;
  },

  // Chart Settings
  async getChartSettings(userId: string) {
    const { data } = await api.get<ChartSettings>(`/trading/chart-settings?userId=${userId}`);
    return data;
  },

  async updateChartSettings(userId: string, settings: Partial<ChartSettings>) {
    const { data } = await api.put<ChartSettings>(`/trading/chart-settings/${userId}`, settings);
    return data;
  }
}; 