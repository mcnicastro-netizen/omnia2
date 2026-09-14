import React from "react";

/**
 * Global error boundary — prevents white-screen-of-death in production.
 * Logs the error to console and offers a graceful "reload / report" UI.
 */
export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, errorInfo) {
    // Keep a structured log so DevTools shows it cleanly
    // eslint-disable-next-line no-console
    console.error("[OMNIA ErrorBoundary]", error, errorInfo);
    this.setState({ errorInfo });
  }

  handleReload = () => {
    try { window.location.reload(); } catch { /* noop */ }
  };

  handleHome = () => {
    try { window.location.href = "/"; } catch { /* noop */ }
  };

  render() {
    if (!this.state.error) return this.props.children;
    const stack = (this.state.error?.stack || String(this.state.error || "")).slice(0, 600);
    return (
      <div
        data-testid="error-boundary"
        className="min-h-screen flex items-center justify-center px-6 bg-stone-50"
      >
        <div className="max-w-lg w-full bg-white border border-stone-200 rounded-lg p-8 shadow-sm">
          <div className="text-5xl mb-4">⚠️</div>
          <h1
            className="text-2xl font-semibold text-stone-900 mb-2"
            style={{ fontFamily: "'Fraunces', Georgia, serif" }}
          >
            Qualcosa è andato storto
          </h1>
          <p className="text-sm text-stone-600 mb-5">
            Abbiamo registrato l'errore. Prova a ricaricare la pagina — se il problema persiste, contattaci.
          </p>
          {process.env.NODE_ENV !== "production" && (
            <details className="bg-stone-50 border border-stone-200 rounded-md text-xs text-stone-700 mb-5">
              <summary className="cursor-pointer px-3 py-2 font-medium">Dettaglio tecnico</summary>
              <pre className="px-3 py-3 overflow-x-auto whitespace-pre-wrap break-words">{stack}</pre>
            </details>
          )}
          <div className="flex gap-3">
            <button
              data-testid="error-reload-btn"
              onClick={this.handleReload}
              className="flex-1 px-4 py-2.5 bg-stone-900 text-white text-xs uppercase tracking-widest rounded-md hover:bg-stone-700"
            >
              Ricarica
            </button>
            <button
              data-testid="error-home-btn"
              onClick={this.handleHome}
              className="px-4 py-2.5 border border-stone-300 text-stone-700 text-xs uppercase tracking-widest rounded-md hover:bg-stone-50"
            >
              Vai alla home
            </button>
          </div>
        </div>
      </div>
    );
  }
}
