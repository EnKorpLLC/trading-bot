from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
import sys
import os
from datetime import datetime
import numpy as np
from typing import List, Dict, Any
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project root to Python path
try:
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
    sys.path.append(project_root)
    logger.info(f"Added {project_root} to Python path")
except Exception as e:
    logger.error(f"Error setting up Python path: {e}")

# Import project modules
try:
    from src.ai.model_manager import ModelManager
    from src.backtesting.advanced_backtester import AdvancedBacktester
    from src.analysis.predictive_analytics import PredictiveAnalytics
    from src.strategies.strategy_optimizer import StrategyOptimizer
    from src.data.mt5_connector import MT5Connector
    logger.info("Successfully imported project modules")
except Exception as e:
    logger.error(f"Error importing project modules: {e}")

# Initialize components
try:
    model_manager = ModelManager()
    backtester = AdvancedBacktester()
    analytics = PredictiveAnalytics()
    optimizer = StrategyOptimizer()
    mt5_connector = MT5Connector()
    if not mt5_connector.connect():
        logger.warning("Failed to connect to MT5. Please ensure MetaTrader 5 is installed and running.")
    logger.info("Successfully initialized components")
except Exception as e:
    logger.error(f"Error initializing components: {e}")

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Trading Bot API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/analyze")
async def analyze_market(data: Dict[str, Any]):
    try:
        symbol = data.get("symbol", "EURUSD")
        timeframe = data.get("timeframe", "1h")
        
        # Get real market data from MT5
        market_data = mt5_connector.get_ohlcv(symbol, timeframe)
        if market_data is None:
            raise HTTPException(status_code=404, detail=f"No data found for {symbol}")
        
        # Perform analysis
        analysis_result = analytics.analyze_market(market_data.to_dict(orient="records"))
        return analysis_result
    except Exception as e:
        logger.error(f"Error in market analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ai-analysis")
async def ai_analysis(data: Dict[str, Any]):
    try:
        # Get market analysis from AI model
        prediction = model_manager.predict(
            data["data"],
            max_position_size=data.get("maxPositionSize", 1.0),
            stop_loss=data.get("stopLoss", 2.0),
            take_profit=data.get("takeProfit", 4.0)
        )
        
        if prediction:
            return {
                "signal": {
                    "type": prediction["action"],
                    "price": prediction["price"],
                    "size": prediction["size"],
                    "confidence": prediction["confidence"],
                    "stop_loss": prediction["stop_loss"],
                    "take_profit": prediction["take_profit"]
                }
            }
        return {"signal": None}
    except Exception as e:
        logger.error(f"Error in AI analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/backtest")
async def run_backtest(data: Dict[str, Any]):
    try:
        # Run backtest with provided parameters
        backtest_result = backtester.run_backtest(
            data["data"],
            strategy=data["strategy"],
            timeframe=data["timeframe"],
            risk_per_trade=data["riskPerTrade"],
            max_drawdown=data["maxDrawdown"]
        )
        
        return {
            "equity_curve": backtest_result["equity_curve"],
            "trades": backtest_result["trades"],
            "metrics": {
                "returns": backtest_result["total_return"],
                "sharpe_ratio": backtest_result["sharpe_ratio"],
                "max_drawdown": backtest_result["max_drawdown"],
                "win_rate": backtest_result["win_rate"]
            }
        }
    except Exception as e:
        logger.error(f"Error in backtesting: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/optimize")
async def optimize_strategy(data: Dict[str, Any]):
    try:
        # Run strategy optimization
        optimization_result = optimizer.optimize(
            data["data"],
            strategy=data["strategy"],
            timeframe=data["timeframe"],
            initial_params={
                "risk_per_trade": data["riskPerTrade"],
                "max_drawdown": data["maxDrawdown"]
            }
        )
        
        return {
            "optimal_params": optimization_result["parameters"],
            "performance": optimization_result["performance"]
        }
    except Exception as e:
        logger.error(f"Error in optimization: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/trade")
async def execute_trade(trade: Dict[str, Any]):
    try:
        # Execute the trade with safety checks
        if trade["type"] not in ["BUY", "SELL"]:
            raise ValueError("Invalid trade type")
        
        # Add trade execution logic here
        return {"status": "success", "trade_id": "12345"}
    except Exception as e:
        logger.error(f"Error executing trade: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/close-all")
async def close_all_trades():
    try:
        # Add logic to close all open trades
        return {"status": "success", "closed_trades": []}
    except Exception as e:
        logger.error(f"Error closing trades: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/symbols")
async def get_symbols():
    """Get available trading symbols"""
    try:
        symbols = mt5_connector.get_symbols()
        return {"symbols": symbols}
    except Exception as e:
        logger.error(f"Error getting symbols: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/market-data/{symbol}")
async def get_market_data(symbol: str, timeframe: str = "1h", num_candles: int = 1000):
    """Get market data for a symbol"""
    try:
        data = mt5_connector.get_ohlcv(symbol, timeframe, num_candles)
        if data is None:
            raise HTTPException(status_code=404, detail=f"No data found for {symbol}")
        return {"data": data.to_dict(orient="records")}
    except Exception as e:
        logger.error(f"Error getting market data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/price/{symbol}")
async def get_price(symbol: str):
    """Get current price for a symbol"""
    try:
        price = mt5_connector.get_current_price(symbol)
        if price is None:
            raise HTTPException(status_code=404, detail=f"No price found for {symbol}")
        return price
    except Exception as e:
        logger.error(f"Error getting price: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/account")
async def get_account_info():
    """Get account information"""
    try:
        info = mt5_connector.get_account_info()
        if info is None:
            raise HTTPException(status_code=404, detail="No account information available")
        return info
    except Exception as e:
        logger.error(f"Error getting account info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    logger.info("Starting FastAPI server...")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 