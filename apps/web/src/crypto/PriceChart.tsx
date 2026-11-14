/** A dependency-free SVG line chart: daily closes plus rolling MA50/MA200 series. */

import type { Close } from "./types";

interface PriceChartProps {
  series: Close[];
  height?: number;
}

const WIDTH = 720;
const HEIGHT = 260;
const PAD = { top: 12, right: 12, bottom: 22, left: 52 };

const rollingMean = (series: Close[], window: number): (number | null)[] =>
  series.map((_, index) => {
    if (index + 1 < window) return null;
    let sum = 0;
    for (let i = index + 1 - window; i <= index; i += 1) {
      const close = series[i];
      if (close === undefined) return null;
      sum += close.price;
    }
    return sum / window;
  });

const buildPath = (
  values: (number | null)[],
  toX: (index: number) => number,
  toY: (value: number) => number,
): string => {
  const parts: string[] = [];
  values.forEach((value, index) => {
    if (value === null) return;
    parts.push(`${parts.length === 0 ? "M" : "L"}${toX(index).toFixed(1)},${toY(value).toFixed(1)}`);
  });
  return parts.join(" ");
};

export const PriceChart = ({ series, height = HEIGHT }: PriceChartProps) => {
  if (series.length < 2) {
    return (
      <p className="text-sm text-slate-500">
        Historique insuffisant pour tracer un graphique (paire récemment cotée).
      </p>
    );
  }
  const prices = series.map((c) => c.price);
  const ma50 = rollingMean(series, 50);
  const ma200 = rollingMean(series, 200);
  const all: number[] = [...prices, ...ma50, ...ma200].filter(
    (v): v is number => v !== null,
  );
  const min = Math.min(...all);
  const max = Math.max(...all);
  const span = max - min || 1;
  const innerW = WIDTH - PAD.left - PAD.right;
  const innerH = height - PAD.top - PAD.bottom;
  const toX = (index: number) => PAD.left + (index / (series.length - 1)) * innerW;

  const toY = (value: number) => PAD.top + innerH - ((value - min) / span) * innerH;
  const ticks = [max, min + span * 0.5, min];
  const firstClose = series[0];
  const lastClose = series[series.length - 1];
  if (firstClose === undefined || lastClose === undefined) return null;

  return (
    <svg
      viewBox={`0 0 ${WIDTH} ${height}`}
      className="w-full"
      role="img"
      aria-label="Cours quotidien sur 365 jours avec moyennes mobiles 50 et 200 jours"
    >
      {ticks.map((tick) => (
        <g key={tick}>
          <line
            x1={PAD.left}
            x2={WIDTH - PAD.right}
            y1={toY(tick)}
            y2={toY(tick)}
            stroke="#e2e8f0"
            strokeWidth="1"
          />
          <text x={4} y={toY(tick) + 4} fontSize="10" fill="#64748b">
            {tick >= 1000 ? `${Math.round(tick / 100) / 10}k` : Math.round(tick * 100) / 100}
          </text>
        </g>
      ))}
      <path d={buildPath(ma200, toX, toY)} fill="none" stroke="#f59e0b" strokeWidth="1.6" />
      <path d={buildPath(ma50, toX, toY)} fill="none" stroke="#8b5cf6" strokeWidth="1.6" />
      <path d={buildPath(prices, toX, toY)} fill="none" stroke="#0f172a" strokeWidth="1.8" />
      <text x={PAD.left} y={height - 6} fontSize="10" fill="#64748b">
        {firstClose.date}
      </text>
      <text x={WIDTH - PAD.right} y={height - 6} fontSize="10" fill="#64748b" textAnchor="end">
        {lastClose.date}
      </text>
    </svg>
  );
};

export const chartLegend = [
  { label: "Cours", color: "#0f172a" },
  { label: "MA50", color: "#8b5cf6" },
  { label: "MA200", color: "#f59e0b" },
];
