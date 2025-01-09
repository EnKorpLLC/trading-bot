import { useState, FormEvent } from 'react';

interface RiskSettings {
    maxPositionSize: number;
    maxDailyLoss: number;
    riskPerTrade: number;
    maxDrawdown: number;
    leverageLimit: number;
}

interface RiskManagementProps {
    initialSettings?: RiskSettings;
    onSave: (settings: RiskSettings) => Promise<void>;
    isSubmitting?: boolean;
}

const defaultSettings: RiskSettings = {
    maxPositionSize: 5, // 5% of account
    maxDailyLoss: 2, // 2% of account
    riskPerTrade: 1, // 1% of account
    maxDrawdown: 10, // 10% of account
    leverageLimit: 10, // 10x leverage
};

export function RiskManagement({ initialSettings = defaultSettings, onSave, isSubmitting }: RiskManagementProps) {
    const [settings, setSettings] = useState<RiskSettings>(initialSettings);
    const [errors, setErrors] = useState<string[]>([]);

    const validateSettings = (): boolean => {
        const newErrors: string[] = [];

        if (settings.maxPositionSize <= 0 || settings.maxPositionSize > 100) {
            newErrors.push('Maximum position size must be between 0 and 100%');
        }
        if (settings.maxDailyLoss <= 0 || settings.maxDailyLoss > 100) {
            newErrors.push('Maximum daily loss must be between 0 and 100%');
        }
        if (settings.riskPerTrade <= 0 || settings.riskPerTrade > settings.maxDailyLoss) {
            newErrors.push('Risk per trade must be between 0 and maximum daily loss');
        }
        if (settings.maxDrawdown <= 0 || settings.maxDrawdown > 100) {
            newErrors.push('Maximum drawdown must be between 0 and 100%');
        }
        if (settings.leverageLimit <= 0) {
            newErrors.push('Leverage limit must be greater than 0');
        }

        setErrors(newErrors);
        return newErrors.length === 0;
    };

    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();
        if (!validateSettings()) return;

        try {
            await onSave(settings);
            setErrors([]);
        } catch (error) {
            setErrors([error instanceof Error ? error.message : 'Failed to save risk settings']);
        }
    };

    return (
        <form onSubmit={handleSubmit} data-testid="risk-settings-form" className="space-y-4">
            <div>
                <label className="block text-sm font-medium text-gray-700">
                    Maximum Position Size (% of account)
                </label>
                <input
                    type="number"
                    value={settings.maxPositionSize}
                    onChange={(e) => setSettings({ ...settings, maxPositionSize: parseFloat(e.target.value) })}
                    data-testid="max-position-size-input"
                    step="0.1"
                    min="0"
                    max="100"
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
            </div>

            <div>
                <label className="block text-sm font-medium text-gray-700">
                    Maximum Daily Loss (% of account)
                </label>
                <input
                    type="number"
                    value={settings.maxDailyLoss}
                    onChange={(e) => setSettings({ ...settings, maxDailyLoss: parseFloat(e.target.value) })}
                    data-testid="max-daily-loss-input"
                    step="0.1"
                    min="0"
                    max="100"
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
            </div>

            <div>
                <label className="block text-sm font-medium text-gray-700">
                    Risk per Trade (% of account)
                </label>
                <input
                    type="number"
                    value={settings.riskPerTrade}
                    onChange={(e) => setSettings({ ...settings, riskPerTrade: parseFloat(e.target.value) })}
                    data-testid="risk-per-trade-input"
                    step="0.1"
                    min="0"
                    max={settings.maxDailyLoss}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
            </div>

            <div>
                <label className="block text-sm font-medium text-gray-700">
                    Maximum Drawdown (% of account)
                </label>
                <input
                    type="number"
                    value={settings.maxDrawdown}
                    onChange={(e) => setSettings({ ...settings, maxDrawdown: parseFloat(e.target.value) })}
                    data-testid="max-drawdown-input"
                    step="0.1"
                    min="0"
                    max="100"
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
            </div>

            <div>
                <label className="block text-sm font-medium text-gray-700">
                    Leverage Limit (x)
                </label>
                <input
                    type="number"
                    value={settings.leverageLimit}
                    onChange={(e) => setSettings({ ...settings, leverageLimit: parseFloat(e.target.value) })}
                    data-testid="leverage-limit-input"
                    step="0.1"
                    min="0"
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
            </div>

            {errors.length > 0 && (
                <div data-testid="risk-settings-errors" className="rounded-md bg-red-50 p-4">
                    <ul className="list-disc pl-5 space-y-1">
                        {errors.map((error, index) => (
                            <li key={index} className="text-sm text-red-700">{error}</li>
                        ))}
                    </ul>
                </div>
            )}

            <button
                type="submit"
                disabled={isSubmitting}
                data-testid="save-risk-settings-button"
                className={`w-full py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white ${
                    isSubmitting ? 'bg-gray-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700'
                }`}
            >
                {isSubmitting ? 'Saving...' : 'Save Risk Settings'}
            </button>
        </form>
    );
} 