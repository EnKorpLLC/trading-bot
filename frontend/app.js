// Global variables
const API_URL = 'http://localhost:8000';
let priceChart = null;
let activeStrategy = null;
let drawingMode = null;
let activeIndicators = new Set();
let drawings = [];
let selectedSymbol = 'EURUSD';
let availableSymbols = [];

// Initialize Chart.js price chart with advanced features
function initializePriceChart(data) {
    const ctx = document.getElementById('priceChart').getContext('2d');
    if (priceChart) {
        priceChart.destroy();
    }
    
    priceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.map(d => new Date(d.timestamp).toLocaleString()),
            datasets: [
                {
                    label: 'Price',
                    data: data.map(d => d.close || d.price),
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1,
                    fill: false
                },
                {
                    label: 'Volume',
                    data: data.map(d => d.volume),
                    borderColor: 'rgb(153, 102, 255)',
                    backgroundColor: 'rgba(153, 102, 255, 0.2)',
                    type: 'bar',
                    yAxisID: 'volume'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Time'
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Price'
                    }
                },
                volume: {
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Volume'
                    },
                    grid: {
                        drawOnChartArea: false
                    }
                }
            },
            plugins: {
                zoom: {
                    zoom: {
                        wheel: {
                            enabled: true
                        },
                        pinch: {
                            enabled: true
                        },
                        mode: 'xy'
                    },
                    pan: {
                        enabled: true,
                        mode: 'xy'
                    }
                },
                annotation: {
                    annotations: {}
                },
                legend: {
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed.y !== null) {
                                label += context.parsed.y.toFixed(2);
                            }
                            return label;
                        }
                    }
                }
            }
        }
    });

    // Add drawings and indicators
    updateDrawings();
    updateIndicators();
}

// Strategy selection
function selectStrategy(strategy) {
    activeStrategy = strategy;
    document.getElementById('activeStrategy').textContent = strategy.toUpperCase();
    document.querySelectorAll('.strategy-card').forEach(card => {
        card.classList.remove('active');
        if (card.querySelector('.card-title').textContent.toLowerCase().includes(strategy)) {
            card.classList.add('active');
        }
    });

    // Handle independent mode
    if (strategy === 'independent') {
        enableIndependentMode();
    } else {
        disableIndependentMode();
    }
    
    updateTimeframe(document.getElementById('defaultTimeframe').value);
    bootstrap.Modal.getInstance(document.getElementById('strategyModal')).hide();
}

// Independent mode functions
function enableIndependentMode() {
    // Enable AI trading with safety parameters
    const settings = loadSettings();
    const aiControls = document.createElement('div');
    aiControls.id = 'aiControls';
    aiControls.className = 'position-absolute top-0 start-50 translate-middle-x mt-2';
    aiControls.innerHTML = `
        <div class="card bg-light">
            <div class="card-body p-2">
                <h6 class="card-title mb-2">AI Trading Controls</h6>
                <div class="form-check form-switch mb-2">
                    <input class="form-check-input" type="checkbox" id="aiTrading">
                    <label class="form-check-label" for="aiTrading">Enable AI Trading</label>
                </div>
                <div class="mb-2">
                    <label class="form-label small">Max Position Size</label>
                    <input type="number" class="form-control form-control-sm" id="maxPositionSize" value="${settings.riskPerTrade}">
                </div>
                <div class="mb-2">
                    <label class="form-label small">Stop Loss (%)</label>
                    <input type="number" class="form-control form-control-sm" id="stopLoss" value="2">
                </div>
                <div>
                    <label class="form-label small">Take Profit (%)</label>
                    <input type="number" class="form-control form-control-sm" id="takeProfit" value="4">
                </div>
            </div>
        </div>
    `;
    document.querySelector('.chart-container').appendChild(aiControls);
    
    // Start AI monitoring when enabled
    document.getElementById('aiTrading').addEventListener('change', function(e) {
        if (e.target.checked) {
            startAITrading();
        } else {
            stopAITrading();
        }
    });
}

function disableIndependentMode() {
    const aiControls = document.getElementById('aiControls');
    if (aiControls) {
        stopAITrading();
        aiControls.remove();
    }
}

let aiTradingInterval = null;

