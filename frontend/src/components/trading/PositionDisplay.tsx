import { useState, useEffect } from 'react';

interface Position {
    id: string;
    symbol: string;
    side: 'BUY' | 'SELL';
    size: number;
    entryPrice: number;
    currentPrice: number;
    unrealizedPnL: number;
    unrealizedPnLPercentage: number;
    liquidationPrice?: number;
    margin: number;
    leverage: number;
    timestamp: string;
}

interface PositionDisplayProps {
    positions: Position[];
    onClosePosition?: (positionId: string) => Promise<void>;
    isClosing?: { [key: string]: boolean };
}

export function PositionDisplay({ positions, onClosePosition, isClosing = {} }: PositionDisplayProps) {
    const [sortField, setSortField] = useState<keyof Position>('timestamp');
    const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');
    const [sortedPositions, setSortedPositions] = useState<Position[]>(positions);

    useEffect(() => {
        const sorted = [...positions].sort((a, b) => {
            const aValue = a[sortField];
            const bValue = b[sortField];

            if (typeof aValue === 'string' && typeof bValue === 'string') {
                return sortDirection === 'asc' 
                    ? aValue.localeCompare(bValue)
                    : bValue.localeCompare(aValue);
            }

            if (typeof aValue === 'number' && typeof bValue === 'number') {
                return sortDirection === 'asc' 
                    ? aValue - bValue
                    : bValue - aValue;
            }

            return 0;
        });

        setSortedPositions(sorted);
    }, [positions, sortField, sortDirection]);

    const handleSort = (field: keyof Position) => {
        setSortDirection(currentDirection => 
            sortField === field 
                ? currentDirection === 'asc' ? 'desc' : 'asc'
                : 'asc'
        );
        setSortField(field);
    };

    const formatNumber = (num: number, decimals: number = 2) => {
        return new Intl.NumberFormat('en-US', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals,
        }).format(num);
    };

    const formatCurrency = (num: number) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
        }).format(num);
    };

    const formatDate = (timestamp: string) => {
        return new Date(timestamp).toLocaleString();
    };

    if (positions.length === 0) {
        return (
            <div 
                data-testid="no-positions-message"
                className="text-center py-8 text-gray-500"
            >
                No open positions
            </div>
        );
    }

    return (
        <div data-testid="positions-table" className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                    <tr>
                        <th
                            scope="col"
                            className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
                            onClick={() => handleSort('symbol')}
                        >
                            Symbol
                        </th>
                        <th
                            scope="col"
                            className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
                            onClick={() => handleSort('side')}
                        >
                            Side
                        </th>
                        <th
                            scope="col"
                            className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
                            onClick={() => handleSort('size')}
                        >
                            Size
                        </th>
                        <th
                            scope="col"
                            className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
                            onClick={() => handleSort('entryPrice')}
                        >
                            Entry Price
                        </th>
                        <th
                            scope="col"
                            className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
                            onClick={() => handleSort('currentPrice')}
                        >
                            Current Price
                        </th>
                        <th
                            scope="col"
                            className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
                            onClick={() => handleSort('unrealizedPnL')}
                        >
                            Unrealized P&L
                        </th>
                        <th
                            scope="col"
                            className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
                            onClick={() => handleSort('leverage')}
                        >
                            Leverage
                        </th>
                        <th
                            scope="col"
                            className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
                            onClick={() => handleSort('liquidationPrice')}
                        >
                            Liquidation Price
                        </th>
                        <th
                            scope="col"
                            className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                        >
                            Actions
                        </th>
                    </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                    {sortedPositions.map((position) => (
                        <tr key={position.id} data-testid={`position-row-${position.id}`}>
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                {position.symbol}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                <span
                                    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                        position.side === 'BUY'
                                            ? 'bg-green-100 text-green-800'
                                            : 'bg-red-100 text-red-800'
                                    }`}
                                >
                                    {position.side}
                                </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                {formatNumber(position.size)}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                {formatCurrency(position.entryPrice)}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                {formatCurrency(position.currentPrice)}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm">
                                <div
                                    className={`${
                                        position.unrealizedPnL >= 0
                                            ? 'text-green-600'
                                            : 'text-red-600'
                                    }`}
                                >
                                    {formatCurrency(position.unrealizedPnL)}
                                    <span className="text-xs ml-1">
                                        ({formatNumber(position.unrealizedPnLPercentage)}%)
                                    </span>
                                </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                {formatNumber(position.leverage)}x
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                {position.liquidationPrice
                                    ? formatCurrency(position.liquidationPrice)
                                    : 'N/A'}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                {onClosePosition && (
                                    <button
                                        onClick={() => onClosePosition(position.id)}
                                        disabled={isClosing[position.id]}
                                        data-testid={`close-position-${position.id}`}
                                        className={`inline-flex items-center px-3 py-1 border border-transparent text-xs font-medium rounded-md text-white ${
                                            isClosing[position.id]
                                                ? 'bg-gray-400 cursor-not-allowed'
                                                : 'bg-red-600 hover:bg-red-700'
                                        }`}
                                    >
                                        {isClosing[position.id] ? 'Closing...' : 'Close'}
                                    </button>
                                )}
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
} 