import { MarketData, TradingStrategy, BacktestResult } from '@/types/trading';
import { MarketDataService } from './marketDataService';

interface OptimizationResult {
    parameters: Record<string, number>;
    performance: {
        profitFactor: number;
        sharpeRatio: number;
        maxDrawdown: number;
        totalReturn: number;
        winRate: number;
    };
}

interface OptimizationConfig {
    parameterRanges: {
        [key: string]: {
            min: number;
            max: number;
            step: number;
        };
    };
    optimizationMetric: 'sharpeRatio' | 'profitFactor' | 'totalReturn';
    populationSize?: number;
    generations?: number;
}

export class StrategyOptimizationService {
    private marketDataService: MarketDataService;

    constructor(marketDataService: MarketDataService) {
        this.marketDataService = marketDataService;
    }

    public async optimizeStrategy(
        strategy: TradingStrategy,
        config: OptimizationConfig,
        startDate: Date,
        endDate: Date
    ): Promise<OptimizationResult[]> {
        // Get historical data for backtesting
        const historicalData = await this.marketDataService.getHistoricalData(
            strategy.parameters.symbol,
            strategy.parameters.timeframe,
            startDate,
            endDate
        );

        // Initialize population with random parameters
        let population = this.initializePopulation(config);

        // Run genetic algorithm optimization
        for (let generation = 0; generation < (config.generations || 10); generation++) {
            // Evaluate fitness for each set of parameters
            const results = await Promise.all(
                population.map(params => this.evaluateParameters(
                    strategy,
                    params,
                    historicalData
                ))
            );

            // Sort by fitness
            results.sort((a, b) => 
                b.performance[config.optimizationMetric] - 
                a.performance[config.optimizationMetric]
            );

            // Select best performers
            population = this.selectBestPerformers(results, config.populationSize || 20);

            // Create new generation
            population = this.createNewGeneration(population, config);
        }

        // Return best results
        return population.map(params => ({
            parameters: params,
            performance: this.calculatePerformance(strategy, params, historicalData)
        }));
    }

    private initializePopulation(config: OptimizationConfig): Record<string, number>[] {
        const population: Record<string, number>[] = [];
        const size = config.populationSize || 20;

        for (let i = 0; i < size; i++) {
            const params: Record<string, number> = {};
            for (const [param, range] of Object.entries(config.parameterRanges)) {
                params[param] = this.randomInRange(range.min, range.max, range.step);
            }
            population.push(params);
        }

        return population;
    }

    private async evaluateParameters(
        strategy: TradingStrategy,
        parameters: Record<string, number>,
        historicalData: MarketData[]
    ): Promise<OptimizationResult> {
        const modifiedStrategy = {
            ...strategy,
            parameters: { ...strategy.parameters, ...parameters }
        };

        // Run backtest with these parameters
        const backtestResult = await this.runBacktest(modifiedStrategy, historicalData);

        return {
            parameters,
            performance: {
                profitFactor: this.calculateProfitFactor(backtestResult),
                sharpeRatio: this.calculateSharpeRatio(backtestResult),
                maxDrawdown: backtestResult.maxDrawdown,
                totalReturn: this.calculateTotalReturn(backtestResult),
                winRate: backtestResult.winRate
            }
        };
    }

    private selectBestPerformers(
        results: OptimizationResult[],
        count: number
    ): Record<string, number>[] {
        return results
            .slice(0, count)
            .map(result => result.parameters);
    }

    private createNewGeneration(
        population: Record<string, number>[],
        config: OptimizationConfig
    ): Record<string, number>[] {
        const newPopulation: Record<string, number>[] = [...population];

        while (newPopulation.length < (config.populationSize || 20)) {
            // Select parents
            const parent1 = population[Math.floor(Math.random() * population.length)];
            const parent2 = population[Math.floor(Math.random() * population.length)];

            // Create child through crossover
            const child = this.crossover(parent1, parent2);

            // Mutate child
            this.mutate(child, config.parameterRanges);

            newPopulation.push(child);
        }

        return newPopulation;
    }

    private crossover(
        parent1: Record<string, number>,
        parent2: Record<string, number>
    ): Record<string, number> {
        const child: Record<string, number> = {};

        for (const param in parent1) {
            // Randomly select from either parent
            child[param] = Math.random() < 0.5 ? parent1[param] : parent2[param];
        }

        return child;
    }

    private mutate(
        parameters: Record<string, number>,
        ranges: OptimizationConfig['parameterRanges']
    ): void {
        for (const [param, value] of Object.entries(parameters)) {
            if (Math.random() < 0.1) { // 10% mutation rate
                const range = ranges[param];
                parameters[param] = this.randomInRange(range.min, range.max, range.step);
            }
        }
    }

    private randomInRange(min: number, max: number, step: number): number {
        const steps = Math.floor((max - min) / step);
        return min + (Math.floor(Math.random() * steps) * step);
    }

    private async runBacktest(
        strategy: TradingStrategy,
        historicalData: MarketData[]
    ): Promise<BacktestResult> {
        const response = await fetch(
            `${process.env.NEXT_PUBLIC_API_URL}/trading/backtest`,
            {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    strategy,
                    historicalData
                })
            }
        );

        if (!response.ok) {
            throw new Error('Failed to run backtest');
        }

        return response.json();
    }

    private calculateProfitFactor(result: BacktestResult): number {
        const grossProfit = result.trades
            .filter(t => t.pnl > 0)
            .reduce((sum, t) => sum + t.pnl, 0);

        const grossLoss = Math.abs(
            result.trades
                .filter(t => t.pnl < 0)
                .reduce((sum, t) => sum + t.pnl, 0)
        );

        return grossLoss === 0 ? grossProfit : grossProfit / grossLoss;
    }

    private calculateSharpeRatio(result: BacktestResult): number {
        const returns = result.trades.map(t => t.pnl);
        const avgReturn = returns.reduce((sum, r) => sum + r, 0) / returns.length;
        const stdDev = Math.sqrt(
            returns.reduce((sum, r) => sum + Math.pow(r - avgReturn, 2), 0) / returns.length
        );

        return stdDev === 0 ? 0 : avgReturn / stdDev;
    }

    private calculateTotalReturn(result: BacktestResult): number {
        return ((result.finalBalance - result.initialBalance) / result.initialBalance) * 100;
    }

    public async saveOptimizedStrategy(
        strategy: TradingStrategy,
        parameters: Record<string, number>
    ): Promise<TradingStrategy> {
        const optimizedStrategy = {
            ...strategy,
            parameters: { ...strategy.parameters, ...parameters }
        };

        const response = await fetch(
            `${process.env.NEXT_PUBLIC_API_URL}/trading/strategies/${strategy.id}`,
            {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(optimizedStrategy)
            }
        );

        if (!response.ok) {
            throw new Error('Failed to save optimized strategy');
        }

        return response.json();
    }
} 