import { afterEach, describe, expect, spyOn, test } from "bun:test";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import {
  RouterProvider,
  createMemoryHistory,
  createRootRoute,
  createRouter,
} from "@tanstack/react-router";
import type { RouteComponent } from "@tanstack/react-router";
import { cleanup, render, screen } from "@testing-library/react";
import type { ReactNode } from "react";

import { NotFound } from "./not-found";
import { RootScreensContext } from "./root-screens";
import type { RootScreens, RootTexts } from "./root-screens";
import { Route as IndexRoute } from "./routes/index";
import type { Analysis } from "./crypto/types";

/**
 * A source that answers in French whatever it is asked, as a capability would contribute; `asked`
 * records the locales it was asked for.
 */
const FRENCH: RootTexts = {
  lang: "fr",
  dir: "ltr",
  missingChunkTitle: "L’application a été mise à jour",
  missingChunk: "Cette page n’a pas pu se charger.",
  reload: "Recharger",
  errorTitle: "Une erreur est survenue",
  errorDescription: "Cette page a rencontré un problème inattendu.",
  retry: "Réessayer",
  errorDetails: "Détails",
  notFound: "Page introuvable",
  notFoundDescription: "Rien ne se trouve à cette adresse.",
  home: "Aller à l’accueil",
  starterEyebrow: "Pour commencer",
  starterHint: ({ file, directory }) => (
    <>
      Modifiez {file} ou ajoutez une route dans {directory}.
    </>
  ),
};

const french = (
  screens: Partial<RootScreens> = {}
): RootScreens & { asked: string[] } => {
  const asked: string[] = [];

  return {
    ...screens,
    asked,
    resolveLocale: () => "fr",
    texts: (locale) => {
      asked.push(locale);

      return FRENCH;
    },
  };
};

const home = (): RouteComponent => {
  const Home = IndexRoute.options.component;

  if (Home === undefined) {
    throw new Error("The index route has no component.");
  }

  return Home;
};

const renderRoot = (
  component: RouteComponent,
  source: RootScreens,
  context?: { locale: string }
) => {
  const router = createRouter({
    routeTree: createRootRoute({
      beforeLoad: () => context,
      component,
      notFoundComponent: NotFound,
    }),
    history: createMemoryHistory(),
  });

  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <RootScreensContext value={source}>{children}</RootScreensContext>
    </QueryClientProvider>
  );

  render(<RouterProvider router={router} />, { wrapper });
};

afterEach(() => {
  cleanup();
});

describe("the root screens", () => {
  test("the not-found page speaks the provided source in the root route's locale", async () => {
    const source = french();

    renderRoot(NotFound, source, { locale: "fr" });

    await screen.findByText("Page introuvable");
    expect(new Set(source.asked)).toEqual(new Set(["fr"]));
  });

  test("the plain not-found page links home", async () => {
    renderRoot(NotFound, french(), { locale: "fr" });

    const link = await screen.findByRole("link", { name: "Aller à l’accueil" });

    expect(link.getAttribute("href")).toBe("/");
    expect(screen.getByText("Rien ne se trouve à cette adresse.")).toBeTruthy();
  });

  test("the dashboard renders the tracked pairs from the analysis", async () => {
    const fetchCalls: string[] = [];
    globalThis.fetch = (async (input: RequestInfo | URL) => {
      fetchCalls.push(String(input));
      const body: Analysis = {
        as_of: "2026-11-14",
        source: "snapshot",
        pairs: [
          {
            symbol: "BTC",
            name: "Bitcoin",
            quote: "USDC",
            price: 68233,
            change_24h: -3.7,
            ma50: 78820,
            ma200: 69650,
            trend: "bearish",
            trend_label: "Baissière",
            swing_high: 99697,
            swing_high_date: "2025-11-13",
            swing_low: 58559,
            swing_low_date: "2026-06-30",
            leg: "down",
            fib: {
              retracements: { "0.236": 68268, "0.382": 74274 },
              extensions: { "1.272": 47370, "1.618": 33036 },
            },
            plan: null,
            series: [],
            insufficient_history: false,
          },
        ],
        tvl: { BTC: { value: 3604000000, label: "TVL DeFi (BTCFi)", source: "snapshot" } },
      };
      return new Response(JSON.stringify(body), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    }) as typeof fetch;

    renderRoot(home(), french(), { locale: "fr" });

    expect(await screen.findByRole("heading", { name: "Cryptoanalyse — Top 10 / USDC" })).toBeTruthy();
    expect(await screen.findByText("BTC/USDC")).toBeTruthy();
    expect(fetchCalls).toContain("/api/crypto");
  });

  test("with no locale on the root route, they ask for English and never resolve one", async () => {
    const source = french();
    const resolveLocale = spyOn(source, "resolveLocale");

    renderRoot(NotFound, source);

    await screen.findByText("Page introuvable");
    expect(new Set(source.asked)).toEqual(new Set(["en"]));
    expect(resolveLocale).not.toHaveBeenCalled();
  });

  test("a source's own screens replace the plain ones, given the words", async () => {
    const source = french({
      NotFound: ({ texts }) => <h1>{`404 · ${texts.notFound}`}</h1>,
    });

    renderRoot(NotFound, source, { locale: "fr" });
    await screen.findByRole("heading", { name: "404 · Page introuvable" });
  });
});
