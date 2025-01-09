import { useEffect, useRef, useState } from 'react';
import { createChart, IChartApi, ISeriesApi, ColorType } from 'lightweight-charts';
import type { MarketData, ChartSettings, TechnicalIndicator } from '@/types/trading';
import { tradingService } from '@/services/trading/tradingService';

interface PriceChartProps {
  symbol: string;
  userId: string;
  onCrosshairMove?: (price: number, time: number) => void;
  onTimeRangeChange?: (from: number, to: number) => void;
}

export default function PriceChart({ symbol, userId, onCrosshairMove, onTimeRangeChange }: PriceChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const [chart, setChart] = useState<IChartApi | null>(null);
  const [candlestickSeries, setCandlestickSeries] = useState<ISeriesApi<'Candlestick'> | null>(null);
  const [volumeSeries, setVolumeSeries] = useState<ISeriesApi<'Histogram'> | null>(null);
  const [settings, setSettings] = useState<ChartSettings | null>(null);
  const [indicators, setIndicators] = useState<Map<string, ISeriesApi<'Line'>>>(new Map());

  // Initialize chart
  useEffect(() => {
    if (!chartContainerRef.current) return;

    const chartInstance = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 600,
      layout: {
        background: { type: ColorType.Solid, color: '#ffffff' },
        textColor: '#333',
      },
      grid: {
        vertLines: { color: '#f0f0f0' },
        horzLines: { color: '#f0f0f0' },
      },
      crosshair: {
        mode: 0,
      },
      rightPriceScale: {
        borderColor: '#f0f0f0',
      },
      timeScale: {
        borderColor: '#f0f0f0',
        timeVisible: true,
        secondsVisible: false,
      },
    });

    const handleResize = () => {
      if (chartContainerRef.current) {
        chartInstance.applyOptions({ 
          width: chartContainerRef.current.clientWidth 
        });
      }
    };

    window.addEventListener('resize', handleResize);

    const candleSeries = chartInstance.addCandlestickSeries({
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderVisible: false,
      wickUpColor: '#26a69a',
      wickDownColor: '#ef5350',
    });

    const volumeHistogram = chartInstance.addHistogramSeries({
      color: '#26a69a',
      priceFormat: {
        type: 'volume',
      },
      priceScaleId: '',
      scaleMargins: {
        top: 0.8,
        bottom: 0,
      },
    });

    setChart(chartInstance);
    setCandlestickSeries(candleSeries);
    setVolumeSeries(volumeHistogram);

    // Cleanup
    return () => {
      window.removeEventListener('resize', handleResize);
      chartInstance.remove();
    };
  }, []);

  // Load chart settings
  useEffect(() => {
    const loadSettings = async () => {
      try {
        const chartSettings = await tradingService.getChartSettings(userId);
        setSettings(chartSettings);
      } catch (error) {
        console.error('Failed to load chart settings:', error);
      }
    };
    loadSettings();
  }, [userId]);

  // Apply settings
  useEffect(() => {
    if (!chart || !settings) return;

    chart.applyOptions({
      layout: {
        background: { 
          type: ColorType.Solid, 
          color: settings.theme === 'dark' ? '#131722' : '#ffffff' 
        },
        textColor: settings.theme === 'dark' ? '#d1d4dc' : '#333',
      },
      grid: {
        vertLines: { visible: settings.showGrid },
        horzLines: { visible: settings.showGrid },
      },
    });
  }, [chart, settings]);

  // Load market data
  useEffect(() => {
    const loadMarketData = async () => {
      if (!candlestickSeries || !volumeSeries || !settings) return;

      try {
        const data = await tradingService.getMarketData(symbol, settings.timeframe);
        
        const candleData = data.map(item => ({
          time: item.timestamp.getTime() / 1000,
          open: item.open,
          high: item.high,
          low: item.low,
          close: item.close,
        }));

        const volumeData = data.map(item => ({
          time: item.timestamp.getTime() / 1000,
          value: item.volume,
          color: item.close >= item.open ? '#26a69a' : '#ef5350',
        }));

        candlestickSeries.setData(candleData);
        if (settings.showVolume) {
          volumeSeries.setData(volumeData);
        }
      } catch (error) {
        console.error('Failed to load market data:', error);
      }
    };

    loadMarketData();
  }, [candlestickSeries, volumeSeries, symbol, settings]);

  // Setup event handlers
  useEffect(() => {
    if (!chart) return;

    chart.subscribeCrosshairMove(param => {
      if (param.time && param.point && onCrosshairMove) {
        const price = param.point.y;
        onCrosshairMove(price, param.time as number);
      }
    });

    chart.timeScale().subscribeVisibleTimeRangeChange(range => {
      if (range && onTimeRangeChange) {
        onTimeRangeChange(range.from as number, range.to as number);
      }
    });
  }, [chart, onCrosshairMove, onTimeRangeChange]);

  // Add technical indicators
  const addIndicator = async (indicator: TechnicalIndicator) => {
    if (!chart || !candlestickSeries) return;

    try {
      const series = chart.addLineSeries({
        color: indicator.color,
        lineWidth: 2,
        priceScaleId: 'right',
      });

      // Calculate indicator values (implement calculation logic based on indicator type)
      // This is a placeholder for demonstration
      const data = await calculateIndicator(indicator);
      series.setData(data);

      setIndicators(prev => new Map(prev.set(indicator.id, series)));
    } catch (error) {
      console.error(`Failed to add indicator ${indicator.name}:`, error);
    }
  };

  // Placeholder for indicator calculation
  const calculateIndicator = async (indicator: TechnicalIndicator) => {
    // Implement indicator calculation logic here
    return [];
  };

  return (
    <div className="w-full h-[600px] relative">
      <div ref={chartContainerRef} className="w-full h-full" />
      {/* Add indicator controls, timeframe selector, etc. here */}
    </div>
  );
} 