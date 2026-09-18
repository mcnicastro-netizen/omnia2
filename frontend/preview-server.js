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
// Temporary QC gate: auto-session on /app/* so reviewers can open gestionale without login.
// Disable with CRM_PUBLIC_PREVIEW=0 after the review.
const CRM_PUBLIC_PREVIEW = String(process.env.CRM_PUBLIC_PREVIEW || "0") === "1";
const QC_SHOTS_DIRS = [
  "/opt/cursor/artifacts/screenshots",
  "/tmp/omnia-stack/qc-screenshots",
].filter((d) => {
  try {
    return fs.existsSync(d);
  } catch {
    return false;
  }
});

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

function isAppRoute(req) {
  const p = (req.path || "").toLowerCase();
  return /^\/(it|en|es)\/(app|login)(\/|$)/.test(p) || p === "/app" || p === "/login";
}

function hasAccessCookie(req) {
  const raw = req.headers.cookie || "";
  return /(?:^|;\s*)access_token=/.test(raw);
}

function loadPreviewCreds() {
  const email =
    process.env.CRM_PREVIEW_EMAIL ||
    process.env.ADMIN_EMAIL ||
    process.env.OMNIA_ADMIN_EMAIL ||
    "";
  const password =
    process.env.CRM_PREVIEW_PASSWORD ||
    process.env.ADMIN_PASSWORD ||
    process.env.OMNIA_ADMIN_PASSWORD ||
    "";
  if (email && password) return { email, password };
  // Fall back to local env file (server-side only — never exposed to browser)
  try {
    const envPath = path.join(__dirname, "..", "backend", ".env");
    const text = fs.readFileSync(envPath, "utf8");
    const get = (k) => {
      const m = text.match(new RegExp(`^${k}=(.*)$`, "m"));
      return m ? m[1].trim() : "";
    };
    return { email: get("ADMIN_EMAIL"), password: get("ADMIN_PASSWORD") };
  } catch {
    return { email: "", password: "" };
  }
}

function apiLoginForPreview() {
  return new Promise((resolve) => {
    const creds = loadPreviewCreds();
    if (!creds.email || !creds.password) {
      return resolve({ ok: false, cookies: [], error: "missing_preview_creds" });
    }
    const body = JSON.stringify({ email: creds.email, password: creds.password });
    const url = new URL(API);
    const req = http.request(
      {
        hostname: url.hostname,
        port: url.port || 80,
        path: "/api/auth/login",
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Content-Length": Buffer.byteLength(body),
          Connection: "close",
        },
        timeout: 8000,
      },
      (res) => {
        const setCookies = [].concat(res.headers["set-cookie"] || []);
        res.resume();
        resolve({
          ok: res.statusCode >= 200 && res.statusCode < 300 && setCookies.length > 0,
          cookies: setCookies,
          status: res.statusCode,
        });
      }
    );
    req.on("error", (err) => resolve({ ok: false, cookies: [], error: String(err.message || err) }));
    req.on("timeout", () => {
      req.destroy();
      resolve({ ok: false, cookies: [], error: "timeout" });
    });
    req.write(body);
    req.end();
  });
}

/** Rewrite Set-Cookie for the public host (tunnel) — drop Domain; add Secure on HTTPS. */
function forwardAuthCookies(res, setCookieHeaders, req) {
  const https =
    String((req.headers["x-forwarded-proto"] || "").split(",")[0]).trim() === "https" ||
    !!req.secure;
  for (const raw of setCookieHeaders || []) {
    let parts = String(raw)
      .split(";")
      .map((p) => p.trim())
      .filter((p) => p && !/^domain=/i.test(p));
    const hasSecure = parts.some((p) => /^secure$/i.test(p));
    if (https && !hasSecure) parts.push("Secure");
    // SameSite=None required by some browsers when Secure is set cross-site; keep Lax for first-party tunnel
    res.append("Set-Cookie", parts.join("; "));
  }
}

