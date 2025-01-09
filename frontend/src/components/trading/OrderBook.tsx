import { useEffect, useState, useMemo } from 'react';
import type { OrderBook as OrderBookType } from '@/types/trading';
import { tradingService } from '@/services/trading/tradingService';

interface OrderBookProps {
  symbol: string;
  depth?: number;
  onPriceSelect?: (price: number) => void;
}

export default function OrderBook({ symbol, depth = 15, onPriceSelect }: OrderBookProps) {
  const [orderBook, setOrderBook] = useState<OrderBookType | null>(null);
  const [totalBidVolume, totalAskVolume] = useMemo(() => {
    if (!orderBook) return [0, 0];
    
    const bidVolume = orderBook.bids.reduce((sum, [_, volume]) => sum + volume, 0);
    const askVolume = orderBook.asks.reduce((sum, [_, volume]) => sum + volume, 0);
    
    return [bidVolume, askVolume];
  }, [orderBook]);

  useEffect(() => {
    let ws: WebSocket;
    let isSubscribed = true;

    const connectWebSocket = () => {
      ws = new WebSocket(process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:3001/ws');

      ws.onopen = () => {
        ws.send(JSON.stringify({
          type: 'subscribe',
          channel: 'orderbook',
          symbol
        }));
      };

      ws.onmessage = (event) => {
        if (!isSubscribed) return;
        
        const data = JSON.parse(event.data);
        if (data.type === 'orderbook') {
          setOrderBook(data.data);
        }
      };

      ws.onclose = () => {
        if (isSubscribed) {
          setTimeout(connectWebSocket, 1000); // Reconnect after 1 second
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        ws.close();
      };
    };

    // Initial order book load
    const loadOrderBook = async () => {
      try {
        const data = await tradingService.getOrderBook(symbol);
        if (isSubscribed) {
          setOrderBook(data);
        }
      } catch (error) {
        console.error('Failed to load order book:', error);
      }
    };

    loadOrderBook();
    connectWebSocket();

    return () => {
      isSubscribed = false;
      if (ws) {
        ws.close();
      }
    };
  }, [symbol]);

  const renderPriceLevel = (price: number, volume: number, total: number, side: 'bid' | 'ask') => {
    const percentage = (total / (side === 'bid' ? totalBidVolume : totalAskVolume)) * 100;
    const formattedPrice = price.toFixed(2);
    const formattedVolume = volume.toFixed(4);
    const formattedTotal = total.toFixed(4);

    return (
      <div
        key={price}
        className="grid grid-cols-3 gap-4 py-1 text-sm cursor-pointer hover:bg-gray-50"
        onClick={() => onPriceSelect?.(price)}
      >
        <span className={side === 'ask' ? 'text-red-500' : 'text-green-500'}>
          {formattedPrice}
        </span>
        <span className="text-right">{formattedVolume}</span>
        <div className="relative">
          <span className="relative z-10">{formattedTotal}</span>
          <div
            className={`absolute top-0 right-0 h-full ${
              side === 'ask' ? 'bg-red-100' : 'bg-green-100'
            }`}
            style={{ width: `${percentage}%` }}
          />
        </div>
      </div>
    );
  };

  if (!orderBook) {
    return (
      <div className="p-4 text-center">
        Loading order book...
      </div>
    );
  }

  const asks = orderBook.asks
    .slice(0, depth)
    .reverse()
    .map(([price, volume], index, array) => {
      const total = array
        .slice(0, index + 1)
        .reduce((sum, [_, vol]) => sum + vol, 0);
      return renderPriceLevel(price, volume, total, 'ask');
    });

  const bids = orderBook.bids
    .slice(0, depth)
    .map(([price, volume], index, array) => {
      const total = array
        .slice(0, index + 1)
        .reduce((sum, [_, vol]) => sum + vol, 0);
      return renderPriceLevel(price, volume, total, 'bid');
    });

  const spreadValue = orderBook.asks[0][0] - orderBook.bids[0][0];
  const spreadPercentage = (spreadValue / orderBook.asks[0][0]) * 100;

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="mb-4">
        <h3 className="text-lg font-semibold mb-2">Order Book</h3>
        <div className="text-sm text-gray-500">
          Spread: {spreadValue.toFixed(2)} ({spreadPercentage.toFixed(2)}%)
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4 text-xs text-gray-500 mb-2">
        <span>Price</span>
        <span className="text-right">Amount</span>
        <span className="text-right">Total</span>
      </div>

      <div className="space-y-1">
        {asks}
        <div className="border-t border-b border-gray-200 my-2" />
        {bids}
      </div>
    </div>
  );
} 