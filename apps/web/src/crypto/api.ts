/** Typed fetchers for the crypto API. The base URL is same-origin: the gateway routes /api. */

import type { Analysis, History, PairDetail } from "./types";

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(path, { headers: { Accept: "application/json" } });
  if (!response.ok) {
    throw new Error(`API ${path} a répondu ${response.status}`);
  }
  return (await response.json()) as T;
}

export const fetchAnalysis = (): Promise<Analysis> => getJson<Analysis>("/api/crypto");

export const refreshAnalysis = async (): Promise<Analysis> => {
  const response = await fetch("/api/crypto/refresh", { method: "POST" });
  if (!response.ok) {
    throw new Error(`Le recalcul a échoué (${response.status})`);
  }
  return (await response.json()) as Analysis;
};

export const fetchPair = (symbol: string): Promise<PairDetail> =>
  getJson<PairDetail>(`/api/crypto/pairs/${symbol}`);

export const fetchHistory = (): Promise<History> => getJson<History>("/api/crypto/history?limit=60");
