/** Shapes of the /api/crypto responses. */

export interface Close {
  date: string;
  price: number;
}

export interface FibLevels {
  retracements: Record<string, number>;
  extensions: Record<string, number>;
}

export interface TradePlan {
  zone_low: number;
  zone_high: number;
  stop: number;
  target1: number;
  target2: number | null;
  rr: number;
  valid: boolean;
  note: string;
}

export type Trend = "bullish" | "bearish" | "neutral" | "recovering" | "unknown";

export interface PairAnalysis {
  symbol: string;
  name: string;
  quote: string;
  price: number;
  change_24h: number | null;
  ma50: number | null;
  ma200: number | null;
  trend: Trend;
  trend_label: string;
  swing_high: number;
  swing_high_date: string;
  swing_low: number;
  swing_low_date: string;
  leg: "up" | "down";
  fib: FibLevels;
  plan: TradePlan | null;
  series: Close[];
  insufficient_history: boolean;
}

export interface TvlInfo {
  value: number | null;
  label: string;
  source: string;
}

export interface Analysis {
  as_of: string;
  source: "live" | "snapshot" | "mixed";
  restored_from_history?: boolean;
  pairs: PairAnalysis[];
  tvl: Record<string, TvlInfo>;
}

export interface PairDetail
  extends Omit<Analysis, "pairs" | "tvl" | "restored_from_history"> {
  tvl: TvlInfo | null;
  analysis: PairAnalysis;
}

export interface SnapshotMeta {
  date_key: string;
  created_at: string;
}

export interface History {
  snapshots: SnapshotMeta[];
}
