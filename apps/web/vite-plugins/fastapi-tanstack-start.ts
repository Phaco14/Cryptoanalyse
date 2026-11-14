import type { Plugin } from "vite";

/**
 * Sends the dev server's `/api` requests to the FastAPI app on `:3000`, so the web app can call
 * the API same-origin under `vite dev`. The generated client's paths already start with `/api`.
 */
const fastapiProxy: Plugin = {
  name: "fastapi-tanstack-start",
  config: () => ({
    server: {
      proxy: {
        "/api": {
          target: "http://localhost:3000",
          changeOrigin: true,
        },
      },
    },
  }),
  configureServer: (server) => {
    // Nitro owns the dev middleware chain under TanStack Start and serves any request that no
    // later middleware claims by route — it never reads Vite's `server.proxy` itself. Anchoring
    // `/api` in the stack makes Nitro's dev middleware defer, and Vite's proxy (configured above)
    // then forwards the request to the FastAPI app.
    server.middlewares.use("/api", (_req, _res, next) => next());
  },
};

export default fastapiProxy;
