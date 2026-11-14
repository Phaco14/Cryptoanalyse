import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createFileRoute, Link } from "@tanstack/react-router";

import { fetchAnalysis, refreshAnalysis } from "../crypto/api";
import { formatPercent, formatPrice, formatUsdCompact, trendBadge } from "../crypto/format";
import type { PairAnalysis } from "../crypto/types";

const SourceBadge = ({ source }: { source: string }) => {
  const live = source === "live";
  return (
    <span
      className={`rounded-full px-2 py-0.5 text-xs font-medium ${
        live ? "bg-emerald-100 text-emerald-800" : "bg-slate-200 text-slate-700"
      }`}
    >
      {live ? "Données live" : source === "mixed" ? "Données mixtes" : "Instantané du 14/11/2026"}
    </span>
  );
};

const TrendCell = ({ analysis }: { analysis: PairAnalysis }) => {
  const badge = trendBadge(analysis.trend);
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${badge.classes}`}>
      {badge.label}
    </span>
  );
};

const Dashboard = () => {
  const queryClient = useQueryClient();
  const { isPending, isError, error, data } = useQuery({
    queryKey: ["crypto-analysis"],
    queryFn: fetchAnalysis,
  });
  const refresh = useMutation({
    mutationFn: refreshAnalysis,
    onSuccess: (fresh) => {
      queryClient.setQueryData(["crypto-analysis"], fresh);
    },
  });

  return (
    <main className="mx-auto flex min-h-full max-w-6xl flex-col gap-4 p-6">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Cryptoanalyse — Top 10 / USDC</h1>
          <p className="text-sm text-slate-500">
            Fibonacci · MA50/MA200 · zones d&apos;achat · TVL
            {data ? ` · données du ${data.as_of}` : ""}
          </p>
        </div>
        <div className="flex items-center gap-3">
          {data ? <SourceBadge source={data.source} /> : null}
          <button
            type="button"
            onClick={() => {
              refresh.mutate();
            }}
            disabled={refresh.isPending}
            className="rounded-lg bg-slate-900 px-3 py-1.5 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
          >
            {refresh.isPending ? "Recalcul…" : "Analyser maintenant"}
          </button>
        </div>
      </header>

      {isPending ? (
        <p className="animate-pulse text-sm text-slate-500">Chargement de l&apos;analyse…</p>
      ) : isError ? (
        <p className="rounded-lg bg-rose-50 p-3 text-sm text-rose-700">
          Impossible de charger l&apos;analyse : {error.message}
        </p>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-200">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
                <th className="px-3 py-2">Paire</th>
                <th className="px-3 py-2 text-right">Prix</th>
                <th className="px-3 py-2 text-right">24 h</th>
                <th className="px-3 py-2 text-right">MA50</th>
                <th className="px-3 py-2 text-right">MA200</th>
                <th className="px-3 py-2">Tendance</th>
                <th className="px-3 py-2 text-right">TVL / AUM</th>
                <th className="px-3 py-2 text-right">Plan R:R</th>
              </tr>
            </thead>
            <tbody>
              {data.pairs.map((pair) => {
                const tvl = data.tvl[pair.symbol];
                return (
                  <tr key={pair.symbol} className="border-b border-slate-100 hover:bg-slate-50">
                    <td className="px-3 py-2 font-medium">
                      <Link
                        to="/pair/$symbol"
                        params={{ symbol: pair.symbol }}
                        className="text-slate-900 underline-offset-2 hover:underline"
                      >
                        {pair.symbol}/USDC
                      </Link>
                    </td>
                    <td className="px-3 py-2 text-right font-mono">{formatPrice(pair.price)}</td>
                    <td
                      className={`px-3 py-2 text-right font-mono ${
                        (pair.change_24h ?? 0) >= 0 ? "text-emerald-700" : "text-rose-700"
                      }`}
                    >
                      {formatPercent(pair.change_24h)}
                    </td>
                    <td className="px-3 py-2 text-right font-mono text-slate-600">
                      {formatPrice(pair.ma50)}
                    </td>
                    <td className="px-3 py-2 text-right font-mono text-slate-600">
                      {formatPrice(pair.ma200)}
                    </td>
                    <td className="px-3 py-2">
                      <TrendCell analysis={pair} />
                    </td>
                    <td className="px-3 py-2 text-right font-mono text-slate-600">
                      {formatUsdCompact(tvl?.value ?? null)}
                    </td>
                    <td className="px-3 py-2 text-right font-mono">
                      {pair.plan ? (
                        <span className={pair.plan.valid ? "text-emerald-700" : "text-amber-700"}>
                          {pair.plan.rr.toFixed(1)}
                          {pair.plan.valid ? "" : " ( invalide )"}
                        </span>
                      ) : (
                        <span className="text-slate-400">—</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      <p className="text-xs text-slate-400">
        Analyse technique indicative — pas un conseil financier. Cliquez sur une paire pour le
        détail : graphique 365 jours, niveaux de Fibonacci, plan d&apos;achat/vente avec stop et
        cibles. Une analyse quotidienne est enregistrée automatiquement.
      </p>
    </main>
  );
};

export const Route = createFileRoute("/")({
  staticData: { landing: true },
  component: Dashboard,
});