function injectQcBanner(html) {
  if (!CRM_PUBLIC_PREVIEW) return html;
  const banner = `
<style id="omnia-qc-style">
  #omnia-qc-banner{position:fixed;z-index:99999;left:0;right:0;top:0;background:#92400e;color:#fff;font:12px/1.4 system-ui,sans-serif;padding:8px 14px;text-align:center}
  body.omnia-qc-preview{padding-top:36px !important}
</style>
<script>window.__OMNIA_QC_PREVIEW__=true;document.documentElement.classList.add('omnia-qc-preview');</script>
<div id="omnia-qc-banner">QC PREVIEW · ImmoWeb gestionale aperto senza login (temporaneo) · non usare in produzione</div>`;
  if (/<body[^>]*>/i.test(html)) {
    return html.replace(/<body([^>]*)>/i, `<body$1 class="omnia-qc-preview">${banner}`);
  }
  return banner + html;
}

async function ensureQcSession(req, res) {
  if (!CRM_PUBLIC_PREVIEW) return false;
  if (!isAppRoute(req)) return false;
  if (hasAccessCookie(req)) return false;
  const result = await apiLoginForPreview();
  if (result.ok) {
    forwardAuthCookies(res, result.cookies, req);
    res.setHeader("X-Omnia-Qc-Session", "auto");
    return true;
  }
  res.setHeader("X-Omnia-Qc-Session", `fail:${result.error || result.status || "unknown"}`);
  return false;
}

function appRootInnerHtml(origin) {
  return `
  <div id="omnia-ssr-shell" data-omnia-ssr="1" data-omnia-surface="immoweb" style="min-height:70vh;background:#fafaf9;color:#1c1917;font-family:system-ui,sans-serif">
    <div style="max-width:720px;margin:0 auto;padding:48px 24px">
      <p style="letter-spacing:.24em;text-transform:uppercase;font-size:11px;color:#78716c">ImmoWeb · Gestionale OMNIA</p>
      <h1 style="font-family:Georgia,'Fraunces',serif;font-weight:400;font-size:2rem;line-height:1.2;margin:12px 0 16px">Area riservata agenzie</h1>
      <p style="color:#57534e;line-height:1.5">CRM, portafoglio, clienti, match e portali. Accedi per aprire la dashboard.</p>
      <p style="margin-top:24px">
        <a href="${escapeHtml(origin)}/it/login?next=%2Fit%2Fapp%2Fdashboard" style="display:inline-block;padding:12px 20px;background:#0B1E3F;color:#fff;text-decoration:none;border-radius:8px;font-size:14px">Accedi al gestionale</a>
      </p>
      <p style="margin-top:20px;font-size:13px;color:#a8a29e">
        Portale B2C: <a href="${escapeHtml(origin)}/it/cloud" style="color:#0B1E3F">ImmobilCloud</a>
      </p>
    </div>
  </div>`;
}

function rewriteAppSpaHtml(html, req) {
  const origin = publicOrigin(req);
  const url = `${origin}${req.originalUrl || req.path || "/"}`;
  const title = "ImmoWeb — Gestionale OMNIA";
  const description =
    "Area riservata agenzie: CRM, immobili, clienti, match e publishing portali.";
  let out = html;
  const replacements = [
    [/<title>[^<]*<\/title>/i, `<title>${escapeHtml(title)}</title>`],
    [/<meta name="description" content="[^"]*"\s*\/?>/i, `<meta name="description" content="${escapeHtml(description)}" />`],
    [/<meta property="og:title" content="[^"]*"\s*\/?>/i, `<meta property="og:title" content="${escapeHtml(title)}" />`],
    [/<meta property="og:description" content="[^"]*"\s*\/?>/i, `<meta property="og:description" content="${escapeHtml(description)}" />`],
    [/<meta property="og:url" content="[^"]*"\s*\/?>/i, `<meta property="og:url" content="${escapeHtml(url)}" />`],
    [/<meta property="og:site_name" content="[^"]*"\s*\/?>/i, `<meta property="og:site_name" content="ImmoWeb" />`],
    [/<meta name="twitter:title" content="[^"]*"\s*\/?>/i, `<meta name="twitter:title" content="${escapeHtml(title)}" />`],
    [/<meta name="twitter:description" content="[^"]*"\s*\/?>/i, `<meta name="twitter:description" content="${escapeHtml(description)}" />`],
    [/<link rel="canonical" href="[^"]*"\s*\/?>/i, `<link rel="canonical" href="${escapeHtml(url)}" />`],
    [/<meta name="robots" content="[^"]*"\s*\/?>/i, `<meta name="robots" content="noindex, nofollow" />`],
  ];
  for (const [re, rep] of replacements) {
    if (re.test(out)) out = out.replace(re, rep);
  }
  const inner = appRootInnerHtml(origin);
  // Replace #root by matching nested div depth (ImmobilCloud shell is baked into public/index.html)
  const start = out.search(/<div id="root"[^>]*>/i);
  if (start >= 0) {
    const openMatch = out.slice(start).match(/^<div id="root"[^>]*>/i);
    let i = start + openMatch[0].length;
    let depth = 1;
    while (i < out.length && depth > 0) {
      const nextOpen = out.indexOf("<div", i);
      const nextClose = out.indexOf("</div>", i);
      if (nextClose < 0) break;
      if (nextOpen >= 0 && nextOpen < nextClose) {
        depth += 1;
        i = nextOpen + 4;
      } else {
        depth -= 1;
        if (depth === 0) {
          out = `${out.slice(0, start)}<div id="root">${inner}</div>${out.slice(nextClose + 6)}`;
          break;
        }
        i = nextClose + 6;
      }
    }
  }
  out = out.replace(
    /<noscript>[\s\S]*?<\/noscript>/i,
    `<noscript>${inner}</noscript>`
  );
  return out;
}

