import { useEffect, useMemo, useRef, useState } from "react";
import * as echarts from "echarts";
import type { CandleRecord, TradingStyle } from "../types/market";

interface MarketChartProps {
  data: CandleRecord[];
  ticker: string;
  tradingStyle: TradingStyle;
}

export function MarketChart({ data, ticker, tradingStyle }: MarketChartProps) {
  const chartRef = useRef<HTMLDivElement | null>(null);
  const chartInstanceRef = useRef<echarts.ECharts | null>(null);
  const [indicators, setIndicators] = useState({
    emaFast: true,
    emaSlow: true,
    rsi: true,
    macd: true
  });

  const indicatorKeys = useMemo(() => {
    const fast = tradingStyle === "last_3_days" ? "ema_9" : "ema_20";
    const slow = tradingStyle === "last_3_days" ? "ema_20" : "ema_50";
    return { fast, slow };
  }, [tradingStyle]);

  useEffect(() => {
    const container = chartRef.current;
    if (!container || data.length === 0) {
      return;
    }

    let chart: echarts.ECharts | null = null;
    try {
      chart = echarts.getInstanceByDom(container) || echarts.init(container);
      chartInstanceRef.current = chart;
    } catch {
      return;
    }

    const dates: string[] = [];
    const candles: number[][] = [];
    const volumes: number[] = [];
    const rsi: (number | null)[] = [];
    const macd: (number | null)[] = [];
    const macdSignal: (number | null)[] = [];
    const emaFast: (number | null)[] = [];
    const emaSlow: (number | null)[] = [];

    for (const candle of data) {
      dates.push(new Date(candle.date).toLocaleString([], { month: "short", day: "numeric", hour: "2-digit" }));
      candles.push([candle.open, candle.close, candle.low, candle.high].map(Number));
      volumes.push(Number(candle.volume) || 0);
      rsi.push(typeof candle.rsi === "number" ? candle.rsi : null);
      macd.push(typeof candle.macd === "number" ? candle.macd : null);
      macdSignal.push(typeof candle.macd_signal === "number" ? candle.macd_signal : null);
      emaFast.push(toNullableNumber(candle[indicatorKeys.fast as keyof CandleRecord]));
      emaSlow.push(toNullableNumber(candle[indicatorKeys.slow as keyof CandleRecord]));
    }

    try {
      chart.setOption({
      backgroundColor: "transparent",
      animation: true,
      tooltip: {
        trigger: "axis",
        axisPointer: { type: "cross" },
        backgroundColor: "rgba(10, 16, 28, 0.92)",
        borderColor: "rgba(126, 231, 255, 0.25)",
        textStyle: { color: "#d8eef7" }
      },
      axisPointer: { link: [{ xAxisIndex: "all" }] },
      grid: [
        { left: 44, right: 20, top: 28, height: "48%" },
        { left: 44, right: 20, top: "62%", height: "12%" },
        { left: 44, right: 20, top: "79%", height: "12%" }
      ],
      xAxis: [
        { type: "category", data: dates, boundaryGap: false, axisLine: { lineStyle: { color: "#31445b" } }, axisLabel: { color: "#7890a4" } },
        { type: "category", data: dates, gridIndex: 1, boundaryGap: false, axisLabel: { show: false }, axisLine: { lineStyle: { color: "#31445b" } } },
        { type: "category", data: dates, gridIndex: 2, boundaryGap: false, axisLabel: { color: "#7890a4" }, axisLine: { lineStyle: { color: "#31445b" } } }
      ],
      yAxis: [
        { scale: true, axisLabel: { color: "#8ba1b6" }, splitLine: { lineStyle: { color: "rgba(76, 97, 121, 0.25)" } } },
        { scale: true, gridIndex: 1, axisLabel: { color: "#8ba1b6" }, splitLine: { lineStyle: { color: "rgba(76, 97, 121, 0.18)" } } },
        { scale: true, gridIndex: 2, axisLabel: { color: "#8ba1b6" }, splitLine: { lineStyle: { color: "rgba(76, 97, 121, 0.18)" } } }
      ],
      dataZoom: [
        { type: "inside", xAxisIndex: [0, 1, 2], start: 45, end: 100 },
        { show: true, xAxisIndex: [0, 1, 2], bottom: 6, height: 18, borderColor: "rgba(126, 231, 255, 0.18)", fillerColor: "rgba(126, 231, 255, 0.12)" }
      ],
      series: [
        {
          name: ticker,
          type: "candlestick",
          data: candles,
          itemStyle: {
            color: "#2df3a0",
            color0: "#ff5b72",
            borderColor: "#2df3a0",
            borderColor0: "#ff5b72"
          }
        },
        indicators.emaFast && {
          name: indicatorKeys.fast.toUpperCase(),
          type: "line",
          data: emaFast,
          smooth: true,
          symbol: "none",
          lineStyle: { color: "#7ee7ff", width: 2 }
        },
        indicators.emaSlow && {
          name: indicatorKeys.slow.toUpperCase(),
          type: "line",
          data: emaSlow,
          smooth: true,
          symbol: "none",
          lineStyle: { color: "#f7c948", width: 2 }
        },
        {
          name: "Volume",
          type: "bar",
          xAxisIndex: 1,
          yAxisIndex: 1,
          data: volumes,
          itemStyle: { color: "rgba(126, 231, 255, 0.25)" }
        },
        indicators.rsi && {
          name: "RSI",
          type: "line",
          xAxisIndex: 2,
          yAxisIndex: 2,
          data: rsi,
          symbol: "none",
          lineStyle: { color: "#b6f09c", width: 1.7 }
        },
        indicators.macd && {
          name: "MACD",
          type: "line",
          xAxisIndex: 2,
          yAxisIndex: 2,
          data: macd,
          symbol: "none",
          lineStyle: { color: "#9aa7ff", width: 1.6 }
        },
        indicators.macd && {
          name: "MACD Signal",
          type: "line",
          xAxisIndex: 2,
          yAxisIndex: 2,
          data: macdSignal,
          symbol: "none",
          lineStyle: { color: "#ffb86b", width: 1.4 }
        }
      ].filter(Boolean)
    });

    const handleResize = () => { try { chart?.resize(); } catch {} };
    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      try { chartInstanceRef.current?.dispose(); } catch {}
      chartInstanceRef.current = null;
    };
    } catch {
      // chart rendering failed; empty state is visible instead
    }
  }, [data, indicators, indicatorKeys, ticker]);

  return (
    <section className="terminal-card chart-card">
      <div className="card-header">
        <div>
          <p className="eyebrow">Market Evidence</p>
          <h2>{ticker} Institutional Chart</h2>
        </div>
        <div className="indicator-toggles">
          <Toggle label="EMA Fast" checked={indicators.emaFast} onChange={() => setIndicators((state) => ({ ...state, emaFast: !state.emaFast }))} />
          <Toggle label="EMA Slow" checked={indicators.emaSlow} onChange={() => setIndicators((state) => ({ ...state, emaSlow: !state.emaSlow }))} />
          <Toggle label="RSI" checked={indicators.rsi} onChange={() => setIndicators((state) => ({ ...state, rsi: !state.rsi }))} />
          <Toggle label="MACD" checked={indicators.macd} onChange={() => setIndicators((state) => ({ ...state, macd: !state.macd }))} />
        </div>
      </div>
      <div style={{ position: "relative" }}>
        <div className="chart-surface" ref={chartRef} />
        {!data.length && (
          <div className="chart-empty-state" style={{ position: "absolute", inset: 0 }}>
            <h3>Chart data awaiting backend execution</h3>
            <p>Run the workflow to render OHLCV candles and backend-computed EMA, RSI, and MACD overlays.</p>
          </div>
        )}
      </div>
    </section>
  );
}

function toNullableNumber(value: unknown) {
  return typeof value === "number" ? value : null;
}

interface ToggleProps {
  checked: boolean;
  label: string;
  onChange: () => void;
}

function Toggle({ checked, label, onChange }: ToggleProps) {
  return (
    <label className="toggle-pill">
      <input checked={checked} onChange={onChange} type="checkbox" />
      <span>{label}</span>
    </label>
  );
}
