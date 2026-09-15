/**
 * OMNIA production preview — durable same-origin front door.
 *
 * Serves frontend/build + proxies /api → backend.
 * Tuned for Cursor Port Forwarding (no keep-alive — avoids ERR_EMPTY_RESPONSE).
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

// Cursor Ports / flaky L7 forwards often reset keep-alive → ERR_EMPTY_RESPONSE.
app.use((_req, res, next) => {
  res.setHeader("Connection", "close");
  next();
});

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
    res.status(apiOk ? 200 : 503).json({
      ok: apiOk,
      preview: true,
      api_origin: API,
      api_ok: apiOk,
      api_status: code || null,
      error: err ? String(err.message || err) : null,
    });
  });
});

app.use(
  "/api",
  createProxyMiddleware({
    target: API,
    changeOrigin: true,
    ws: false,
    proxyTimeout: 120000,
    timeout: 120000,
    xfwd: true,
    logLevel: "warn",
    onProxyRes(proxyRes) {
      proxyRes.headers["connection"] = "close";
      delete proxyRes.headers["keep-alive"];
    },
    onError(err, _req, res) {
      console.error("[preview-proxy]", err.message);
      if (!res.headersSent) {
        res.writeHead(502, {
          "Content-Type": "application/json",
          Connection: "close",
        });
        res.end(
          JSON.stringify({
            detail: "api_gateway_unavailable",
            message: "Backend non raggiungibile. Riesegui: bash scripts/omnia-stack.sh ensure",
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
      res.setHeader("Connection", "close");
      if (filePath.endsWith("index.html")) {
        res.setHeader("Cache-Control", "no-cache");
      }
    },
  })
);

app.get("*", (_req, res) => {
  res.setHeader("Cache-Control", "no-cache");
  res.setHeader("Connection", "close");
  res.sendFile(path.join(BUILD, "index.html"), (err) => {
    if (err) {
      res.status(503).json({
        detail: "frontend_build_missing",
        message: "Esegui: cd frontend && REACT_APP_BACKEND_URL= yarn build",
      });
    }
  });
});

const server = http.createServer(app);
server.keepAliveTimeout = 1;
server.headersTimeout = 5000;
server.requestTimeout = 120000;
server.maxConnections = 100;

server.listen(PORT, "0.0.0.0", () => {
  console.log(`OMNIA preview listening on http://0.0.0.0:${PORT} → API ${API}`);
  console.log(`Health: http://127.0.0.1:${PORT}/healthz`);
});

process.on("SIGTERM", () => server.close(() => process.exit(0)));
process.on("SIGINT", () => server.close(() => process.exit(0)));