function shouldServeCloudSnapshot(req) {
  const p = (req.path || "").toLowerCase();
  if (isAppRoute(req)) return false;
  if (p === "/" || p === "" || p === "/index.html") return true;
  if (/^\/(it|en|es)\/?$/.test(p)) return true;
  if (/^\/(it|en|es)\/cloud(\/|$)/.test(p)) return true;
  if (p === "/cloud" || p === "/cloud/") return true;
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

function extractSpaAssets(indexHtml) {
  const assets = [];
  const re =
    /<link[^>]+href="(\/static\/[^"]+\.css)"[^>]*>|<script[^>]+src="(\/static\/[^"]+\.js)"[^>]*><\/script>/gi;
  let m;
  while ((m = re.exec(indexHtml))) {
    if (m[1]) assets.push(`<link rel="stylesheet" href="${m[1]}">`);
    if (m[2]) assets.push(`<script defer src="${m[2]}"></script>`);
  }
  return assets.join("\n  ");
}

/**
 * Always-on SSR document for ImmobilCloud routes.
 * Markup is in the first byte of the response — curl/bots see "casa giusta"
 * without executing JS. SPA bundles still load and React replaces #root.
 */
function cloudSsrDocument(req, indexHtml) {
  const origin = publicOrigin(req);
  const title = "ImmobilCloud — La casa giusta, senza farsi raccontare storie";
  const description =
    "Cerca immobili in Italia. Scout ti dice se l'annuncio è completo, se il prezzo ha senso e cosa chiedere — prima della visita.";
  const image = `${origin}/cloud/hero.jpg`;
  const url = `${origin}${req.originalUrl || req.path || "/it/cloud"}`;
  const assets = extractSpaAssets(indexHtml || "");
  const inner = cloudRootInnerHtml(origin);

  return `<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>${escapeHtml(title)}</title>
  <meta name="description" content="${escapeHtml(description)}" />
  <meta name="robots" content="index, follow" />
  <link rel="canonical" href="${escapeHtml(url)}" />
  <link rel="icon" type="image/png" href="/favicon.png" />
  <meta property="og:type" content="website" />
  <meta property="og:site_name" content="ImmobilCloud" />
  <meta property="og:title" content="${escapeHtml(title)}" />
  <meta property="og:description" content="${escapeHtml(description)}" />
  <meta property="og:url" content="${escapeHtml(url)}" />
  <meta property="og:image" content="${escapeHtml(image)}" />
  <meta property="og:locale" content="it_IT" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="${escapeHtml(title)}" />
  <meta name="twitter:description" content="${escapeHtml(description)}" />
  <meta name="twitter:image" content="${escapeHtml(image)}" />
  <meta name="theme-color" content="#0B1E3F" />
  ${assets}
</head>
<body>
  <!-- SSR_MARKER casa giusta ImmobilCloud -->
  <div id="root">${inner}</div>
</body>
</html>`;
}

function apiReachable(cb) {
  // timeout → destroy → often also fires "error"; guard so healthz never double-responds
  // (double res.json crashed the process → ERR_EMPTY_RESPONSE / connection reset).
  let settled = false;
  const finish = (err, code) => {
    if (settled) return;
    settled = true;
    cb(err, code);
  };
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
      finish(null, res.statusCode);
    }
  );
  req.on("error", (err) => finish(err));
  req.on("timeout", () => {
    req.destroy();
    finish(new Error("timeout"));
  });
  req.end();
}

