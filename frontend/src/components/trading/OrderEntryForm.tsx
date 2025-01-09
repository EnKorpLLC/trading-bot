import { useState, FormEvent } from 'react';
import { OrderType, OrderSide } from '@/types/trading';

interface OrderEntryFormProps {
    onSubmit: (order: any) => Promise<void>;
    isSubmitting?: boolean;
}

export function OrderEntryForm({ onSubmit, isSubmitting }: OrderEntryFormProps) {
    const [symbol, setSymbol] = useState('');
    const [type, setType] = useState<OrderType>(OrderType.MARKET);
    const [side, setSide] = useState<OrderSide>(OrderSide.BUY);
    const [quantity, setQuantity] = useState('');
    const [price, setPrice] = useState('');
    const [errors, setErrors] = useState<string[]>([]);

    const validateForm = (): boolean => {
        const newErrors: string[] = [];
        
        if (!symbol) newErrors.push('Symbol is required');
        if (!quantity) newErrors.push('Quantity is required');
        if (parseFloat(quantity) <= 0) newErrors.push('Quantity must be greater than 0');
        if (type !== OrderType.MARKET && !price) newErrors.push('Price is required for limit orders');

        setErrors(newErrors);
        return newErrors.length === 0;
    };

    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();
        if (!validateForm()) return;

        try {
            await onSubmit({
                symbol,
                type,
                side,
                quantity: parseFloat(quantity),
                price: price ? parseFloat(price) : undefined,
            });

            // Reset form on success
            setSymbol('');
            setQuantity('');
            setPrice('');
            setErrors([]);
        } catch (error) {
            setErrors([error instanceof Error ? error.message : 'Failed to submit order']);
        }
    };

    return (
        <form onSubmit={handleSubmit} data-testid="order-entry-form" className="space-y-4">
            <div>
                <label className="block text-sm font-medium text-gray-700">Symbol</label>
                <input
                    type="text"
                    value={symbol}
                    onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                    data-testid="symbol-input"
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
            </div>

            <div>
                <label className="block text-sm font-medium text-gray-700">Order Type</label>
                <select
                    value={type}
                    onChange={(e) => setType(e.target.value as OrderType)}
                    data-testid="order-type-select"
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                >
                    <option value={OrderType.MARKET}>Market</option>
                    <option value={OrderType.LIMIT}>Limit</option>
                    <option value={OrderType.STOP}>Stop</option>
                </select>
            </div>

            <div>
                <label className="block text-sm font-medium text-gray-700">Side</label>
                <select
                    value={side}
                    onChange={(e) => setSide(e.target.value as OrderSide)}
                    data-testid="order-side-select"
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                >
                    <option value={OrderSide.BUY}>Buy</option>
                    <option value={OrderSide.SELL}>Sell</option>
                </select>
            </div>

            <div>
                <label className="block text-sm font-medium text-gray-700">Quantity</label>
                <input
                    type="number"
                    value={quantity}
                    onChange={(e) => setQuantity(e.target.value)}
                    data-testid="quantity-input"
                    step="any"
                    min="0"
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
                {errors.includes('Quantity must be greater than 0') && (
                    <p data-testid="quantity-error" className="mt-1 text-sm text-red-600">
                        Quantity must be greater than 0
                    </p>
                )}
            </div>

            {type === OrderType.LIMIT && (
                <div>
                    <label className="block text-sm font-medium text-gray-700">Price</label>
                    <input
                        type="number"
                        value={price}
                        onChange={(e) => setPrice(e.target.value)}
                        data-testid="price-input"
                        step="any"
                        min="0"
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                    />
                </div>
            )}

            {errors.length > 0 && (
                <div data-testid="order-form-errors" className="rounded-md bg-red-50 p-4">
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
                data-testid="submit-order-button"
                className={`w-full py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white ${
                    isSubmitting
                        ? 'bg-gray-400 cursor-not-allowed'
                        : side === OrderSide.BUY
                        ? 'bg-green-600 hover:bg-green-700'
                        : 'bg-red-600 hover:bg-red-700'
                }`}
            >
                {isSubmitting ? 'Submitting...' : `${side} ${symbol || 'Order'}`}
            </button>
        </form>
    );
} 