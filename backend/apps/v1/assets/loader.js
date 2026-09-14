(function () {
  // OMNIA Widget Loader v1 — M2.5.3
  // Reads <script data-*> config, creates a responsive iframe pointing to the
  // widget page, and listens to postMessage for auto-resize.
  //
  // Backend base injected at serve time: __BACKEND_BASE__
  var BACKEND = "__BACKEND_BASE__";
  var current = document.currentScript;
  if (!current) return;

  var key = current.getAttribute("data-key");
  var widget = current.getAttribute("data-widget") || "valuator";
  var primary = current.getAttribute("data-primary") || "#0b1e3f";
  var lang = current.getAttribute("data-lang") || "it";
  var target = current.getAttribute("data-target"); // optional CSS selector

  if (!key || key.indexOf("omk_live_") !== 0) {
    console.error("[OMNIA] Missing or invalid data-key on <script> tag.");
    return;
  }
  if (["valuator", "mortgages", "staging", "legal"].indexOf(widget) === -1) {
    console.error("[OMNIA] Unknown data-widget:", widget);
    return;
  }

  var params = new URLSearchParams({
    key: key,
    primary: primary,
    lang: lang,
  });
  var iframeSrc = BACKEND + "/api/widgets/v1/" + widget + ".html?" + params.toString();

  var iframe = document.createElement("iframe");
  iframe.src = iframeSrc;
  iframe.title = "OMNIA " + widget + " widget";
  iframe.setAttribute("loading", "lazy");
  iframe.style.width = "100%";
  iframe.style.border = "0";
  iframe.style.display = "block";
  iframe.style.minHeight = "500px";
  iframe.style.background = "transparent";
  iframe.allow = "clipboard-write";
  iframe.setAttribute("data-omnia-widget", widget);

  var mount;
  if (target) {
    mount = document.querySelector(target);
  }
  if (!mount) {
    // insert right before the script tag
    mount = current.parentNode;
    mount.insertBefore(iframe, current);
  } else {
    mount.appendChild(iframe);
  }

  // Auto-resize via postMessage from the widget
  window.addEventListener("message", function (ev) {
    if (!ev.data || ev.data.omnia !== widget) return;
    if (ev.data.type === "resize" && typeof ev.data.height === "number") {
      iframe.style.height = Math.min(Math.max(ev.data.height, 300), 2000) + "px";
    }
  });
})();