app.get("/healthz", (_req, res) => {
  apiReachable((err, code) => {
    if (res.headersSent || res.writableEnded) return;
    const apiOk = !err && code && code < 500;
    try {
      res.status(apiOk ? 200 : 503).json({
        ok: apiOk,
        preview: true,
        api_origin: API,
        api_ok: apiOk,
        api_status: code || null,
        crm_public_preview: CRM_PUBLIC_PREVIEW,
        error: err ? String(err.message || err) : null,
      });
    } catch (sendErr) {
      console.error("[healthz] send failed:", sendErr && sendErr.message);
    }
  });
});

app.use(
  "/api",
  createProxyMiddleware({
    target: API,
    changeOrigin: true,
    ws: false,
    proxyTimeout: 300000,
    timeout: 300000,
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

app.get("/ssr-check", (req, res) => {
  res.setHeader("Cache-Control", "no-store");
  res.setHeader("Content-Type", "text/plain; charset=utf-8");
  res.status(200).send("SSR_OK casa giusta ImmobilCloud\n");
});

function sendCloudSsr(req, res) {
  res.setHeader("Cache-Control", "no-store, no-cache, must-revalidate");
  res.setHeader("Connection", "close");
  res.setHeader("Pragma", "no-cache");
  const indexPath = path.join(BUILD, "index.html");
  fs.readFile(indexPath, "utf8", (err, html) => {
    const doc = cloudSsrDocument(req, err ? "" : html);
    res.setHeader("Content-Type", "text/html; charset=utf-8");
    res.setHeader("X-Omnia-Prerender", "ssr-always");
    res.status(200).send(doc);
  });
}

// Register SSR BEFORE static so /it/cloud never falls through to an empty shell.
[
  "/",
  "/index.html",
  "/it",
  "/it/",
  "/en",
  "/en/",
  "/es",
  "/es/",
  "/it/cloud",
  "/it/cloud/",
  "/en/cloud",
  "/en/cloud/",
  "/es/cloud",
  "/es/cloud/",
  "/cloud",
  "/cloud/",
].forEach((p) => app.get(p, sendCloudSsr));
app.get(/^\/(it|en|es)\/cloud(\/.*)?$/, sendCloudSsr);

// —— QC artifacts (public screenshots for external review) ——
// Keep outside frontend/build so express.static cannot redirect-loop /_qc/.
function resolveQcShot(name) {
  const safe = path.basename(String(name || ""));
  if (!safe || safe !== name || !/\.png$/i.test(safe)) return null;
  const dirs = [
    "/opt/cursor/artifacts/screenshots",
    "/tmp/omnia-stack/qc-screenshots",
    ...QC_SHOTS_DIRS,
  ];
  for (const dir of dirs) {
    try {
      const full = path.join(dir, safe);
      if (fs.existsSync(full)) return full;
    } catch {
      /* continue */
    }
  }
  return null;
}

function sendQcGallery(req, res) {
  // Prefer fully inline gallery (base64) so external reviewers never depend on cookie/JS/app.
  const inlineCandidates = [
    "/opt/cursor/artifacts/screenshots/gallery-inline.html",
    "/tmp/omnia-stack/qc-screenshots/gallery-inline.html",
  ];
  for (const full of inlineCandidates) {
    if (fs.existsSync(full)) {
      res.setHeader("Cache-Control", "no-store");
      res.setHeader("Content-Type", "text/html; charset=utf-8");
      res.setHeader("X-Omnia-Qc-Gallery", "inline-base64");
      return res.status(200).send(fs.readFileSync(full, "utf8"));
    }
  }
  const origin = publicOrigin(req);
  const shots = [
    ["01-gestionale-dashboard.png", "Dashboard gestionale"],
    ["02-gestionale-immobili.png", "Lista immobili"],
    ["03-gestionale-scheda-immobile.png", "Scheda immobile"],
    ["04-gestionale-clienti.png", "Clienti / CRM"],
    ["05-gestionale-hal.png", "HAL Knowledge"],
  ];
  const cards = shots
    .map(
      ([file, label]) => `
    <section style="margin:0 0 48px">
      <h2 style="font:600 18px system-ui;margin:0 0 12px">${escapeHtml(label)}</h2>
      <p style="font:13px system-ui;color:#57534e;margin:0 0 12px"><a href="${escapeHtml(origin)}/_qc/screenshots/${escapeHtml(file)}">${escapeHtml(file)}</a></p>
      <img src="${escapeHtml(origin)}/_qc/screenshots/${escapeHtml(file)}" alt="${escapeHtml(label)}" style="width:100%;max-width:1100px;border:1px solid #d6d3d1;border-radius:8px" />
    </section>`
    )
    .join("\n");
  res.setHeader("Cache-Control", "no-store");
  res.setHeader("Content-Type", "text/html; charset=utf-8");
  res.status(200).send(`<!doctype html>
<html lang="it"><head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>ImmoWeb QC — screenshot gestionale</title>
<meta name="robots" content="noindex,nofollow"/>
</head>
<body style="margin:0;background:#fafaf9;color:#1c1917;font-family:system-ui,sans-serif">
  <header style="padding:28px 24px;border-bottom:1px solid #e7e5e4;background:#fff">
    <p style="margin:0;letter-spacing:.2em;text-transform:uppercase;font-size:11px;color:#a8a29e">ImmoWeb · QC review</p>
    <h1 style="margin:8px 0 0;font:400 28px Georgia,serif">Screenshot gestionale</h1>
  </header>
  <main style="padding:32px 24px;max-width:1140px;margin:0 auto">${cards}</main>
</body></html>`);
}

app.get(["/_qc", "/_qc/", "/qc", "/qc/"], sendQcGallery);

app.get("/_qc/screenshots/:file", (req, res) => {
  const full = resolveQcShot(req.params.file);
  if (!full) return res.status(404).type("text").send("not found");
  res.setHeader("Cache-Control", "public, max-age=300");
  res.sendFile(full);
});

app.get("/qc/screenshots/:file", (req, res) => {
  const full = resolveQcShot(req.params.file);
  if (!full) return res.status(404).type("text").send("not found");
  res.setHeader("Cache-Control", "public, max-age=300");
  res.sendFile(full);
});

app.use(
  express.static(BUILD, {
    index: false,
    maxAge: "5m",
    etag: true,
    setHeaders(res) {
      res.setHeader("Connection", "close");
    },
  })
);

app.get("*", async (req, res) => {
  res.setHeader("Cache-Control", "no-store, no-cache, must-revalidate");
  res.setHeader("Connection", "close");
  res.setHeader("Pragma", "no-cache");

  if (shouldServeCloudSnapshot(req)) {
    return sendCloudSsr(req, res);
  }

  try {
    await ensureQcSession(req, res);
  } catch (e) {
    console.error("[qc-session]", e && e.message);
  }

  const indexPath = path.join(BUILD, "index.html");
  fs.readFile(indexPath, "utf8", (err, html) => {
    if (err || !html) {
      return res.status(503).json({
        detail: "frontend_build_missing",
        message: "Esegui: cd frontend && REACT_APP_BACKEND_URL= yarn build",
      });
    }
    let body = isAppRoute(req) ? rewriteAppSpaHtml(html, req) : html;
    if (isAppRoute(req) && CRM_PUBLIC_PREVIEW) body = injectQcBanner(body);
    res.setHeader("Content-Type", "text/html; charset=utf-8");
    if (isAppRoute(req)) res.setHeader("X-Omnia-Surface", "immoweb");
    if (CRM_PUBLIC_PREVIEW) res.setHeader("X-Omnia-Qc-Preview", "1");
    res.status(200).send(body);
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
  if (CRM_PUBLIC_PREVIEW) {
    console.log(`QC PREVIEW ON — /it/app/dashboard auto-session · screenshots /_qc/`);
  }
});

process.on("SIGTERM", () => server.close(() => process.exit(0)));
process.on("SIGINT", () => server.close(() => process.exit(0)));
