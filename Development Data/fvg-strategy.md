# Fair Value Gap (FVG) Trading Strategy

## Definition and Concept
A Fair Value Gap (FVG) is a price inefficiency that occurs when there is a gap between candles, specifically where the low of one candle is higher than the high of another, leaving an unfilled space in price action.

## Technical Requirements
- Minimum of three candles to confirm a fair value gap
- Gap must be larger than five pips
- Multiple timeframe analysis capability
- Clear chart with minimal indicators

## Entry Criteria
1. Gap Identification:
   - Locate gaps between candle bodies where price has moved rapidly
   - Gap must form during specific trading windows
   - Minimum gap size: 5 pips

2. Entry Points:
   - Use centerline of fair value gap for entries
   - Enter when price returns to test the gap
   - Must occur within trading windows:
     - London Trading Window (LTW): 8:00 AM to 9:00 AM (UK time)
     - New York Trading Window (NTW): 1:00 PM to 4:00 PM (UK time)

3. Confirmation Signals:
   - Align with liquidity sweeps
   - Look for draw-on liquidity
   - Verify with order blocks/supply and demand zones

## Exit Criteria
1. Target Setting:
   - Place targets before major zones
   - Use order blocks as target areas
   - Target daily highs/lows
   - Maintain 1:2 risk-to-reward ratio

2. Exit Rules:
   - Close trades by end of trading day
   - Exit if price shows strong rejection at gap
   - Take profits at liquidity pools

## Risk Management Parameters
1. Stop Loss Rules:
   - Minimum: 5 pips
   - Maximum: 20 pips
   - Place at high/low of first candle within gap
   - Account for spread in calculations

2. Position Sizing:
   - Risk fixed percentage per trade (1%)
   - Reduce size if experiencing losses
   - Calculate based on stop loss distance

## Market Conditions
1. Optimal Conditions:
   - Clear market structure
   - Defined trend direction
   - Low spread environment
   - Normal volatility levels

2. Avoid Trading:
   - During major news events
   - When gaps are too small (<5 pips)
   - In choppy or ranging markets
   - During high spread conditions

## Implementation Process
1. Pre-Trade Analysis:
   - Identify market structure
   - Mark key levels and zones
   - Note previous day high/low
   - Check economic calendar

2. Trade Execution:
   - Wait for price to approach FVG
   - Confirm with price action
   - Enter at centerline of gap
   - Set predetermined stops/targets

3. Trade Management:
   - Monitor price reaction at gap
   - Adjust stops to break-even when possible
   - Take partial profits at key levels
   - Close by end of day

## Key Levels and Indicators
1. Critical Zones:
   - Order blocks
   - Supply/demand zones
   - Daily highs/lows
   - Previous swing points

2. Time Analysis:
   - Respect trading windows
   - Monitor session transitions
   - Track time at key levels

## Technical Validation
1. Multiple Timeframe Confluence:
   - Check higher timeframe trend
   - Verify on lower timeframes
   - Confirm with price action

2. Additional Confirmation:
   - Liquidity sweeps
   - Order flow analysis
   - Market structure breaks

## Trading Scenarios
1. Bullish FVG:
   - Gap forms in uptrend
   - Price returns to test gap
   - Enter long at centerline
   - Target next significant resistance

2. Bearish FVG:
   - Gap forms in downtrend
   - Price returns to test gap
   - Enter short at centerline
   - Target next significant support

## Strategy Optimization
1. Data Collection:
   - Track all trades
   - Record gap sizes
   - Note market conditions
   - Document profit/loss

2. Analysis Parameters:
   - Win rate statistics
   - Average profit per trade
   - Maximum drawdown
   - Risk-reward ratios

3. Refinement Process:
   - Review failed trades
   - Identify optimal conditions
   - Adjust parameters based on data
   - Regular strategy review