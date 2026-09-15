/**
 * Stable preview server for Cloudflare tunnel.
 * Serves production build + proxies /api → backend :43121
 * Avoids CRA webpack-dev-server incomplete responses through CF.
 */
const path = require("path");
const express = require("express");
const { createProxyMiddleware } = require("http-proxy-middleware");

const PORT = Number(process.env.PREVIEW_PORT || 43123);
const API = process.env.API_ORIGIN || "http://127.0.0.1:43121";
const BUILD = path.join(__dirname, "build");

const app = express();
app.disable("x-powered-by");

app.use(
  "/api",
  createProxyMiddleware({
    target: API,
    changeOrigin: true,
    logLevel: "warn",
  })
);

app.use(express.static(BUILD, { index: false, maxAge: "1h" }));

app.get("*", (_req, res) => {
  res.sendFile(path.join(BUILD, "index.html"));
});

app.listen(PORT, "0.0.0.0", () => {
  console.log(`OMNIA preview listening on http://0.0.0.0:${PORT} → API ${API}`);
});
