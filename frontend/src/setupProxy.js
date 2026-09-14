/**
 * Dev proxy: browser calls /api/* on the FE origin → backend :43121
 * Enables single-tunnel preview when Cursor port-forward is unavailable.
 */
const { createProxyMiddleware } = require("http-proxy-middleware");

module.exports = function setupProxy(app) {
  app.use(
    "/api",
    createProxyMiddleware({
      target: "http://127.0.0.1:43121",
      changeOrigin: true,
      ws: true,
      logLevel: "warn",
    })
  );
};
