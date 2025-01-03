from typing import Dict, List, Optional
import logging
from datetime import datetime
import pandas as pd

from .api_client import TradingAPIClient
from .risk_manager import RiskManager
from .market_analyzer import MarketAnalyzer
from ..strategies.base_strategy import BaseStrategy
from .strategy_manager import StrategyManager
from ..utils.trade_logger import TradeLogger

logger = logging.getLogger(__name__)

class TradingEngine:
    def __init__(self, api_key: str, api_secret: str):
        self.api_client = TradingAPIClient(api_key, api_secret)
        self.risk_manager = RiskManager()
        self.market_analyzer = MarketAnalyzer()
        self.strategy_manager = StrategyManager()
        self.trade_logger = TradeLogger()
        self.active_trades: Dict[str, Dict] = {}
        self.market_data: Dict[str, pd.DataFrame] = {}
        self.require_user_confirmation: bool = False  # Default to automated trading
        
    def add_strategy(self, strategy: BaseStrategy) -> None:
        """Add a trading strategy to the engine."""
        self.strategy_manager.add_strategy(strategy)
        self.trade_logger.log_system_config({
            'event': 'strategy_added',
            'strategy_name': strategy.name
        })
        
    def update_market_data(self, symbol: str, timeframe: str, data: pd.DataFrame) -> None:
        """Update market data for analysis."""
        key = f"{symbol}_{timeframe}"
        self.market_data[key] = data
        logger.debug(f"Updated market data for {key}")
        
    def analyze_markets(self) -> Dict:
        """Analyze all tracked markets."""
        analysis_results = {}
        
        for key, data in self.market_data.items():
            try:
                market_condition = self.market_analyzer.analyze_market_condition(data)
                analysis_results[key] = market_condition
                logger.info(f"Market analysis completed for {key}")
            except Exception as e:
                logger.error(f"Error analyzing market {key}: {str(e)}")
                
        return analysis_results
        
    def generate_signals(self) -> List[Dict]:
        """Generate trading signals from appropriate strategies."""
        signals = []
        analysis = self.analyze_markets()
        
        for market_key, market_condition in analysis.items():
            # Select appropriate strategies for current market condition
            selected_strategies = self.strategy_manager.select_strategies(market_condition)
            
            for strategy in selected_strategies:
                try:
                    signal = strategy.generate_signals({market_key: market_condition})
                    if signal:
                        signal_data = {
                            'strategy': strategy.name,
                            'signal': signal,
                            'timestamp': datetime.now()
                        }
                        signals.append(signal_data)
                        self.trade_logger.log_trade_signal(strategy.name, signal)
                except Exception as e:
                    logger.error(f"Error generating signals for {strategy.name}: {str(e)}")
                    self.trade_logger.log_error('signal_generation', {
                        'strategy': strategy.name,
                        'error': str(e)
                    })
        
        return signals
        
    def execute_trades(self, signals: List[Dict]) -> None:
        """Execute trades based on generated signals."""
        for signal in signals:
            try:
                if not self.validate_trade(signal):
                    continue
                    
                # Get user confirmation if required
                if not self.get_user_confirmation(signal):
                    logger.info("Trade rejected by user")
                    continue
                
                # Calculate position size
                entry_price = signal['signal'].get('entry_price')
                stop_loss = signal['signal'].get('stop_loss')
                
                if not entry_price or not stop_loss:
                    logger.warning(f"Missing entry or stop loss price in signal: {signal}")
                    continue
                    
                account_balance = self.get_account_balance()
                position_size = self.risk_manager.calculate_position_size(
                    account_balance,
                    entry_price,
                    stop_loss
                )
                
                # Place the trade
                order = self.api_client.place_market_order(
                    product_id=signal['signal']['symbol'],
                    side=signal['signal']['side'],
                    size=position_size
                )
                
                # Track the trade
                trade_id = order['id']
                self.active_trades[trade_id] = {
                    'signal': signal,
                    'order': order,
                    'position_size': position_size,
                    'entry_time': datetime.now()
                }
                
                # Update risk exposure
                self.risk_manager.update_exposure(
                    trade_id,
                    position_size,
                    self.risk_manager.max_risk_per_trade
                )
                
                # Log trade execution
                self.trade_logger.log_trade_execution(
                    signal['strategy'],
                    {
                        'trade_id': trade_id,
                        'signal': signal,
                        'position_size': position_size,
                        'entry_time': datetime.now().isoformat()
                    }
                )
                
                logger.info(f"Executed trade for signal: {signal}")
                
            except Exception as e:
                self.trade_logger.log_error('trade_execution', {
                    'signal': signal,
                    'error': str(e)
                })
                logger.error(f"Error executing trade for signal {signal}: {str(e)}")
                
    def validate_trade(self, signal: Dict) -> bool:
        """Validate if a trade should be executed."""
        # Check if we have necessary signal components
        required_fields = ['symbol', 'side', 'entry_price', 'stop_loss']
        if not all(field in signal['signal'] for field in required_fields):
            logger.warning(f"Missing required fields in signal: {signal}")
            return False
            
        # Validate with risk manager
        if not self.risk_manager.validate_trade(signal['signal']):
            return False
            
        return True
        
    def get_account_balance(self) -> float:
        """Get current account balance."""
        try:
            accounts = self.api_client.get_accounts()
            # Assume we're trading with the first account
            return float(accounts[0]['balance'])
        except Exception as e:
            logger.error(f"Error fetching account balance: {str(e)}")
            raise 
        
    def set_user_confirmation(self, required: bool) -> None:
        """Enable or disable user confirmation requirement."""
        self.require_user_confirmation = required
        self.trade_logger.log_system_config({
            'user_confirmation_required': required
        })
        logger.info(f"User confirmation requirement set to: {required}")
        
    def get_user_confirmation(self, signal: Dict) -> bool:
        """Get user confirmation for a trade signal."""
        if not self.require_user_confirmation:
            return True
            
        print("\n=== Trade Confirmation Required ===")
        print(f"Strategy: {signal['strategy']}")
        print(f"Symbol: {signal['signal']['symbol']}")
        print(f"Side: {signal['signal']['side']}")
        print(f"Entry Price: {signal['signal']['entry_price']}")
        print(f"Stop Loss: {signal['signal']['stop_loss']}")
        print(f"Take Profit: {signal['signal'].get('take_profit', 'Not set')}")
        
        response = input("\nExecute this trade? (yes/no): ").lower().strip()
        confirmed = response in ['y', 'yes']
        
        self.trade_logger.log_user_decision({
            'signal': signal,
            'confirmed': confirmed,
            'timestamp': datetime.now().isoformat()
        })
        
        return confirmed 