import { useState } from 'react';
import { OrderRequest, OrderResponse, RiskValidation } from '@/types/trading';
import { OrderEntryForm } from './OrderEntryForm';

interface OrderEntryProps {
    onValidation?: (validation: RiskValidation) => void;
    accountBalance: number;
}

export function OrderEntry({ onValidation, accountBalance }: OrderEntryProps) {
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [lastResponse, setLastResponse] = useState<OrderResponse | null>(null);

    const handleSubmit = async (order: OrderRequest) => {
        setIsSubmitting(true);
        try {
            // First, validate the order
            const validationResponse = await fetch('/api/trading/validate-order', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    order,
                    accountBalance
                }),
            });

            const validationData = await validationResponse.json();
            onValidation?.(validationData);

            if (!validationData.isValid) {
                throw new Error(validationData.messages.join('. '));
            }

            // If validation passes, submit the order
            const response = await fetch('/api/trading/orders', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(order),
            });

            const data = await response.json();
            setLastResponse(data);

            if (!response.ok) {
                throw new Error(data.message || 'Failed to submit order');
            }

            // Show success message or update UI
            console.log('Order submitted successfully:', data);
        } catch (error) {
            console.error('Error submitting order:', error);
            throw error;
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="max-w-md mx-auto">
            <h2 className="text-2xl font-bold mb-4">Place Order</h2>
            <OrderEntryForm 
                onSubmit={handleSubmit} 
                isSubmitting={isSubmitting}
                accountBalance={accountBalance}
            />
            
            {lastResponse && (
                <div className={`mt-4 p-4 rounded-md ${
                    lastResponse.success ? 'bg-green-50' : 'bg-red-50'
                }`}>
                    <p className={`text-sm ${
                        lastResponse.success ? 'text-green-800' : 'text-red-800'
                    }`}>
                        {lastResponse.message}
                    </p>
                    {lastResponse.order && (
                        <div className="mt-2 text-sm text-gray-600">
                            <p>Order ID: {lastResponse.order.id}</p>
                            <p>Status: {lastResponse.order.status}</p>
                            <p>Type: {lastResponse.order.type}</p>
                            <p>Side: {lastResponse.order.side}</p>
                            <p>Quantity: {lastResponse.order.quantity}</p>
                            {lastResponse.order.price && (
                                <p>Price: {lastResponse.order.price}</p>
                            )}
                            {lastResponse.order.stopPrice && (
                                <p>Stop Price: {lastResponse.order.stopPrice}</p>
                            )}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
} 