/** French formatters for prices, TVL and percentages. */

const priceFormatter = (min: number, max: number, decimals: number) =>
  new Intl.NumberFormat("fr-FR", {
    minimumFractionDigits: min === max ? decimals : min,
    maximumFractionDigits: decimals,
  });

export const formatPrice = (value: number | null | undefined): string => {
  if (value === null || value === undefined) return "—";
  const abs = Math.abs(value);
  const decimals = abs >= 1000 ? 0 : abs >= 10 ? 2 : abs >= 1 ? 3 : 5;
  return `$${priceFormatter(0, 0, decimals).format(value)}`;
};

export const formatPercent = (value: number | null | undefined): string => {
  if (value === null || value === undefined) return "—";
  const formatted = new Intl.NumberFormat("fr-FR", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  }).format(value);
  return `${value > 0 ? "+" : ""}${formatted} %`;
};

export const formatUsdCompact = (value: number | null | undefined): string => {
  if (value === null || value === undefined) return "—";
  const abs = Math.abs(value);
  if (abs >= 1e9) return `$${(value / 1e9).toLocaleString("fr-FR", { maximumFractionDigits: 2 })} Md`;
  if (abs >= 1e6) return `$${(value / 1e6).toLocaleString("fr-FR", { maximumFractionDigits: 1 })} M`;
  if (abs >= 1e3) return `$${(value / 1e3).toLocaleString("fr-FR", { maximumFractionDigits: 1 })} k`;
  return `$${value.toLocaleString("fr-FR", { maximumFractionDigits: 2 })}`;
};

export const trendBadge = (trend: string): { label: string; classes: string } => {
  switch (trend) {
    case "bullish":
      return { label: "Haussière", classes: "bg-emerald-100 text-emerald-800" };
    case "recovering":
      return { label: "Retournement", classes: "bg-teal-100 text-teal-800" };
    case "bearish":
      return { label: "Baissière", classes: "bg-rose-100 text-rose-800" };
    case "neutral":
      return { label: "Neutre", classes: "bg-amber-100 text-amber-800" };
    default:
      return { label: "n/d", classes: "bg-slate-100 text-slate-600" };
  }
};
