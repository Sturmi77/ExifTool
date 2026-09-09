function formatEta(seconds) {
  if (seconds == null || seconds < 0) return "";
  const minutes = Math.max(1, Math.round(Number(seconds) / 60));
  if (minutes < 60) return `ca. ${minutes} Min. verbleibend`;
  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;
  return rest ? `ca. ${hours} Std. ${rest} Min. verbleibend` : `ca. ${hours} Std. verbleibend`;
}

function renderJob(job) {
  const progress = document.getElementById("scan-progress");
  const label = document.getElementById("scan-label");
  const startBtn = document.getElementById("scan-start");
  const cancelBtn = document.getElementById("scan-cancel");
  const errorEl = document.getElementById("scan-error");
  if (!progress || !label) return job;

  const running = Boolean(job && job.running);
  const total = Number(job && job.total) || 0;
  const done = Number(job && job.done) || 0;
  const status = (job && job.status) || "idle";
  progress.max = total > 0 ? total : 1;
  progress.value = total > 0 ? done : 0;

  if (!job || !job.id) {
    label.textContent = "Noch kein Scan";
  } else if (running) {
    const eta = formatEta(job.eta_seconds);
    label.textContent = eta
      ? `Scan läuft: ${done} / ${total} – ${eta}`
      : `Scan läuft: ${done} / ${total}`;
  } else if (status === "cancelled") {
    label.textContent = `Abgebrochen (${done} / ${total})`;
  } else if (status === "error") {
    label.textContent = "Scan fehlgeschlagen";
  } else if (status === "done") {
    label.textContent = `Fertig: ${done} Dateien, ${job.skipped || 0} übersprungen`;
  } else {
    label.textContent = status;
  }

  if (startBtn) startBtn.disabled = running;
  if (cancelBtn) cancelBtn.disabled = !running;
  if (errorEl) {
    if (job && job.error) {
      errorEl.hidden = false;
      errorEl.textContent = job.error;
    } else {
      errorEl.hidden = true;
      errorEl.textContent = "";
    }
  }
  return job;
}

async function fetchStatus() {
  const res = await fetch("/gaps/status");
  if (!res.ok) return null;
  return renderJob(await res.json());
}

let pollTimer = null;
function startPolling() {
  if (pollTimer) return;
  pollTimer = setInterval(async () => {
    const job = await fetchStatus();
    if (job && !job.running) {
      clearInterval(pollTimer);
      pollTimer = null;
      if (job.status === "done") window.location.reload();
    }
  }, 1500);
}

async function startScan() {
  const res = await fetch("/gaps/scan", { method: "POST" });
  const body = await res.json().catch(() => ({}));
  if (res.status === 409) {
    startPolling();
    return;
  }
  if (!res.ok) {
    renderJob({ status: "error", error: body.error || "Scan konnte nicht starten", running: false });
    return;
  }
  await fetchStatus();
  startPolling();
}

async function cancelScan() {
  await fetch("/gaps/scan/cancel", { method: "POST" });
  await fetchStatus();
}

document.addEventListener("DOMContentLoaded", async () => {
  const startBtn = document.getElementById("scan-start");
  const cancelBtn = document.getElementById("scan-cancel");
  const openBtn = document.getElementById("open-selected");
  if (startBtn) startBtn.addEventListener("click", startScan);
  if (cancelBtn) cancelBtn.addEventListener("click", cancelScan);
  if (openBtn) openBtn.addEventListener("click", openSelectedInEditor);
  const job = await fetchStatus();
  if (job && job.running) startPolling();
});

function openSelectedInEditor() {
  const boxes = Array.from(document.querySelectorAll(".gap-select:checked"));
  if (!boxes.length) {
    window.alert("Bitte beschreibbare Dateien auswählen.");
    return;
  }
  const subdirs = new Set(boxes.map((box) => box.dataset.subdir || ""));
  if (subdirs.size > 1) {
    window.alert("Bitte nur Dateien aus demselben Ordner auswählen.");
    return;
  }
  const params = new URLSearchParams();
  params.set("subdir", boxes[0].dataset.subdir || "");
  params.set("selected", boxes[0].dataset.name || "");
  boxes.forEach((box) => params.append("checked", box.dataset.name || ""));
  window.location.href = "/?" + params.toString();
}
