import { Position, RiskSettings, PortfolioMetrics } from '@/types/trading';

interface PositionSizeResult {
    size: number;
    riskAmount: number;
    potentialLoss: number;
    marginRequired: number;
}

interface RiskMetrics {
    totalExposure: number;
    marginUtilization: number;
    portfolioHeatmap: Map<string, number>;
    riskPerTrade: number;
    maxDrawdown: number;
}

export class RiskManagementService {
    private settings: RiskSettings;

    constructor(settings: RiskSettings) {
        this.settings = settings;
    }

    public calculatePositionSize(
        accountBalance: number,
        entryPrice: number,
        stopLoss: number,
        leverage: number = 1
    ): PositionSizeResult {
        // Calculate risk amount based on risk per trade setting
        const riskAmount = accountBalance * (this.settings.riskPerTrade / 100);
        
        // Calculate position size based on risk and stop loss distance
        const stopLossDistance = Math.abs(entryPrice - stopLoss);
        const riskPerUnit = stopLossDistance;
        const size = (riskAmount / riskPerUnit) * leverage;

        // Calculate potential loss
        const potentialLoss = size * stopLossDistance;

        // Calculate required margin
        const marginRequired = (entryPrice * size) / leverage;

        return {
            size,
            riskAmount,
            potentialLoss,
            marginRequired
        };
    }

    public validatePosition(
        position: Position,
        portfolio: Position[],
        accountBalance: number
    ): { isValid: boolean; message: string } {
        // Check position size limit
        const positionValue = position.quantity * position.averageEntryPrice;
        const maxPositionSize = accountBalance * (this.settings.maxPositionSize / 100);
        
        if (positionValue > maxPositionSize) {
            return {
                isValid: false,
                message: `Position size exceeds maximum allowed (${this.settings.maxPositionSize}% of account)`
            };
        }

        // Check total exposure
        const totalExposure = this.calculateTotalExposure(portfolio);
        const maxExposure = accountBalance * (this.settings.maxLeverage / 100);
        
        if (totalExposure + positionValue > maxExposure) {
            return {
                isValid: false,
                message: `Total exposure would exceed maximum allowed leverage (${this.settings.maxLeverage}x)`
            };
        }

        // Check daily loss limit
        const dailyPnL = this.calculateDailyPnL(portfolio);
        const maxDailyLoss = accountBalance * (this.settings.maxDailyLoss / 100);
        
        if (dailyPnL < -maxDailyLoss) {
            return {
                isValid: false,
                message: `Daily loss limit reached (${this.settings.maxDailyLoss}% of account)`
            };
        }

        return { isValid: true, message: 'Position validated' };
    }

    public calculateRiskMetrics(
        portfolio: Position[],
        accountBalance: number
    ): RiskMetrics {
        // Calculate total exposure
        const totalExposure = this.calculateTotalExposure(portfolio);
        
        // Calculate margin utilization
        const marginUtilization = (totalExposure / accountBalance) * 100;

        // Calculate portfolio heatmap (exposure distribution)
        const portfolioHeatmap = new Map<string, number>();
        portfolio.forEach(position => {
            const exposure = position.quantity * position.currentPrice;
            portfolioHeatmap.set(position.symbol, (exposure / totalExposure) * 100);
        });

        // Calculate risk per trade
        const riskPerTrade = this.calculateRiskPerTrade(portfolio, accountBalance);

        // Calculate maximum drawdown
        const maxDrawdown = this.calculateMaxDrawdown(portfolio);

        return {
            totalExposure,
            marginUtilization,
            portfolioHeatmap,
            riskPerTrade,
            maxDrawdown
        };
    }

    private calculateTotalExposure(portfolio: Position[]): number {
        return portfolio.reduce((total, position) => {
            return total + (position.quantity * position.currentPrice);
        }, 0);
    }

    private calculateDailyPnL(portfolio: Position[]): number {
        const startOfDay = new Date();
        startOfDay.setHours(0, 0, 0, 0);

        return portfolio.reduce((total, position) => {
            if (new Date(position.openedAt) >= startOfDay) {
                return total + position.unrealizedPnL + position.realizedPnL;
            }
            return total;
        }, 0);
    }

    private calculateRiskPerTrade(portfolio: Position[], accountBalance: number): number {
        const totalRisk = portfolio.reduce((total, position) => {
            const positionValue = position.quantity * position.currentPrice;
            return total + (positionValue / accountBalance) * 100;
        }, 0);

        return totalRisk / portfolio.length || 0;
    }

    private calculateMaxDrawdown(portfolio: Position[]): number {
        let peak = 0;
        let maxDrawdown = 0;

        portfolio.forEach(position => {
            const equity = position.unrealizedPnL + position.realizedPnL;
            peak = Math.max(peak, equity);
            maxDrawdown = Math.max(maxDrawdown, (peak - equity) / peak * 100);
        });

        return maxDrawdown;
    }

    public updateSettings(newSettings: Partial<RiskSettings>): void {
        this.settings = { ...this.settings, ...newSettings };
    }

    public getSettings(): RiskSettings {
        return { ...this.settings };
    }

    public async saveSettings(): Promise<void> {
        const response = await fetch(
            `${process.env.NEXT_PUBLIC_API_URL}/trading/risk-settings`,
            {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(this.settings)
            }
        );

        if (!response.ok) {
            throw new Error('Failed to save risk settings');
        }
    }
} 