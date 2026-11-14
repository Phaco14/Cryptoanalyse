import { useQuery } from "@tanstack/react-query";
import { createFileRoute, Link } from "@tanstack/react-router";

import { fetchPair } from "../crypto/api";
import { formatPrice, formatUsdCompact, trendBadge } from "../crypto/format";
import { chartLegend, PriceChart } from "../crypto/PriceChart";

type RouteContext = { symbol?: string };

const StatCard = ({
  label,
  value,
  hint,
}: {
  label: string;
  value: string;
  hint?: string;
}) => (
  <div className="rounded-xl border border-slate-200 bg-white p-4">
    <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
    <p className="mt-1 text-xl font-semibold text-slate-900">{value}</p>
    {hint ? <p className="mt-0.5 text-xs text-slate-500">{hint}</p> : null}
  </div>
);

const PairPage = () => {
  const { symbol } = Route.useParams() as RouteContext;
  const upper = (symbol ?? "").toUpperCase();
  const { isPending, isError, error, data } = useQuery({
    queryKey: ["crypto-pair", upper],
    queryFn: () => {
      return fetchPair(upper);
    },
  });

  if (isPending) {
    return (
      <main className="mx-auto max-w-4xl p-6">
        <p className="animate-pulse text-sm text-slate-500">Chargement…</p>
      </main>
    );
  }
  if (isError) {
    return (
      <main className="mx-auto max-w-4xl p-6">
        <p className="rounded-lg bg-rose-50 p-3 text-sm text-rose-700">{error.message}</p>
        <p className="mt-3">
          <Link to="/" className="text-slate-900 underline">
            ← Retour au tableau de bord
          </Link>
        </p>
      </main>
    );
  }

  const pair = data.analysis;
  const tvl = data.tvl;
  const badge = trendBadge(pair.trend);
  const retrRows = Object.entries(pair.fib.retracements);
  const extRows = Object.entries(pair.fib.extensions);

  return (
    <main className="mx-auto flex max-w-4xl flex-col gap-5 p-6">
      <header className="flex flex-wrap items-baseline justify-between gap-2">
        <div>
          <h1 className="text-2xl font-semibold">
            {pair.symbol}/USDC <span className="text-base font-normal text-slate-500">{pair.name}</span>
          </h1>
          <p className="text-sm text-slate-500">
            Données du {data.as_of} ·{" "}
            {data.source === "live" ? "sources publiques live" : "instantané du 14/11/2026"}
          </p>
        </div>
        <Link to="/" className="text-sm text-slate-900 underline">
          ← Tableau de bord
        </Link>
      </header>

      <section className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <StatCard label="Prix actuel" value={formatPrice(pair.price)} hint={`Cours en ${pair.quote}`} />
        <StatCard
          label="MA200"
          value={formatPrice(pair.ma200)}
          hint={pair.ma200 === null ? "Historique insuffisant" : "Moyenne 200 jours"}
        />
        <StatCard
          label="Tendance"
          value={badge.label}
          hint={pair.trend_label}
        />
        <StatCard
          label={tvl?.label ?? "TVL"}
          value={formatUsdCompact(tvl?.value ?? null)}
          hint={tvl?.source === "defillama" ? "DefiLlama" : "Instantané du 14/11/2026"}
        />
      </section>

      <section className="rounded-xl border border-slate-200 bg-white p-4">
        <div className="mb-2 flex flex-wrap gap-4">
          {chartLegend.map((entry) => (
            <span key={entry.label} className="flex items-center gap-1 text-xs text-slate-600">
              <span className="inline-block h-2 w-4 rounded" style={{ background: entry.color }} />
              {entry.label}
            </span>
          ))}
        </div>
        <PriceChart series={pair.series} />
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <div className="rounded-xl border border-slate-200 bg-white p-4">
          <h2 className="mb-2 font-semibold">Niveaux de Fibonacci</h2>
          <p className="mb-2 text-xs text-slate-500">
            Jambe {pair.leg === "down" ? "baissière" : "haussière"} : plus bas {formatPrice(pair.swing_low)} (
            {pair.swing_low_date}) → plus haut {formatPrice(pair.swing_high)} ({pair.swing_high_date})
          </p>
          <table className="w-full text-sm">
            <tbody>
              {retrRows.map(([level, value]) => (
                <tr key={level} className="border-b border-slate-100">
                  <td className="py-1 text-slate-500">Retracement {level}</td>
                  <td className="py-1 text-right font-mono">{formatPrice(value)}</td>
                </tr>
              ))}
              {extRows.map(([level, value]) => (
                <tr key={level} className="border-b border-slate-100">
                  <td className="py-1 text-slate-500">Extension {level}</td>
                  <td className="py-1 text-right font-mono">{formatPrice(value)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4">
          <h2 className="mb-2 font-semibold">Plan de trade</h2>
          {pair.plan ? (
            <table className="w-full text-sm">
              <tbody>
                <tr className="border-b border-slate-100">
                  <td className="py-1 text-slate-500">Zone d&apos;achat</td>
                  <td className="py-1 text-right font-mono">
                    {formatPrice(pair.plan.zone_low)} – {formatPrice(pair.plan.zone_high)}
                  </td>
                </tr>
                <tr className="border-b border-slate-100">
                  <td className="py-1 text-slate-500">Stop-loss</td>
                  <td className="py-1 text-right font-mono">{formatPrice(pair.plan.stop)}</td>
                </tr>
                <tr className="border-b border-slate-100">
                  <td className="py-1 text-slate-500">Cible 1</td>
                  <td className="py-1 text-right font-mono">{formatPrice(pair.plan.target1)}</td>
                </tr>
                <tr className="border-b border-slate-100">
                  <td className="py-1 text-slate-500">Cible 2</td>
                  <td className="py-1 text-right font-mono">
                    {pair.plan.target2 === null ? "—" : formatPrice(pair.plan.target2)}
                  </td>
                </tr>
                <tr className="border-b border-slate-100">
                  <td className="py-1 text-slate-500">Ratio rendement/risque</td>
                  <td
                    className={`py-1 text-right font-mono font-semibold ${
                      pair.plan.valid ? "text-emerald-700" : "text-amber-700"
                    }`}
                  >
                    {pair.plan.rr.toFixed(2)} {pair.plan.valid ? "✓" : "(< 2, invalide)"}
                  </td>
                </tr>
              </tbody>
            </table>
          ) : (
            <p className="text-sm text-slate-500">
              {pair.insufficient_history
                ? "Historique insuffisant pour construire un plan (paire récemment cotée)."
                : "Aucun plan validé : attendre un signal ou une zone de confluence."}
            </p>
          )}
          {pair.plan ? <p className="mt-2 text-xs text-slate-500">{pair.plan.note}</p> : null}
        </div>
      </section>

      <p className="text-xs text-slate-400">
        Analyse technique indicative — pas un conseil financier. Les niveaux sont calculés sur les
        clôtures quotidiennes des 365 derniers jours.
      </p>
    </main>
  );
};

export const Route = createFileRoute("/pair/$symbol")({
  component: PairPage,
});
