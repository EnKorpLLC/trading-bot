from typing import Dict, List, Optional
import logging
from datetime import datetime
import pandas as pd
import asyncio

# Core components
from .tradelocker_client import TradeLockerClient
from .account_manager import AccountManager
from .strategy_manager import StrategyManager
from .risk_manager import RiskManager, RiskParameters
from .market_analyzer import MarketAnalyzer
from .safety_system import SafetySystem
from ..utils.trade_logger import TradeLogger

logger = logging.getLogger(__name__)

class TradingEngine:
    def __init__(self, api_key: str, api_secret: str):
        # Core components
        self.client = TradeLockerClient(api_key, api_secret)
        self.account_manager = AccountManager()
        self.risk_manager = RiskManager()
        self.market_analyzer = None  # Will be initialized after client connection
        self.strategy_manager = StrategyManager()
        self.safety_system = SafetySystem()
        self.trade_logger = TradeLogger()
        
        # State tracking
        self.active_trades: Dict[str, Dict] = {}
        self.market_data: Dict[str, pd.DataFrame] = {}
        self.require_user_confirmation: bool = False
        self.is_running: bool = False
        
        # Performance monitoring
        self._last_account_update = 0
        self.ACCOUNT_UPDATE_INTERVAL = 60  # Update account info every 60 seconds
        
        # Background tasks
        self._market_update_task = None
        self._risk_update_task = None
        
    async def start(self, credentials: Dict):
        """Start the trading engine."""
        try:
            # Connect to trading platform
            if not await self.client.connect(credentials):
                raise Exception("Failed to connect to trading platform")
                
            # Initialize components that require client
            self.market_analyzer = MarketAnalyzer(self.client)
            
            # Start background tasks
            self._market_update_task = asyncio.create_task(self._market_update_loop())
            self._risk_update_task = asyncio.create_task(self._risk_update_loop())
            
            self.is_running = True
            logger.info("Trading engine started successfully")
            
        except Exception as e:
            logger.error(f"Error starting trading engine: {str(e)}")
            raise
            
    async def stop(self):
        """Stop the trading engine."""
        try:
            self.is_running = False
            
            # Cancel background tasks
            if self._market_update_task:
                self._market_update_task.cancel()
            if self._risk_update_task:
                self._risk_update_task.cancel()
                
            # Close positions if configured
            await self._close_all_positions()
            
            # Disconnect from platform
            await self.client.disconnect()
            
            logger.info("Trading engine stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping trading engine: {str(e)}")
            raise
            
    def add_strategy(self, strategy) -> None:
        """Add a trading strategy to the engine."""
        self.strategy_manager.add_strategy(strategy)
        self.trade_logger.log_system_config({
            'event': 'strategy_added',
            'strategy_name': strategy.name
        })
        
    async def process_strategy_signal(self, signal: Dict) -> Dict:
        """Process and execute a strategy signal."""
        try:
            if not self.validate_trade(signal):
                return {'status': 'rejected', 'reason': 'validation_failed'}
                
            # Get user confirmation if required
            if not await self.get_user_confirmation(signal):
                return {'status': 'rejected', 'reason': 'user_rejected'}
                
            # Calculate position size
            account_balance = await self.client.get_account_balance()
            position_size = self.risk_manager.calculate_position_size(
                account_balance,
                signal['entry_price'],
                signal['stop_loss']
            )
            
            # Execute trade
            order = await self.client.place_market_order(
                symbol=signal['symbol'],
                side=signal['side'],
                size=position_size,
                stop_loss=signal['stop_loss'],
                take_profit=signal.get('take_profit')
            )
            
            # Track trade
            trade_id = order['id']
            self.active_trades[trade_id] = {
                'signal': signal,
                'order': order,
                'position_size': position_size,
                'entry_time': datetime.now()
            }
            
            # Update risk exposure
            self.risk_manager.update_exposure(trade_id, position_size)
            
            # Log execution
            self.trade_logger.log_trade_execution(
                signal['strategy'],
                {
                    'trade_id': trade_id,
                    'signal': signal,
                    'position_size': position_size,
                    'entry_time': datetime.now().isoformat()
                }
            )
            
            return {'status': 'executed', 'order': order}
            
        except Exception as e:
            logger.error(f"Error processing strategy signal: {str(e)}")
            return {'status': 'error', 'error': str(e)}
            
    async def _market_update_loop(self):
        """Background task for market updates."""
        while self.is_running:
            try:
                # Update market data
                for symbol in self.strategy_manager.get_tracked_symbols():
                    data = await self.client.get_market_data(symbol)
                    self.update_market_data(symbol, data)
                    
                await asyncio.sleep(1)  # Update every second
                
            except Exception as e:
                logger.error(f"Error in market update loop: {str(e)}")
                await asyncio.sleep(5)  # Wait before retrying
                
    async def _risk_update_loop(self):
        """Background task for risk management."""
        while self.is_running:
            try:
                current_time = datetime.now().timestamp()
                
                # Update account info periodically
                if current_time - self._last_account_update >= self.ACCOUNT_UPDATE_INTERVAL:
                    balance = await self.client.get_account_balance()
                    self.account_manager.update_balance(balance)
                    self._last_account_update = current_time
                    
                # Check risk limits
                risk_status = self.risk_manager.check_risk_limits()
                if not risk_status['within_limits']:
                    await self._handle_risk_breach(risk_status)
                    
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in risk update loop: {str(e)}")
                await asyncio.sleep(5)
                
    async def _close_all_positions(self):
        """Close all open positions."""
        try:
            positions = await self.client.get_open_positions()
            for position in positions:
                await self.client.close_position(position['id'])
                
        except Exception as e:
            logger.error(f"Error closing positions: {str(e)}")
            
    def get_market_analysis(self, symbol: str) -> Dict:
        """Get market analysis for a symbol."""
        try:
            if symbol in self.market_data:
                return self.market_analyzer.analyze_market(
                    symbol,
                    self.market_data[symbol]
                )
            return {}
            
        except Exception as e:
            logger.error(f"Error analyzing market for {symbol}: {str(e)}")
            return {}