async function startAITrading() {
    const maxPositionSize = parseFloat(document.getElementById('maxPositionSize').value);
    const stopLoss = parseFloat(document.getElementById('stopLoss').value);
    const takeProfit = parseFloat(document.getElementById('takeProfit').value);
    
    // Start AI trading loop
    aiTradingInterval = setInterval(async () => {
        const response = await fetchData('/ai-analysis', {
            method: 'POST',
            body: JSON.stringify({
                data: priceChart.data.datasets[0].data,
                maxPositionSize,
                stopLoss,
                takeProfit
            })
        });
        
        if (response && response.signal) {
            // Execute AI-generated trade
            const trade = {
                type: response.signal.type,
                price: response.signal.price,
                timestamp: new Date().toISOString(),
                size: response.signal.size,
                strategy: 'AI',
                status: 'OPEN'
            };
            
            await fetchData('/trade', {
                method: 'POST',
                body: JSON.stringify(trade)
            });
            
            updateTrades([trade, ...document.getElementById('trades').querySelectorAll('tr')]);
        }
    }, 5000); // Check every 5 seconds
}

function stopAITrading() {
    if (aiTradingInterval) {
        clearInterval(aiTradingInterval);
        aiTradingInterval = null;
    }
}

// Backtesting functionality
async function runBacktest() {
    const timeframe = document.getElementById('defaultTimeframe').value;
    const strategy = activeStrategy;
    const settings = loadSettings();
    
    const response = await fetchData('/backtest', {
        method: 'POST',
        body: JSON.stringify({
            strategy,
            timeframe,
            riskPerTrade: settings.riskPerTrade,
            maxDrawdown: settings.maxDrawdown,
            data: priceChart.data.datasets[0].data
        })
    });
    
    if (response) {
        // Update chart with backtest results
        const backtestOverlay = {
            label: 'Backtest',
            data: response.equity_curve,
            borderColor: 'rgb(75, 192, 192)',
            borderWidth: 2,
            fill: false,
            yAxisID: 'equity'
        };
        
        priceChart.data.datasets.push(backtestOverlay);
        priceChart.update();
        
        // Update metrics with backtest results
        updateMetrics(response.metrics);
        updateTrades(response.trades);
    }
}

// Optimization functionality
async function runOptimization() {
    const timeframe = document.getElementById('defaultTimeframe').value;
    const strategy = activeStrategy;
    const settings = loadSettings();
    
    const response = await fetchData('/optimize', {
        method: 'POST',
        body: JSON.stringify({
            strategy,
            timeframe,
            riskPerTrade: settings.riskPerTrade,
            maxDrawdown: settings.maxDrawdown,
            data: priceChart.data.datasets[0].data
        })
    });
    
    if (response) {
        // Update settings with optimized parameters
        document.getElementById('riskPerTrade').value = response.optimal_params.risk_per_trade;
        document.getElementById('maxDrawdown').value = response.optimal_params.max_drawdown;
        if (document.getElementById('stopLoss')) {
            document.getElementById('stopLoss').value = response.optimal_params.stop_loss;
        }
        if (document.getElementById('takeProfit')) {
            document.getElementById('takeProfit').value = response.optimal_params.take_profit;
        }
        
        // Save optimized settings
        saveSettings();
        
        // Run backtest with optimized parameters
        await runBacktest();
    }
}

// Add event listeners for backtest and optimize buttons
document.addEventListener('DOMContentLoaded', () => {
    const backtestLink = document.querySelector('a[href="#backtest"]');
    const optimizeLink = document.querySelector('a[href="#optimize"]');
    
    backtestLink.addEventListener('click', (e) => {
        e.preventDefault();
        runBacktest();
    });
    
    optimizeLink.addEventListener('click', (e) => {
        e.preventDefault();
        runOptimization();
    });
});

// Manual trading functions
async function placeTrade(type) {
    if (activeStrategy !== 'independent') return;
    
    const price = priceChart.data.datasets[0].data[priceChart.data.datasets[0].data.length - 1];
    const trade = {
        type: type,
        price: price,
        timestamp: new Date().toISOString(),
        size: 1.0,
        strategy: 'MANUAL',
        status: 'OPEN'
    };
    
    const response = await fetchData('/trade', {
        method: 'POST',
        body: JSON.stringify(trade)
    });
    
    if (response) {
        updateTrades([trade, ...document.getElementById('trades').querySelectorAll('tr')]);
    }
}

