// Browser Source overlay JS.
//   * Connects to /ws/subtitles to receive live partial + final events.
//   * Renders a single caption line with a typewriter / fade / slide
//     animation depending on the body class.
//   * Reads style overrides from the URL hash: #color=%23ff0&size=56...

(function () {
  "use strict";

  const wsScheme = location.protocol === "https:" ? "wss" : "ws";
  const ws = new WebSocket(`${wsScheme}://${location.host}/ws/subtitles`);

  const captionEl = document.getElementById("caption");
  const lineEl = document.getElementById("caption-line");
  let pendingText = "";
  let currentText = "";
  let hideTimer = null;
  let partialBuffer = "";
  let lastPartialAt = 0;

  function parseHash() {
    const hash = location.hash.replace(/^#/, "");
    if (!hash) return;
    const params = new URLSearchParams(hash);
    const set = (k, v) => {
      if (v) document.body.dataset[k] = v;
    };
    const color = params.get("color");
    if (color) {
      document.documentElement.style.setProperty("--caption-color", color);
    }
    const bg = params.get("bg");
    if (bg) {
      document.documentElement.style.setProperty("--caption-bg", bg);
    }
    const size = params.get("size");
    if (size) {
      document.documentElement.style.setProperty("--caption-size", size + "px");
    }
    if (params.get("position")) {
      document.body.className = document.body.className.replace(
        /position-\w+/g, ""
      );
      document.body.classList.add("position-" + params.get("position"));
    }
    if (params.get("layout")) {
      document.body.className = document.body.className.replace(
        /layout-\w+/g, ""
      );
      document.body.classList.add("layout-" + params.get("layout"));
    }
    if (params.get("animation")) {
      document.body.className = document.body.className.replace(
        /animation-\w+/g, ""
      );
      document.body.classList.add("animation-" + params.get("animation"));
    }
  }

  function show(text) {
    if (hideTimer) { clearTimeout(hideTimer); hideTimer = null; }
    currentText = text;
    lineEl.textContent = text;
    captionEl.classList.remove("empty");
    captionEl.classList.add("show");
  }

  function scheduleHide() {
    if (hideTimer) clearTimeout(hideTimer);
    hideTimer = setTimeout(() => {
      captionEl.classList.add("empty");
      captionEl.classList.remove("show");
      lineEl.textContent = "";
    }, 4000);
  }

  function appendPartial(delta) {
    partialBuffer += delta;
    lastPartialAt = Date.now();
    show(partialBuffer);
    scheduleHide();
  }

  function finalize(text) {
    if (text) partialBuffer = text;
    show(partialBuffer);
    partialBuffer = "";
    scheduleHide();
  }

  function clearAll() {
    partialBuffer = "";
    currentText = "";
    lineEl.textContent = "";
    captionEl.classList.add("empty");
    captionEl.classList.remove("show");
    if (hideTimer) { clearTimeout(hideTimer); hideTimer = null; }
  }

  ws.addEventListener("open", () => {
    console.log("overlay ws connected");
  });

  ws.addEventListener("message", (ev) => {
    let payload;
    try { payload = JSON.parse(ev.data); } catch { return; }
    if (payload.type === "current" && payload.line) {
      show(payload.line.text || "");
    } else if (payload.type === "partial") {
      appendPartial(payload.text || "");
    } else if (payload.type === "final") {
      finalize(payload.text || "");
    } else if (payload.type === "cleared") {
      clearAll();
    }
  });

  ws.addEventListener("close", () => {
    // Reconnect with backoff so the overlay survives an admin restart.
    setTimeout(() => location.reload(), 2000);
  });

  parseHash();
})();
