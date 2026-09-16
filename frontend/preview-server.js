/**
 * OMNIA production preview — durable same-origin front door.
 *
 * Serves frontend/build + proxies /api → backend.
 * Bot / unfurl clients get a static HTML snapshot (CSR apps otherwise look empty).
 * Tuned for Cursor Port Forwarding (no keep-alive — avoids ERR_EMPTY_RESPONSE).
 */
const path = require("path");
const fs = require("fs");
const http = require("http");
const express = require("express");
const { createProxyMiddleware } = require("http-proxy-middleware");

const PORT = Number(process.env.PREVIEW_PORT || 43123);
const API = process.env.API_ORIGIN || "http://127.0.0.1:43121";
const BUILD = path.join(__dirname, "build");

const BOT_UA =
  /bot|crawler|spider|slurp|facebookexternalhit|facebot|twitterbot|linkedinbot|whatsapp|telegram|discordbot|slackbot|pinterest|embedly|quora link preview|outbrain|vkshare|w3c_validator|google-inspectiontool|bingpreview|preview|semrush|ahrefs|mj12|dotbot|bytespider|ia_archiver|curl\/|wget\/|python-requests|httpclient|scrapy/i;

const app = express();
app.disable("x-powered-by");
app.set("trust proxy", 1);

app.use((_req, res, next) => {
  res.setHeader("Connection", "close");
  next();
});

function publicOrigin(req) {
  const xfProto = (req.headers["x-forwarded-proto"] || "").split(",")[0].trim();
  const proto = xfProto || (req.secure ? "https" : "http");
  const host =
    (req.headers["x-forwarded-host"] || "").split(",")[0].trim() ||
    req.headers.host ||
    `127.0.0.1:${PORT}`;
  return `${proto}://${host}`;
}

function isBot(req) {
  const ua = req.headers["user-agent"] || "";
  if (!ua) return true;
  if (BOT_UA.test(ua)) return true;
  // Link-preview fetchers often send empty Accept preferring HTML only
  const accept = req.headers.accept || "";
  if (req.query && (req.query.prerender === "1" || req.query._escaped_fragment_ !== undefined)) {
    return true;
  }
  if (accept.includes("text/html") && !accept.includes("*/*") && /facebook|whatsapp|slack/i.test(ua)) {
    return true;
  }
  return false;
}