async function closeAllTrades() {
    if (activeStrategy !== 'independent') return;
    
    const response = await fetchData('/close-all', {
        method: 'POST'
    });
    
    if (response) {
        const trades = Array.from(document.getElementById('trades').querySelectorAll('tr'))
            .map(row => ({
                ...row,
                status: 'CLOSED'
            }));
        updateTrades(trades);
    }
}

// Drawing tools
function setDrawingMode(mode) {
    drawingMode = mode;
    document.querySelectorAll('.drawing-tools .btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
}

function clearDrawings() {
    drawings = [];
    updateDrawings();
}

function updateDrawings() {
    if (!priceChart) return;
    
    // Clear existing annotations
    priceChart.options.plugins.annotation.annotations = {};
    
    // Add all drawings
    drawings.forEach((drawing, index) => {
        const annotation = createAnnotation(drawing);
        if (annotation) {
            priceChart.options.plugins.annotation.annotations[`drawing${index}`] = annotation;
        }
    });
    
    priceChart.update();
}

function createAnnotation(drawing) {
    switch (drawing.type) {
        case 'line':
            return {
                type: 'line',
                scaleID: 'y',
                borderColor: 'rgb(255, 99, 132)',
                borderWidth: 2,
                label: {
                    enabled: true,
                    content: 'Trend Line'
                },
                ...drawing.config
            };
        case 'rectangle':
            return {
                type: 'box',
                backgroundColor: 'rgba(255, 99, 132, 0.25)',
                borderColor: 'rgb(255, 99, 132)',
                borderWidth: 2,
                label: {
                    enabled: true,
                    content: 'Zone'
                },
                ...drawing.config
            };
        // Add more drawing types as needed
    }
}

// Technical indicators
function toggleIndicator(indicator) {
    if (activeIndicators.has(indicator)) {
        activeIndicators.delete(indicator);
    } else {
        activeIndicators.add(indicator);
    }
    updateIndicators();
}

function updateIndicators() {
    if (!priceChart || !priceChart.data.datasets[0].data.length) return;
    
    // Remove all indicator datasets
    priceChart.data.datasets = priceChart.data.datasets.slice(0, 2); // Keep price and volume only
    
    // Add active indicators
    activeIndicators.forEach(indicator => {
        const indicatorData = calculateIndicator(indicator, priceChart.data.datasets[0].data);
        if (indicatorData) {
            priceChart.data.datasets.push(indicatorData);
        }
    });
    
    priceChart.update();
}

function calculateIndicator(indicator, prices) {
    switch (indicator) {
        case 'sma':
            return calculateSMA(prices);
        case 'ema':
            return calculateEMA(prices);
        case 'rsi':
            return calculateRSI(prices);
        case 'macd':
            return calculateMACD(prices);
    }
}

function calculateSMA(prices, period = 20) {
    if (!Array.isArray(prices) || prices.length < period) {
        console.error('Invalid input for SMA calculation');
        return null;
    }
    
    const sma = [];
    for (let i = 0; i < prices.length; i++) {
        if (i < period - 1) {
            sma.push(null);
            continue;
        }
        const sum = prices.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0);
        sma.push(sum / period);
    }
    
    // Verify SMA calculation
    const lastPrice = prices[prices.length - 1];
    const lastSMA = sma[sma.length - 1];
    console.log(`SMA Verification - Last Price: ${lastPrice}, Last SMA: ${lastSMA}`);
    
    return {
        label: `SMA(${period})`,
        data: sma,
        borderColor: 'rgb(255, 159, 64)',
        borderWidth: 1,
        fill: false
    };
}

