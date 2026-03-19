(function () {
  const STATUS_COLOR = {
    NOTIFYING: "#fd7e14",
    DUE: "#dc3545",
    TRIGGERED: "#212529",
  };

  const DEFAULT_COLOR = "#198754";

  function formatRemaining(seconds) {
    const absSeconds = Math.max(0, Math.floor(seconds));
    const days = Math.floor(absSeconds / 86400);
    const hours = Math.floor((absSeconds % 86400) / 3600);
    const minutes = Math.floor((absSeconds % 3600) / 60);
    const secs = absSeconds % 60;

    if (days > 0) {
      return `${days}d ${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
    }

    return `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
  }

  function getStatusColor(status) {
    return STATUS_COLOR[status] || DEFAULT_COLOR;
  }

  function renderTimer(timerEl) {
    const nextTriggerAt = Number(timerEl.dataset.nextTriggerAt);
    const status = timerEl.dataset.status;

    timerEl.style.color = getStatusColor(status);

    if (!Number.isFinite(nextTriggerAt)) {
      timerEl.textContent = "--:--:--";
      return;
    }

    const now = Date.now() / 1000;
    const remaining = nextTriggerAt - now;
    timerEl.textContent = formatRemaining(remaining);
  }

  function initCountdownTimers(options) {
    const config = options || {};
    const root = config.root || document;
    const selector = config.selector || ".countdown-timer";
    const intervalMs = config.intervalMs || 1000;
    const timers = Array.from(root.querySelectorAll(selector));

    if (timers.length === 0) {
      return null;
    }

    timers.forEach(renderTimer);

    const intervalId = window.setInterval(function () {
      timers.forEach(renderTimer);
    }, intervalMs);

    return {
      timers: timers,
      intervalId: intervalId,
      stop: function () {
        window.clearInterval(intervalId);
      },
    };
  }

  window.InsuranceHolderCountdown = {
    formatRemaining: formatRemaining,
    getStatusColor: getStatusColor,
    renderTimer: renderTimer,
    initCountdownTimers: initCountdownTimers,
  };

  document.addEventListener("DOMContentLoaded", function () {
    initCountdownTimers();
  });
})();