function escapeHtml(s) {
  return String(s || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function cloudSnapshotHtml(req) {
  const origin = publicOrigin(req);
  const pathName = (req.path || "/").replace(/\/+$/, "") || "/";
  const title = "ImmobilCloud — La casa giusta, senza farsi raccontare storie";
  const description =
    "Cerca immobili in Italia. Scout ti dice se l'annuncio è completo, se il prezzo ha senso e cosa chiedere — prima della visita.";
  const image = `${origin}/cloud/hero.jpg`;
  const url = `${origin}${req.originalUrl || pathName}`;

  return `<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>${escapeHtml(title)}</title>
  <meta name="description" content="${escapeHtml(description)}" />
  <meta name="robots" content="index, follow" />
  <link rel="canonical" href="${escapeHtml(url)}" />
  <meta property="og:type" content="website" />
  <meta property="og:site_name" content="ImmobilCloud" />
  <meta property="og:title" content="${escapeHtml(title)}" />
  <meta property="og:description" content="${escapeHtml(description)}" />
  <meta property="og:url" content="${escapeHtml(url)}" />
  <meta property="og:image" content="${escapeHtml(image)}" />
  <meta property="og:image:width" content="1200" />
  <meta property="og:image:height" content="630" />
  <meta property="og:locale" content="it_IT" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="${escapeHtml(title)}" />
  <meta name="twitter:description" content="${escapeHtml(description)}" />
  <meta name="twitter:image" content="${escapeHtml(image)}" />
  <meta name="theme-color" content="#0B1E3F" />
  <style>
    body{margin:0;font-family:Georgia,'Fraunces',serif;background:#0B1E3F;color:#fff}
    .wrap{max-width:720px;margin:0 auto;padding:48px 24px}
    .eyebrow{letter-spacing:.28em;text-transform:uppercase;font-size:11px;color:#C19A6B;font-family:system-ui,sans-serif}
    h1{font-weight:400;font-size:2.2rem;line-height:1.15;margin:12px 0 16px}
    p{font-family:system-ui,sans-serif;color:rgba(255,255,255,.82);line-height:1.5}
    a{color:#E8D5B5}
    .cta{display:inline-block;margin-top:20px;padding:12px 20px;background:#C19A6B;color:#fff;text-decoration:none;border-radius:8px;font-family:system-ui,sans-serif;font-size:14px}
    .note{margin-top:28px;font-size:12px;color:rgba(255,255,255,.45);font-family:system-ui,sans-serif}
    img.hero{width:100%;max-height:280px;object-fit:cover;border-radius:12px;margin:24px 0}
  </style>
</head>
<body>
  <div class="wrap">
    <p class="eyebrow">ImmobilCloud™</p>
    <h1>La casa giusta, senza farsi raccontare storie.</h1>
    <p>${escapeHtml(description)}</p>
    <img class="hero" src="${escapeHtml(image)}" alt="ImmobilCloud" />
    <p>
      <a href="${escapeHtml(origin)}/it/cloud">Apri ImmobilCloud</a> ·
      <a href="${escapeHtml(origin)}/it/cloud/search">Cerca</a> ·
      <a href="${escapeHtml(origin)}/it/cloud/valutatore">Valuta</a> ·
      <a href="${escapeHtml(origin)}/it/cloud/register?intent=sell">Vendi</a>
    </p>
    <a class="cta" href="${escapeHtml(origin)}/it/cloud">Entra nel portale</a>
    <p class="note">Anteprima server-side per crawler e anteprime link. L’app interattiva richiede JavaScript nel browser.</p>
  </div>
</body>
</html>`;
}

function shouldServeCloudSnapshot(req) {
  const p = (req.path || "").toLowerCase();
  if (p === "/" || p === "") return true;
  if (/^\/(it|en|es)\/?$/.test(p)) return true;
  if (/^\/(it|en|es)\/cloud(\/|$)/.test(p)) return true;
  if (p.startsWith("/cloud")) return true;
  return false;
}

function cloudRootInnerHtml(origin) {
  const description =
    "Cerca immobili in Italia. Scout ti dice se l'annuncio è completo, se il prezzo ha senso e cosa chiedere — prima della visita.";
  return `
  <div id="omnia-ssr-shell" data-omnia-ssr="1" style="min-height:70vh;background:#0B1E3F;color:#fff;font-family:Georgia,'Fraunces',serif">
    <div style="max-width:720px;margin:0 auto;padding:48px 24px">
      <p style="letter-spacing:.28em;text-transform:uppercase;font-size:11px;color:#C19A6B;font-family:system-ui,sans-serif">ImmobilCloud™</p>
      <h1 style="font-weight:400;font-size:2.2rem;line-height:1.15;margin:12px 0 16px">La casa giusta, senza farsi raccontare storie.</h1>
      <p style="font-family:system-ui,sans-serif;color:rgba(255,255,255,.82);line-height:1.5">${escapeHtml(description)}</p>
      <img src="${escapeHtml(origin)}/cloud/hero.jpg" alt="ImmobilCloud" width="1200" height="630" style="width:100%;max-height:280px;object-fit:cover;border-radius:12px;margin:24px 0" />
      <p style="font-family:system-ui,sans-serif">
        <a href="${escapeHtml(origin)}/it/cloud" style="color:#E8D5B5">Apri ImmobilCloud</a> ·
        <a href="${escapeHtml(origin)}/it/cloud/search" style="color:#E8D5B5">Cerca</a> ·
        <a href="${escapeHtml(origin)}/it/cloud/valutatore" style="color:#E8D5B5">Valuta</a> ·
        <a href="${escapeHtml(origin)}/it/cloud/register?intent=sell" style="color:#E8D5B5">Vendi</a>
      </p>
      <p style="margin-top:20px;font-family:system-ui,sans-serif;font-size:13px;color:rgba(255,255,255,.5)">Scout · Valutatore · Mutui · Annunci in Italia</p>
    </div>
  </div>`;
}

function rewriteSpaHtml(html, req) {
  const origin = publicOrigin(req);
  const url = `${origin}${req.originalUrl || req.path || "/"}`;
  const title = "ImmobilCloud — La casa giusta, senza farsi raccontare storie";
  const description =
    "Cerca immobili in Italia. Scout ti dice se l'annuncio è completo, se il prezzo ha senso e cosa chiedere — prima della visita.";
  const image = `${origin}/cloud/hero.jpg`;

  let out = html;
  const replacements = [
    [/<title>[^<]*<\/title>/i, `<title>${escapeHtml(title)}</title>`],
    [/<meta name="description" content="[^"]*"\s*\/?>/i, `<meta name="description" content="${escapeHtml(description)}" />`],
    [/<meta property="og:title" content="[^"]*"\s*\/?>/i, `<meta property="og:title" content="${escapeHtml(title)}" />`],
    [/<meta property="og:description" content="[^"]*"\s*\/?>/i, `<meta property="og:description" content="${escapeHtml(description)}" />`],
    [/<meta property="og:url" content="[^"]*"\s*\/?>/i, `<meta property="og:url" content="${escapeHtml(url)}" />`],
    [/<meta property="og:image" content="[^"]*"\s*\/?>/i, `<meta property="og:image" content="${escapeHtml(image)}" />`],
    [/<meta property="og:site_name" content="[^"]*"\s*\/?>/i, `<meta property="og:site_name" content="ImmobilCloud" />`],
    [/<meta name="twitter:title" content="[^"]*"\s*\/?>/i, `<meta name="twitter:title" content="${escapeHtml(title)}" />`],
    [/<meta name="twitter:description" content="[^"]*"\s*\/?>/i, `<meta name="twitter:description" content="${escapeHtml(description)}" />`],
    [/<meta name="twitter:image" content="[^"]*"\s*\/?>/i, `<meta name="twitter:image" content="${escapeHtml(image)}" />`],
    [/<link rel="canonical" href="[^"]*"\s*\/?>/i, `<link rel="canonical" href="${escapeHtml(url)}" />`],
  ];
  for (const [re, rep] of replacements) {
    if (re.test(out)) out = out.replace(re, rep);
  }

  // Critical: populate #root in the static HTML so non-JS fetchers never see an empty body.
  // React replaces this on client mount.
  const rootFilled = `<div id="root">${cloudRootInnerHtml(origin)}</div>`;
  if (/<div id="root"><\/div>/i.test(out)) {
    out = out.replace(/<div id="root"><\/div>/i, rootFilled);
  } else if (/<div id="root">\s*<\/div>/i.test(out)) {
    out = out.replace(/<div id="root">\s*<\/div>/i, rootFilled);
  }

  out = out.replace(
    /<noscript>[\s\S]*?<\/noscript>/i,
    `<noscript>${cloudRootInnerHtml(origin)}</noscript>`
  );
  return out;
}

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

app.get("*", (req, res) => {
  res.setHeader("Cache-Control", "no-cache");
  res.setHeader("Connection", "close");

  const wantSnapshot =
    shouldServeCloudSnapshot(req) &&
    (isBot(req) || req.query.prerender === "1" || req.query.ssr === "1");

  // Dedicated prerender document for bots / explicit ?prerender=1
  if (wantSnapshot) {
    res.setHeader("Content-Type", "text/html; charset=utf-8");
    res.setHeader("X-Omnia-Prerender", "cloud-snapshot");
    return res.status(200).send(cloudSnapshotHtml(req));
  }

  const indexPath = path.join(BUILD, "index.html");
  fs.readFile(indexPath, "utf8", (err, html) => {
    if (err || !html) {
      return res.status(503).json({
        detail: "frontend_build_missing",
        message: "Esegui: cd frontend && REACT_APP_BACKEND_URL= yarn build",
      });
    }
    // Cloud routes: SPA + pre-filled #root (readable without executing JS)
    const out = shouldServeCloudSnapshot(req) ? rewriteSpaHtml(html, req) : html;
    res.setHeader("Content-Type", "text/html; charset=utf-8");
    if (shouldServeCloudSnapshot(req)) {
      res.setHeader("X-Omnia-Prerender", "root-shell");
    }
    res.status(200).send(out);
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
