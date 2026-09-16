/**
 * Dev proxy + SSR shell for ImmobilCloud routes.
 *
 * Cursor / automated fetchers often hit CRA :43122 (empty #root CSR shell).
 * Production preview :43123 already SSRs; this mirrors that on the webpack
 * dev server so ANY port returns readable HTML without executing JS.
 */
const fs = require("fs");
const path = require("path");
const { createProxyMiddleware } = require("http-proxy-middleware");

const API = "http://127.0.0.1:43121";

function escapeHtml(s) {
  return String(s || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function publicOrigin(req) {
  const xfProto = (req.headers["x-forwarded-proto"] || "").split(",")[0].trim();
  const proto = xfProto || (req.secure ? "https" : "http");
  const host =
    (req.headers["x-forwarded-host"] || "").split(",")[0].trim() ||
    req.headers.host ||
    "127.0.0.1:43122";
  return `${proto}://${host}`;
}

function isCloudPath(urlPath) {
  const p = (urlPath || "").split("?")[0].toLowerCase();
  if (p === "/" || p === "") return true;
  if (/^\/(it|en|es)\/?$/.test(p)) return true;
  if (/^\/(it|en|es)\/cloud(\/|$)/.test(p)) return true;
  if (p.startsWith("/cloud")) return true;
  return false;
}

function ssrHtml(req) {
  const origin = publicOrigin(req);
  const title = "ImmobilCloud — La casa giusta, senza farsi raccontare storie";
  const description =
    "Cerca immobili in Italia. Scout ti dice se l'annuncio è completo, se il prezzo ha senso e cosa chiedere — prima della visita.";
  const image = `${origin}/cloud/hero.jpg`;
  const url = `${origin}${req.originalUrl || req.url || "/it/cloud"}`;

  // Keep webpack client so the interactive app still boots after SSR paint.
  return `<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>${escapeHtml(title)}</title>
  <meta name="description" content="${escapeHtml(description)}" />
  <link rel="canonical" href="${escapeHtml(url)}" />
  <link rel="icon" type="image/png" href="/favicon.png" />
  <meta property="og:type" content="website" />
  <meta property="og:site_name" content="ImmobilCloud" />
  <meta property="og:title" content="${escapeHtml(title)}" />
  <meta property="og:description" content="${escapeHtml(description)}" />
  <meta property="og:url" content="${escapeHtml(url)}" />
  <meta property="og:image" content="${escapeHtml(image)}" />
  <meta name="theme-color" content="#0B1E3F" />
</head>
<body>
  <!-- SSR_MARKER casa giusta ImmobilCloud -->
  <div id="root">
    <div id="omnia-ssr-shell" data-omnia-ssr="1" style="min-height:70vh;background:#0B1E3F;color:#fff;font-family:Georgia,serif">
      <div style="max-width:720px;margin:0 auto;padding:48px 24px">
        <p style="letter-spacing:.28em;text-transform:uppercase;font-size:11px;color:#C19A6B;font-family:system-ui,sans-serif">ImmobilCloud™</p>
        <h1 style="font-weight:400;font-size:2.2rem;line-height:1.15">La casa giusta, senza farsi raccontare storie.</h1>
        <p style="font-family:system-ui,sans-serif;color:rgba(255,255,255,.82)">${escapeHtml(description)}</p>
        <p style="font-family:system-ui,sans-serif">
          <a href="${escapeHtml(origin)}/it/cloud" style="color:#E8D5B5">Apri ImmobilCloud</a> ·
          <a href="${escapeHtml(origin)}/it/cloud/search" style="color:#E8D5B5">Cerca</a> ·
          <a href="${escapeHtml(origin)}/it/cloud/valutatore" style="color:#E8D5B5">Valuta</a>
        </p>
      </div>
    </div>
  </div>
  <script src="/static/js/bundle.js"></script>
  <script src="/static/js/vendors~main.chunk.js"></script>
  <script src="/static/js/main.chunk.js"></script>
</body>
</html>`;
}

module.exports = function setupProxy(app) {
  // BEFORE webpack HTML fallback — unconditional SSR (no User-Agent gate).
  app.get("/ssr-check", (_req, res) => {
    res.setHeader("Cache-Control", "no-store");
    res.type("text/plain").send("SSR_OK casa giusta ImmobilCloud\n");
  });

  app.use((req, res, next) => {
    if (req.method !== "GET" && req.method !== "HEAD") return next();
    const accept = req.headers.accept || "";
    const looksHtml =
      !accept ||
      accept.includes("text/html") ||
      accept.includes("*/*") ||
      accept.includes("application/xhtml");
    if (!looksHtml) return next();
    if (req.url.startsWith("/static/") || req.url.startsWith("/api/") || req.url.startsWith("/cloud/")) {
      // /cloud/*.jpg assets — only skip if clearly a static file
      if (/\.(js|css|map|png|jpe?g|webp|svg|ico|json|txt|woff2?)(\?|$)/i.test(req.url)) {
        return next();
      }
    }
    if (!isCloudPath(req.path || req.url)) return next();

    res.setHeader("Cache-Control", "no-store");
    res.setHeader("X-Omnia-Prerender", "ssr-always");
    res.setHeader("Content-Type", "text/html; charset=utf-8");
    return res.status(200).send(ssrHtml(req));
  });

  app.use(
    "/api",
    createProxyMiddleware({
      target: API,
      changeOrigin: true,
      ws: true,
      logLevel: "warn",
    })
  );
};
