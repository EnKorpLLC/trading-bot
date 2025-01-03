from typing import Dict, List, Optional
import pandas as pd
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class MarketSimulator:
    def __init__(self):
        self.reset()
        
    def reset(self, data_manager=None, initial_capital: float = 10000.0):
        """Reset simulator state."""
        self.data_manager = data_manager
        self.current_index = 0
        self.equity = initial_capital
        self.balance = initial_capital
        self.positions = {}
        self.pending_orders = []
        self.closed_trades = []
        self.current_time = None
        
    def next(self) -> bool:
        """Move to next timestamp."""
        if self.data_manager is None:
            return False
            
        if self.current_index >= len(self.data_manager.get_timestamps()):
            return False
            
        self.current_time = self.data_manager.get_timestamps()[self.current_index]
        self.current_index += 1
        
        return True
        
    def get_market_data(self) -> Dict:
        """Get current market data."""
        return self.data_manager.get_data_at(self.current_time)
        
    def process_signal(self, signal: Dict):
        """Process a trading signal."""
        # Validate signal
        if not self._validate_signal(signal):
            return
            
        # Create order
        order = {
            'symbol': signal['symbol'],
            'type': 'market',
            'side': signal['side'],
            'entry_price': signal['entry_price'],
            'stop_loss': signal['stop_loss'],
            'take_profit': signal['take_profit'],
            'timestamp': self.current_time,
            'size': self._calculate_position_size(signal)
        }
        
        # Execute order
        self._execute_order(order)
        
    def update_positions(self):
        """Update open positions."""
        current_prices = self.get_market_data()
        
        for symbol, position in list(self.positions.items()):
            price = current_prices[symbol]['close']
            
            # Check stop loss
            if (position['side'] == 'buy' and price <= position['stop_loss'] or
                position['side'] == 'sell' and price >= position['stop_loss']):
                self._close_position(symbol, price, 'stop_loss')
                continue
                
            # Check take profit
            if (position['side'] == 'buy' and price >= position['take_profit'] or
                position['side'] == 'sell' and price <= position['take_profit']):
                self._close_position(symbol, price, 'take_profit')
                continue
                
            # Update unrealized P&L
            position['unrealized_pnl'] = self._calculate_pnl(
                position['side'],
                position['entry_price'],
                price,
                position['size']
            )
            
    def get_current_state(self) -> Dict:
        """Get current simulator state."""
        return {
            'timestamp': self.current_time,
            'equity': self.equity,
            'balance': self.balance,
            'positions': self.positions.copy(),
            'daily_pnl': self._calculate_daily_pnl()
        }
        
    def get_closed_trades(self) -> List[Dict]:
        """Get list of closed trades."""
        return self.closed_trades
        
    def _validate_signal(self, signal: Dict) -> bool:
        """Validate trading signal."""
        required_fields = ['symbol', 'side', 'entry_price', 'stop_loss', 'take_profit']
        return all(field in signal for field in required_fields)
        
    def _calculate_position_size(self, signal: Dict) -> float:
        """Calculate position size based on risk management rules."""
        risk_per_trade = self.equity * 0.01  # 1% risk per trade
        price_risk = abs(signal['entry_price'] - signal['stop_loss'])
        
        return risk_per_trade / price_risk
        
    def _execute_order(self, order: Dict):
        """Execute a trading order."""
        # Check if we already have a position in this symbol
        if order['symbol'] in self.positions:
            return
            
        # Calculate required margin
        required_margin = order['entry_price'] * order['size']
        
        # Check if we have enough balance
        if required_margin > self.balance:
            return
            
        # Open position
        self.positions[order['symbol']] = {
            'side': order['side'],
            'entry_price': order['entry_price'],
            'stop_loss': order['stop_loss'],
            'take_profit': order['take_profit'],
            'size': order['size'],
            'entry_time': self.current_time,
            'unrealized_pnl': 0.0
        }
        
        # Update balance
        self.balance -= required_margin
        
    def _close_position(self, symbol: str, exit_price: float, exit_reason: str):
        """Close an open position."""
        position = self.positions[symbol]
        
        # Calculate P&L
        pnl = self._calculate_pnl(
            position['side'],
            position['entry_price'],
            exit_price,
            position['size']
        )
        
        # Record trade
        self.closed_trades.append({
            'symbol': symbol,
            'side': position['side'],
            'entry_price': position['entry_price'],
            'exit_price': exit_price,
            'entry_time': position['entry_time'],
            'exit_time': self.current_time,
            'size': position['size'],
            'pnl': pnl,
            'exit_reason': exit_reason,
            'duration': (self.current_time - position['entry_time']).total_seconds() / 3600  # hours
        })
        
        # Update balance and equity
        self.balance += (position['entry_price'] * position['size']) + pnl
        self.equity += pnl
        
        # Remove position
        del self.positions[symbol]
        
    def _calculate_pnl(self, side: str, entry_price: float, 
                      current_price: float, size: float) -> float:
        """Calculate position P&L."""
        if side == 'buy':
            return (current_price - entry_price) * size
        else:
            return (entry_price - current_price) * size
            
    def _calculate_daily_pnl(self) -> float:
        """Calculate daily P&L."""
        if not hasattr(self, '_last_equity'):
            self._last_equity = self.equity
            return 0.0
            
        daily_pnl = self.equity - self._last_equity
        self._last_equity = self.equity
        return daily_pnl 