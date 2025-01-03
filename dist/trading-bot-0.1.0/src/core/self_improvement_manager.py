from typing import Dict, Optional
import logging
from datetime import datetime
import json
from pathlib import Path
from ..analysis.performance_analyzer import SelfLearningAnalyzer
from ..utils.config_manager import ConfigManager

logger = logging.getLogger(__name__)

class SelfImprovementManager:
    def __init__(self, trading_engine, config_manager: ConfigManager):
        self.trading_engine = trading_engine
        self.config = config_manager
        self.analyzer = SelfLearningAnalyzer()
        
        # Load improvement settings
        self.settings = self._load_improvement_settings()
        
        # Track improvements
        self.improvements_file = Path("data/improvements.json")
        self.applied_improvements = self._load_applied_improvements()
        
    def run_improvement_cycle(self):
        """Run a complete self-improvement cycle."""
        try:
            # Analyze current performance
            performance_results = self.analyzer.analyze_trading_history()
            
            if not performance_results:
                logger.info("Insufficient data for improvement analysis")
                return
                
            # Get recommendations
            recommendations = self.analyzer.get_strategy_recommendations()
            
            # Validate and apply improvements
            for strategy_name, recommendation in recommendations.items():
                if self._should_apply_improvements(strategy_name, recommendation):
                    # Backtest improvements
                    backtest_results = self.analyzer.backtest_improvements(
                        strategy_name,
                        recommendation
                    )
                    
                    if self._validate_improvements(backtest_results):
                        self._apply_improvements(
                            strategy_name,
                            recommendation,
                            backtest_results
                        )
                        
            # Save improvement history
            self._save_applied_improvements()
            
        except Exception as e:
            logger.error(f"Error in improvement cycle: {str(e)}")
            
    def _should_apply_improvements(self,
                                 strategy_name: str,
                                 recommendation: Dict) -> bool:
        """Determine if improvements should be applied."""
        # Check confidence score
        if recommendation['confidence_score'] < self.settings['min_confidence']:
            return False
            
        # Check if recently improved
        last_improvement = self.applied_improvements.get(strategy_name, {}).get(
            'last_update'
        )
        if last_improvement:
            days_since = (
                datetime.now() - datetime.fromisoformat(last_improvement)
            ).days
            if days_since < self.settings['min_days_between_updates']:
                return False
                
        return True
        
    def _validate_improvements(self, backtest_results: Dict) -> bool:
        """Validate improvement results."""
        if not backtest_results:
            return False
            
        improvement_pct = backtest_results['improvement_percentage']
        return improvement_pct >= self.settings['min_improvement_pct']
        
    def _apply_improvements(self,
                          strategy_name: str,
                          recommendation: Dict,
                          backtest_results: Dict):
        """Apply validated improvements."""
        try:
            # Update strategy parameters
            self.trading_engine.update_strategy_parameters(
                strategy_name,
                recommendation['parameter_adjustments']
            )
            
            # Record improvement
            self.applied_improvements[strategy_name] = {
                'last_update': datetime.now().isoformat(),
                'improvements': recommendation,
                'backtest_results': backtest_results,
                'performance_impact': backtest_results['improvement_percentage']
            }
            
            logger.info(
                f"Applied improvements to {strategy_name} "
                f"with {backtest_results['improvement_percentage']}% improvement"
            )
            
        except Exception as e:
            logger.error(f"Error applying improvements: {str(e)}")
            
    def _load_improvement_settings(self) -> Dict:
        """Load self-improvement settings."""
        default_settings = {
            'min_confidence': 0.7,
            'min_improvement_pct': 5.0,
            'min_days_between_updates': 7,
            'max_param_adjustment': 0.2  # 20% max adjustment
        }
        
        return self.config.get_setting('self_improvement', default_settings)
        
    def _load_applied_improvements(self) -> Dict:
        """Load history of applied improvements."""
        try:
            if self.improvements_file.exists():
                with open(self.improvements_file) as f:
                    return json.load(f)
            return {}
            
        except Exception as e:
            logger.error(f"Error loading improvements history: {str(e)}")
            return {}
            
    def _save_applied_improvements(self):
        """Save history of applied improvements."""
        try:
            with open(self.improvements_file, 'w') as f:
                json.dump(self.applied_improvements, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving improvements history: {str(e)}") 