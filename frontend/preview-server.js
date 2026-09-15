/**
 * OMNIA production preview — durable same-origin front door.
 *
 * Serves frontend/build + proxies /api → backend.
 * Use Cursor Ports on PREVIEW_PORT (default 43123). Do not depend on localtunnel.
 */
const path = require("path");
const http = require("http");
const express = require("express");
const { createProxyMiddleware } = require("http-proxy-middleware");

const PORT = Number(process.env.PREVIEW_PORT || 43123);
const API = process.env.API_ORIGIN || "http://127.0.0.1:43121";
const BUILD = path.join(__dirname, "build");

const app = express();
app.disable("x-powered-by");
app.set("trust proxy", 1);

function apiReachable(cb) {
  const url = new URL(API);
  const req = http.request(
    {
      hostname: url.hostname,
      port: url.port || 80,
      path: "/api/",
      method: "GET",
      timeout: 2000,
    },
    (res) => {
      res.resume();
      cb(null, res.statusCode);
    }
  );
  req.on("error", (err) => cb(err));
  req.on("timeout", () => {
    req.destroy();
    cb(new Error("timeout"));
  });
  req.end();
}

app.get("/healthz", (_req, res) => {
  apiReachable((err, code) => {
    const apiOk = !err && code && code < 500;
    const body = {
      ok: apiOk,
      preview: true,
      api_origin: API,
      api_ok: apiOk,
      api_status: code || null,
      error: err ? String(err.message || err) : null,
    };
    res.status(apiOk ? 200 : 503).json(body);
  });
});

app.use(
  "/api",
  createProxyMiddleware({
    target: API,
    changeOrigin: true,
    ws: true,
    proxyTimeout: 120000,
    timeout: 120000,
    xfwd: true,
    logLevel: "warn",
    onError(err, _req, res) {
      console.error("[preview-proxy]", err.message);
      if (!res.headersSent) {
        res.writeHead(502, { "Content-Type": "application/json" });
        res.end(
          JSON.stringify({
            detail: "api_gateway_unavailable",
            message:
              "Backend non raggiungibile dalla preview. Riesegui scripts/omnia-stack.sh ensure",
            error: String(err.message || err),
          })
        );
      }
    },
  })
);

app.use(
  express.static(BUILD, {
    index: false,
    maxAge: "5m",
    etag: true,
    setHeaders(res, filePath) {
      if (filePath.endsWith("index.html")) {
        res.setHeader("Cache-Control", "no-cache");
      }
    },
  })
);

app.get("*", (_req, res) => {
  res.setHeader("Cache-Control", "no-cache");
  res.sendFile(path.join(BUILD, "index.html"), (err) => {
    if (err) {
      res.status(503).json({
        detail: "frontend_build_missing",
        message: "Esegui: cd frontend && REACT_APP_BACKEND_URL= yarn build",
      });
    }
  });
});

const server = app.listen(PORT, "0.0.0.0", () => {
  console.log(`OMNIA preview listening on http://0.0.0.0:${PORT} → API ${API}`);
  console.log(`Health: http://127.0.0.1:${PORT}/healthz`);
  console.log("Access: Cursor Ports → omnia-preview (avoid localtunnel)");
});

server.keepAliveTimeout = 65000;
server.headersTimeout = 66000;

process.on("SIGTERM", () => server.close(() => process.exit(0)));
process.on("SIGINT", () => server.close(() => process.exit(0)));
