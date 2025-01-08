import numpy as np
import pandas as pd
from deap import base, creator, tools, algorithms
import random
import os
import sys

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backtesting.advanced_backtester import AdvancedBacktester

class StrategyOptimizer:
    def __init__(self, data, param_ranges, population_size=50, generations=30):
        self.data = data
        self.param_ranges = param_ranges
        self.population_size = population_size
        self.generations = generations
        self.backtester = AdvancedBacktester()
        
        # Set up genetic algorithm components
        self.setup_toolbox()
    
    def setup_toolbox(self):
        """Initialize the genetic algorithm components"""
        # Create fitness and individual classes
        creator.create("FitnessMax", base.Fitness, weights=(1.0,))
        creator.create("Individual", list, fitness=creator.FitnessMax)
        
        self.toolbox = base.Toolbox()
        
        # Register attribute generators
        for param_name, param_range in self.param_ranges.items():
            if isinstance(param_range[0], float):
                self.toolbox.register(
                    f"attr_{param_name}",
                    random.uniform,
                    param_range[0],
                    param_range[1]
                )
            else:
                self.toolbox.register(
                    f"attr_{param_name}",
                    random.randint,
                    param_range[0],
                    param_range[1]
                )
        
        # Register individual and population creation
        attrs = [getattr(self.toolbox, f"attr_{param}") for param in self.param_ranges.keys()]
        self.toolbox.register("individual", tools.initCycle, creator.Individual, tuple(attrs), n=1)
        self.toolbox.register("population", tools.initRepeat, list, self.toolbox.individual)
        
        # Register genetic operators
        self.toolbox.register("evaluate", self._evaluate_strategy)
        self.toolbox.register("mate", tools.cxBlend, alpha=0.5)
        self.toolbox.register("mutate", tools.mutGaussian, mu=0, sigma=1, indpb=0.2)
        self.toolbox.register("select", tools.selTournament, tournsize=3)
    
    def _evaluate_strategy(self, individual):
        """Evaluate a strategy with given parameters using the backtester"""
        # Convert individual to strategy parameters
        strategy_params = dict(zip(self.param_ranges.keys(), individual))
        
        # Run backtest
        results = self.backtester.run_backtest(self.data, strategy_params)
        
        # Calculate fitness (can be modified based on optimization goals)
        fitness = results.sharpe_ratio * (1 + results.returns) * (1 - results.max_drawdown)
        
        return (fitness,)
    
    def optimize(self):
        """Run the genetic algorithm to find optimal strategy parameters"""
        # Create initial population
        pop = self.toolbox.population(n=self.population_size)
        
        # Track the best individual
        hof = tools.HallOfFame(1)
        
        # Track statistics
        stats = tools.Statistics(lambda ind: ind.fitness.values)
        stats.register("avg", np.mean)
        stats.register("min", np.min)
        stats.register("max", np.max)
        
        # Run the genetic algorithm
        final_pop, logbook = algorithms.eaSimple(
            pop,
            self.toolbox,
            cxpb=0.7,  # Crossover probability
            mutpb=0.3,  # Mutation probability
            ngen=self.generations,
            stats=stats,
            halloffame=hof,
            verbose=True
        )
        
        # Get the best parameters
        best_params = dict(zip(self.param_ranges.keys(), hof[0]))
        
        # Run a final backtest with the best parameters
        final_results = self.backtester.run_backtest(self.data, best_params)
        
        return {
            'best_parameters': best_params,
            'best_fitness': hof[0].fitness.values[0],
            'final_results': {
                'returns': float(final_results.returns),
                'sharpe_ratio': float(final_results.sharpe_ratio),
                'max_drawdown': float(final_results.max_drawdown),
                'win_rate': float(final_results.win_rate)
            },
            'optimization_history': logbook
        } 