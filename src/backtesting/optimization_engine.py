from typing import Dict, List, Optional, Callable
import pandas as pd
import numpy as np
from datetime import datetime
import logging
from concurrent.futures import ProcessPoolExecutor
from itertools import product
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class OptimizationEngine:
    def __init__(self, 
                 backtest_func: Callable,
                 optimization_metric: str = 'sharpe_ratio',
                 max_workers: int = None):
        self.backtest_func = backtest_func
        self.optimization_metric = optimization_metric
        self.max_workers = max_workers
        self.results_cache = {}
        
    def optimize(self, 
                param_ranges: Dict[str, List],
                fixed_params: Dict = None,
                constraints: List[Callable] = None) -> Dict:
        """Run parameter optimization."""
        try:
            # Generate parameter combinations
            param_combinations = self._generate_param_combinations(param_ranges)
            
            # Apply constraints
            if constraints:
                param_combinations = self._apply_constraints(param_combinations, constraints)
                
            # Run parallel optimization
            results = self._run_parallel_optimization(param_combinations, fixed_params)
            
            # Analyze optimization results
            analysis = self._analyze_optimization_results(results)
            
            # Save optimization results
            self._save_optimization_results(analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Optimization error: {str(e)}")
            raise
            
    def _generate_param_combinations(self, param_ranges: Dict[str, List]) -> List[Dict]:
        """Generate all valid parameter combinations."""
        keys = param_ranges.keys()
        values = param_ranges.values()
        combinations = list(product(*values))
        
        return [dict(zip(keys, combo)) for combo in combinations]
        
    def _apply_constraints(self, 
                         combinations: List[Dict],
                         constraints: List[Callable]) -> List[Dict]:
        """Apply constraints to parameter combinations."""
        valid_combinations = []
        
        for params in combinations:
            if all(constraint(params) for constraint in constraints):
                valid_combinations.append(params)
                
        return valid_combinations
        
    def _run_parallel_optimization(self, 
                                 param_combinations: List[Dict],
                                 fixed_params: Dict) -> List[Dict]:
        """Run backtests in parallel."""
        results = []
        
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            
            for params in param_combinations:
                # Combine with fixed parameters
                full_params = {**params}
                if fixed_params:
                    full_params.update(fixed_params)
                    
                # Submit backtest job
                future = executor.submit(self._run_single_backtest, full_params)
                futures.append((params, future))
                
            # Collect results
            for params, future in futures:
                try:
                    backtest_result = future.result()
                    results.append({
                        'parameters': params,
                        'results': backtest_result,
                        'metric_value': self._extract_metric(backtest_result)
                    })
                except Exception as e:
                    logger.error(f"Backtest failed for params {params}: {str(e)}")
                    
        return results
        
    def _run_single_backtest(self, params: Dict) -> Dict:
        """Run a single backtest with given parameters."""
        # Check cache first
        param_key = json.dumps(params, sort_keys=True)
        if param_key in self.results_cache:
            return self.results_cache[param_key]
            
        # Run backtest
        result = self.backtest_func(**params)
        
        # Cache result
        self.results_cache[param_key] = result
        
        return result
        
    def _extract_metric(self, backtest_result: Dict) -> float:
        """Extract optimization metric from backtest results."""
        try:
            return backtest_result['summary'][self.optimization_metric]
        except KeyError:
            logger.error(f"Metric {self.optimization_metric} not found in results")
            return float('-inf')
            
    def _analyze_optimization_results(self, results: List[Dict]) -> Dict:
        """Analyze optimization results."""
        # Sort results by metric value
        sorted_results = sorted(
            results,
            key=lambda x: x['metric_value'],
            reverse=True
        )
        
        # Get top parameters
        top_n = min(10, len(sorted_results))
        top_results = sorted_results[:top_n]
        
        # Calculate parameter importance
        param_importance = self._calculate_parameter_importance(results)
        
        # Generate surface plots for top parameter pairs
        surface_plots = self._generate_surface_plots(results)
        
        return {
            'best_parameters': top_results[0]['parameters'],
            'best_metric_value': top_results[0]['metric_value'],
            'top_results': top_results,
            'parameter_importance': param_importance,
            'surface_plots': surface_plots,
            'total_combinations': len(results),
            'timestamp': datetime.now().isoformat()
        }
        
    def _calculate_parameter_importance(self, results: List[Dict]) -> Dict:
        """Calculate parameter importance using correlation analysis."""
        # Convert results to DataFrame
        df = pd.DataFrame([
            {**r['parameters'], 'metric': r['metric_value']}
            for r in results
        ])
        
        # Calculate correlations
        correlations = df.corr()['metric'].drop('metric')
        
        return correlations.to_dict()
        
    def _save_optimization_results(self, analysis: Dict):
        """Save optimization results to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path("optimization_results")
        output_dir.mkdir(exist_ok=True)
        
        output_file = output_dir / f"optimization_{timestamp}.json"
        with open(output_file, 'w') as f:
            json.dump(analysis, f, indent=2, default=str) 