function calculateEMA(prices, period = 20) {
    if (!Array.isArray(prices) || prices.length < period) {
        console.error('Invalid input for EMA calculation');
        return null;
    }
    
    const multiplier = 2 / (period + 1);
    const ema = [prices[0]];
    
    for (let i = 1; i < prices.length; i++) {
        ema.push((prices[i] - ema[i-1]) * multiplier + ema[i-1]);
    }
    
    // Verify EMA calculation
    const lastPrice = prices[prices.length - 1];
    const lastEMA = ema[ema.length - 1];
    console.log(`EMA Verification - Last Price: ${lastPrice}, Last EMA: ${lastEMA}`);
    
    return {
        label: `EMA(${period})`,
        data: ema,
        borderColor: 'rgb(153, 102, 255)',
        borderWidth: 1,
        fill: false
    };
}

function calculateRSI(prices, period = 14) {
    if (!Array.isArray(prices) || prices.length < period + 1) {
        console.error('Invalid input for RSI calculation');
        return null;
    }
    
    const changes = prices.map((price, i) => i === 0 ? 0 : price - prices[i-1]);
    const gains = changes.map(change => change > 0 ? change : 0);
    const losses = changes.map(change => change < 0 ? -change : 0);
    
    const avgGain = [];
    const avgLoss = [];
    let sumGain = gains.slice(0, period).reduce((a, b) => a + b, 0) / period;
    let sumLoss = losses.slice(0, period).reduce((a, b) => a + b, 0) / period;
    
    avgGain.push(sumGain);
    avgLoss.push(sumLoss);
    
    for (let i = period; i < prices.length; i++) {
        sumGain = ((avgGain[avgGain.length-1] * (period-1)) + gains[i]) / period;
        sumLoss = ((avgLoss[avgLoss.length-1] * (period-1)) + losses[i]) / period;
        avgGain.push(sumGain);
        avgLoss.push(sumLoss);
    }
    
    const rsi = avgGain.map((gain, i) => {
        const rs = gain / avgLoss[i];
        return 100 - (100 / (1 + rs));
    });
    
    // Verify RSI calculation
    const lastRSI = rsi[rsi.length - 1];
    console.log(`RSI Verification - Last RSI: ${lastRSI}`);
    if (lastRSI < 0 || lastRSI > 100) {
        console.error('Invalid RSI value detected');
    }
    
    return {
        label: 'RSI',
        data: rsi,
        borderColor: 'rgb(255, 99, 132)',
        borderWidth: 1,
        fill: false,
        yAxisID: 'rsi'
    };
}

function calculateMACD(prices, fastPeriod = 12, slowPeriod = 26, signalPeriod = 9) {
    if (!Array.isArray(prices) || prices.length < Math.max(fastPeriod, slowPeriod) + signalPeriod) {
        console.error('Invalid input for MACD calculation');
        return null;
    }
    
    const fastEMA = calculateEMA(prices, fastPeriod).data;
    const slowEMA = calculateEMA(prices, slowPeriod).data;
    const macdLine = fastEMA.map((fast, i) => fast - slowEMA[i]);
    const signalLine = calculateEMA(macdLine, signalPeriod).data;
    
    // Verify MACD calculation
    const lastMACD = macdLine[macdLine.length - 1];
    const lastSignal = signalLine[signalLine.length - 1];
    console.log(`MACD Verification - Last MACD: ${lastMACD}, Last Signal: ${lastSignal}`);
    
    return {
        label: 'MACD',
        data: macdLine,
        borderColor: 'rgb(75, 192, 192)',
        borderWidth: 1,
        fill: false,
        yAxisID: 'macd'
    };
}

// Update trading signals
function updateSignals(signals) {
    const signalsContainer = document.getElementById('signals');
    signalsContainer.innerHTML = signals.map(signal => `
        <div class="signal-item ${signal.type === 'BUY' ? 'signal-buy' : 'signal-sell'}">
            <span>${signal.type}</span>
            <span>${signal.price}</span>
            <small>${new Date(signal.timestamp).toLocaleString()}</small>
        </div>
    `).join('');
}

// Update performance metrics
function updateMetrics(metrics) {
    document.getElementById('totalReturn').textContent = `${(metrics.returns * 100).toFixed(2)}%`;
    document.getElementById('sharpeRatio').textContent = metrics.sharpe_ratio.toFixed(2);
    document.getElementById('maxDrawdown').textContent = `${(metrics.max_drawdown * 100).toFixed(2)}%`;
    document.getElementById('winRate').textContent = `${(metrics.win_rate * 100).toFixed(2)}%`;
}

