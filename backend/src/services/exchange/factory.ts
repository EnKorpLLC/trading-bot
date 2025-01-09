import { BaseExchangeService } from './base';
import { BinanceService } from './binance';
import { ExchangeCredentials } from './types';
import { logger } from '../../utils/logger';

export type ExchangeType = 'binance' | 'other_exchanges_to_be_added';

export class ExchangeFactory {
    private static instances: Map<string, BaseExchangeService> = new Map();

    static createExchange(
        type: ExchangeType,
        credentials: ExchangeCredentials
    ): BaseExchangeService {
        const key = `${type}-${credentials.apiKey}`;

        if (!this.instances.has(key)) {
            logger.info(`Creating new exchange instance for ${type}`);
            let exchange: BaseExchangeService;

            switch (type) {
                case 'binance':
                    exchange = new BinanceService(credentials);
                    break;
                default:
                    throw new Error(`Unsupported exchange type: ${type}`);
            }

            this.instances.set(key, exchange);
        }

        return this.instances.get(key)!;
    }

    static getExchange(type: ExchangeType, apiKey: string): BaseExchangeService | undefined {
        return this.instances.get(`${type}-${apiKey}`);
    }

    static removeExchange(type: ExchangeType, apiKey: string): void {
        const key = `${type}-${apiKey}`;
        const exchange = this.instances.get(key);
        if (exchange) {
            exchange.disconnect();
            this.instances.delete(key);
            logger.info(`Removed exchange instance for ${type}`);
        }
    }
} 