// Update recent trades
function updateTrades(trades) {
    const tradesContainer = document.getElementById('trades');
    tradesContainer.innerHTML = trades.map(trade => `
        <tr>
            <td>${new Date(trade.timestamp).toLocaleString()}</td>
            <td>${trade.type}</td>
            <td>${trade.price.toFixed(2)}</td>
            <td>${trade.size || '-'}</td>
            <td class="${trade.pnl >= 0 ? 'trade-profit' : 'trade-loss'}">${trade.pnl.toFixed(2)}%</td>
            <td>${trade.strategy || activeStrategy || '-'}</td>
            <td><span class="badge bg-${trade.status === 'OPEN' ? 'warning' : 'success'}">${trade.status || 'CLOSED'}</span></td>
        </tr>
    `).join('');
}

// Function to fetch data from the API
async function fetchData(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_URL}${endpoint}`, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });
        return await response.json();
    } catch (error) {
        console.error('Error fetching data:', error);
        document.getElementById('status').textContent = 'Error connecting to API: ' + error.message;
        document.getElementById('status').className = 'alert alert-danger m-3';
        return null;
    }
}

// Update timeframe
async function updateTimeframe(timeframe) {
    const testData = generateTestData(timeframe);
    initializePriceChart(testData);
    await testAnalyzeEndpoint(testData);
}

// Generate test data based on timeframe
function generateTestData(timeframe) {
    const data = [];
    const now = new Date();
    const points = 50;
    let basePrice = 100;
    
    for (let i = 0; i < points; i++) {
        const timestamp = new Date(now);
        timestamp.setHours(now.getHours() - i * (timeframe === '1h' ? 1 : timeframe === '4h' ? 4 : 24));
        
        const volatility = 0.02;
        const change = (Math.random() - 0.5) * volatility * basePrice;
        basePrice += change;
        
        data.unshift({
            timestamp: timestamp.toISOString(),
            open: basePrice - Math.random(),
            high: basePrice + Math.random(),
            low: basePrice - Math.random(),
            close: basePrice,
            volume: Math.floor(Math.random() * 1000) + 500
        });
    }
    
    return data;
}

// Test functions with enhanced visualization
async function testAnalyzeEndpoint(testData = null) {
    if (!testData) {
        testData = generateTestData('1d');
    }
    
    const response = await fetchData('/analyze', {
        method: 'POST',
        body: JSON.stringify({ data: testData })
    });
    
    if (response) {
        updateSignals(response.signals || []);
        updateMetrics(response.metrics || {
            returns: 0,
            sharpe_ratio: 0,
            max_drawdown: 0,
            win_rate: 0
        });
        updateTrades(response.trades || []);
    }
}

// Settings management
function saveSettings() {
    const settings = {
        riskPerTrade: document.getElementById('riskPerTrade').value,
        maxDrawdown: document.getElementById('maxDrawdown').value,
        defaultTimeframe: document.getElementById('defaultTimeframe').value
    };
    localStorage.setItem('tradingBotSettings', JSON.stringify(settings));
    bootstrap.Modal.getInstance(document.getElementById('settingsModal')).hide();
    updateTimeframe(settings.defaultTimeframe);
}

// Load saved settings
function loadSettings() {
    const settings = JSON.parse(localStorage.getItem('tradingBotSettings')) || {
        riskPerTrade: 1,
        maxDrawdown: 10,
        defaultTimeframe: '1d'
    };
    document.getElementById('riskPerTrade').value = settings.riskPerTrade;
    document.getElementById('maxDrawdown').value = settings.maxDrawdown;
    document.getElementById('defaultTimeframe').value = settings.defaultTimeframe;
    return settings;
}

// Initialize the dashboard
async function initDashboard() {
    document.getElementById('status').textContent = 'Connecting to API...';
    
    const settings = loadSettings();
    
    try {
        // Get available symbols
        const symbolsResponse = await fetchData('/symbols');
        if (symbolsResponse && symbolsResponse.symbols) {
            availableSymbols = symbolsResponse.symbols.filter(s => 
                // Filter for major Forex pairs
                /^(EUR|USD|GBP|JPY|AUD|NZD|CAD|CHF)/.test(s) && 
                /(EUR|USD|GBP|JPY|AUD|NZD|CAD|CHF)$/.test(s)
            );
            
            // Populate symbol selector
            const symbolSelector = document.getElementById('symbolSelector');
            symbolSelector.innerHTML = availableSymbols.map(s => 
                `<option value="${s}" ${s === selectedSymbol ? 'selected' : ''}>${s}</option>`
            ).join('');
        }
        
        // Get account info
        const accountInfo = await fetchData('/account');
        if (accountInfo) {
            updateAccountInfo(accountInfo);
        }
        
        document.getElementById('status').textContent = 'Connected to MT5';
        document.getElementById('status').className = 'alert alert-success m-3';
        
        // Load initial data
        await updateMarketData();
        
        // Start real-time updates
        setInterval(updateMarketData, 1000);
    } catch (error) {
        document.getElementById('status').textContent = 'Error connecting to MT5: ' + error.message;
        document.getElementById('status').className = 'alert alert-danger m-3';
    }
}

// Update account information
function updateAccountInfo(info) {
    document.getElementById('accountBalance').textContent = `${info.balance.toFixed(2)} ${info.currency}`;
    document.getElementById('accountEquity').textContent = `${info.equity.toFixed(2)} ${info.currency}`;
    document.getElementById('accountMargin').textContent = `${info.margin.toFixed(2)} ${info.currency}`;
    document.getElementById('accountFreeMargin').textContent = `${info.free_margin.toFixed(2)} ${info.currency}`;
    document.getElementById('accountLeverage').textContent = `1:${info.leverage}`;
}

// Update market data
async function updateMarketData() {
    const timeframe = document.getElementById('defaultTimeframe').value;
    
    try {
        // Get OHLCV data
        const response = await fetchData(`/market-data/${selectedSymbol}?timeframe=${timeframe}`);
        if (response && response.data) {
            initializePriceChart(response.data);
            
            // Get current price
            const priceResponse = await fetchData(`/price/${selectedSymbol}`);
            if (priceResponse) {
                updateCurrentPrice(priceResponse);
            }
            
            // Update analysis if we have an active strategy
            if (activeStrategy) {
                const analysisResponse = await fetchData('/analyze', {
                    method: 'POST',
                    body: JSON.stringify({
                        symbol: selectedSymbol,
                        timeframe: timeframe,
                        data: response.data
                    })
                });
                
                if (analysisResponse) {
                    updateSignals(analysisResponse.signals || []);
                    updateMetrics(analysisResponse.metrics || {});
                    updateTrades(analysisResponse.trades || []);
                }
            }
        }
    } catch (error) {
        console.error('Error updating market data:', error);
    }
}

// Update current price display
function updateCurrentPrice(price) {
    const bidSpan = document.getElementById('bidPrice');
    const askSpan = document.getElementById('askPrice');
    const spreadSpan = document.getElementById('spread');
    
    if (bidSpan && askSpan && spreadSpan) {
        bidSpan.textContent = price.bid.toFixed(5);
        askSpan.textContent = price.ask.toFixed(5);
        spreadSpan.textContent = (price.spread * 10000).toFixed(1) + ' pips';
    }
}

// Calculate position size
function calculatePositionSize(stopLossPips) {
    const settings = loadSettings();
    const accountInfo = {
        balance: parseFloat(document.getElementById('accountBalance').textContent),
        currency: document.getElementById('accountBalance').textContent.split(' ')[1]
    };
    
    const riskAmount = accountInfo.balance * (settings.riskPerTrade / 100);
    const pipValue = 0.0001; // For most pairs (adjust for JPY pairs)
    const lotSize = riskAmount / (stopLossPips * pipValue * 100000);
    
    return Math.min(lotSize, settings.maxPositionSize || 1.0);
}

// Add event listeners
document.addEventListener('DOMContentLoaded', () => {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Symbol selector change
    const symbolSelector = document.getElementById('symbolSelector');
    if (symbolSelector) {
        symbolSelector.addEventListener('change', (e) => {
            selectedSymbol = e.target.value;
            updateMarketData();
        });
    }
    
    // Initialize dashboard
    initDashboard();
}); 