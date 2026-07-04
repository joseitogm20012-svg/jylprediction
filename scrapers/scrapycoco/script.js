document.addEventListener("DOMContentLoaded", () => {
  const scrapersGrid = document.getElementById("scrapers-grid");
  const consoleOutput = document.getElementById("console-output");
  const btnClearConsole = document.getElementById("btn-clear-console");
  const chkAutoscroll = document.getElementById("chk-autoscroll");
  const chkSandbox = document.getElementById("chk-sandbox");
  const sandboxIndicator = document.getElementById("sandbox-indicator");
  const batchProgress = document.getElementById("batch-progress");
  const batchProgressFill = document.getElementById("batch-progress-fill");
  const batchProgressText = document.getElementById("batch-progress-text");
  const batchCount = document.getElementById("batch-count");
  const btnBatchRun = document.getElementById("btn-batch-run");

  let activeEventSource = null;
  let runningScraperId = null;
  let currentLogLevel = "all";
  let historyChart = null;
  let durationChart = null;
  let previewData = null;
  let previewScraperId = null;

  // ── Log System ──
  function appendLog(text, type = "normal") {
    const line = document.createElement("div");
    line.className = "console-line";
    const map = { system: "system-msg", error: "error-msg", success: "success-msg", warning: "warning-msg", info: "info-msg" };
    if (map[type]) line.classList.add(map[type]);
    line.textContent = text;
    line.dataset.logLevel = type;
    consoleOutput.appendChild(line);
    if (chkAutoscroll.checked) consoleOutput.scrollTop = consoleOutput.scrollHeight;
  }

  function reapplyLogFilters() {
    const level = currentLogLevel;
    consoleOutput.querySelectorAll(".console-line").forEach(el => {
      el.style.display = (level === "all" || el.dataset.logLevel === level) ? "" : "none";
    });
  }

  document.querySelectorAll(".log-filter-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".log-filter-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      currentLogLevel = btn.dataset.level;
      reapplyLogFilters();
    });
  });

  chkSandbox.addEventListener("change", () => {
    sandboxIndicator.classList.toggle("hidden", !chkSandbox.checked);
  });

  btnClearConsole.addEventListener("click", () => {
    consoleOutput.innerHTML = `<div class="console-line system-msg">[Sistema] Consola limpiada.</div>`;
  });

  // ── Tab System ──
  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
      btn.classList.add("active");
      const tab = document.getElementById("tab-" + btn.dataset.tab);
      if (tab) {
        tab.classList.add("active");
        if (btn.dataset.tab === "history") loadHistory();
      }
    });
  });

  function getLogLevel(parsed) {
    const map = { info: "info", warning: "warning", error: "error", success: "success", system: "system" };
    return map[parsed.level || "info"] || "normal";
  }

  // ── Scrapers ──
  async function loadScrapers() {
    try {
      const res = await fetch("/api/scrapers");
      renderScrapers(await res.json());
    } catch {
      scrapersGrid.innerHTML = `<div class="loading-state" style="color:var(--color-error)">Error conectando con el servidor</div>`;
    }
  }

  function renderScrapers(scrapers) {
    scrapersGrid.innerHTML = "";
    scrapers.forEach(s => {
      const card = document.createElement("div");
      card.className = "scraper-card";
      let sc = "idle", sl = "Listo";
      if (s.status === "running") { sc = "running"; sl = "Ejecutando..."; card.classList.add("running"); runningScraperId = s.id; }
      else if (s.exit_code === 0) { sc = "success"; sl = "Exitoso"; card.classList.add("success-state"); }
      else if (s.exit_code !== null) { sc = "error"; sl = "Fallido"; card.classList.add("error-state"); }
      const lastRun = s.last_run ? new Date(s.last_run).toLocaleString() : "Nunca";
      const isScript = ["results", "wc2026", "elo"].includes(s.id);
      card.innerHTML = `
        <div class="card-top">
          <div class="card-title-row">
            <label class="card-checkbox-label" title="Seleccionar para ejecución por lotes">
              <input type="checkbox" class="scraper-checkbox" data-id="${s.id}" onchange="updateBatchCount()">
            </label>
            <h3>${s.name}</h3>
            <span class="status-badge ${sc}">${sl}</span>
          </div>
          <p class="scraper-desc">${s.description}</p>
        </div>
        <div class="card-bottom">
          <div class="card-meta">
            <div class="meta-item"><span>Última ejecución:</span><span class="meta-val">${lastRun}</span></div>
          </div>
          <div class="card-actions">
            <button class="btn btn-secondary btn-sm btn-preview" data-id="${s.id}" ${isScript ? "disabled title='No soportado para scripts legacy'" : ""}>Vista Previa</button>
            <button class="btn btn-secondary btn-sm btn-diagnostic" data-id="${s.id}" ${isScript ? "disabled title='No soportado para scripts legacy'" : ""} onclick="openDiagnostic('${s.id}')">Diagnóstico</button>
            <button class="btn btn-primary btn-run" data-id="${s.id}" ${runningScraperId && runningScraperId !== s.id ? "disabled" : ""}>
              ${s.status === "running" ? "[Ejecutando]" : "Ejecutar"}
            </button>
          </div>
        </div>
      `;
      scrapersGrid.appendChild(card);
    });
    document.querySelectorAll(".btn-run").forEach(b => b.addEventListener("click", () => startScraper(b.dataset.id)));
    document.querySelectorAll(".btn-preview").forEach(b => b.addEventListener("click", () => openPreview(b.dataset.id)));
  }

  window.updateBatchCount = function() {
    const checked = document.querySelectorAll(".scraper-checkbox:checked").length;
    batchCount.textContent = checked + " seleccionados";
    btnBatchRun.disabled = checked === 0;
  };

  window.runBatch = async function() {
    const ids = [...document.querySelectorAll(".scraper-checkbox:checked")].map(c => c.dataset.id);
    if (!ids.length) return;
    const sandbox = chkSandbox.checked;
    batchProgress.style.display = "block";
    batchProgressFill.style.width = "0%";
    batchProgressText.textContent = `0/${ids.length} — Iniciando...`;
    if (activeEventSource) activeEventSource.close();

    const res = await fetch("/api/batch/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scraper_ids: ids, sandbox })
    });
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const events = buffer.split("\n\n");
      buffer = events.pop() || "";
      for (const evt of events) {
        const lines = evt.split("\n");
        let evtName = "message", data = "";
        for (const l of lines) {
          if (l.startsWith("event: ")) evtName = l.slice(7);
          else if (l.startsWith("data: ")) data = l.slice(6);
        }
        let parsed;
        try { parsed = JSON.parse(data); } catch { parsed = null; }

        if (evtName === "batch-start") {
          batchProgressText.textContent = `0/${parsed.total} — Iniciando...`;
        } else if (evtName === "batch-progress" && parsed) {
          const pct = Math.round((parsed.completed / parsed.total) * 100);
          batchProgressFill.style.width = pct + "%";
          const statusIcon = parsed.status === "error" ? "[Fallo]" : "[Exitoso]";
          batchProgressText.textContent = `${parsed.completed}/${parsed.total} — ${parsed.current_scraper} ${statusIcon}`;
        } else if (evtName === "batch-end" && parsed) {
          batchProgressText.textContent = `Completado — ${parsed.completed} éxitos, ${parsed.failed} fallos`;
          if (parsed.failed > 0) batchProgressFill.style.background = "var(--color-warning)";
          setTimeout(() => { batchProgress.style.display = "none"; batchProgressFill.style.background = ""; }, 3000);
        } else if (evtName === "log" && parsed) {
          const type = getLogLevel(parsed);
          appendLog((type === "error" ? "[Error] " : type === "warning" ? "[Advertencia] " : type === "success" ? "[Éxito] " : "") + parsed.message, type);
        } else if (evtName === "start" && parsed) {
          appendLog(parsed.message, "system");
        } else if (evtName === "end" && parsed) {
          appendLog(parsed.message, parsed.level === "error" ? "error" : "success");
        }
      }
    }
    loadScrapers();
    updateBatchCount();
  };

  function startScraper(scraperId) {
    if (activeEventSource) activeEventSource.close();
    appendLog(`[Sistema] Iniciando scraper: "${scraperId}"...`, "system");
    document.querySelectorAll(".btn-run").forEach(b => b.disabled = true);
    const sandbox = chkSandbox.checked;
    let params = [];
    const mid = document.getElementById("custom-match-id").value;
    const tn = document.getElementById("custom-team-name").value;
    if (mid && mid.trim()) params.push("match_id=" + encodeURIComponent(mid.trim()));
    if (tn && tn.trim()) params.push("team_name=" + encodeURIComponent(tn.trim()));
    if (sandbox) params.push("sandbox=true");
    const qs = params.length ? "?" + params.join("&") : "";
    activeEventSource = new EventSource(`/api/run/${scraperId}${qs}`);
    runningScraperId = scraperId;

    activeEventSource.addEventListener("start", e => {
      try { appendLog(JSON.parse(e.data).message, "system"); } catch { appendLog(e.data, "system"); }
      loadScrapers();
    });
    activeEventSource.addEventListener("log", e => {
      try {
        const d = JSON.parse(e.data);
        const type = getLogLevel(d);
        appendLog((type === "error" ? "[Error] " : type === "warning" ? "[Advertencia] " : type === "success" ? "[Éxito] " : "") + d.message, type);
      } catch { appendLog(e.data); }
    });
    activeEventSource.onmessage = e => appendLog(e.data);
    activeEventSource.addEventListener("end", e => {
      try {
        const d = JSON.parse(e.data);
        appendLog(d.message, d.level === "error" ? "error" : "success");
      } catch { appendLog(e.data, "success"); }
      cleanup();
    });
    activeEventSource.onerror = () => { appendLog("[Error] Conexión interrumpida.", "error"); cleanup(); };
    function cleanup() { if (activeEventSource) { activeEventSource.close(); activeEventSource = null; } runningScraperId = null; loadScrapers(); }
  }

  // ── Preview ──
  window.openPreview = async function(scraperId) {
    previewScraperId = scraperId;
    document.getElementById("preview-modal-title").textContent = "Vista Previa — " + scraperId;
    document.getElementById("preview-tbody").innerHTML = '<tr><td colspan="10" class="loading-state">Cargando...</td></tr>';
    document.getElementById("preview-modal").style.display = "flex";
    try {
      const res = await fetch(`/api/preview/${scraperId}?limit=50&sandbox=true`);
      const data = await res.json();
      previewData = data;
      renderPreviewTable(data);
    } catch {
      document.getElementById("preview-tbody").innerHTML = '<tr><td class="loading-state" style="color:var(--color-error)">Error cargando preview</td></tr>';
    }
  };

  function renderPreviewTable(data) {
    const thead = document.getElementById("preview-thead");
    const tbody = document.getElementById("preview-tbody");
    document.getElementById("preview-count").textContent = data.total + " registros (mostrando " + data.rows.length + ")";
    document.getElementById("preview-warnings-count").textContent = data.warnings.length + " advertencias";

    if (!data.columns.length || !data.rows.length) {
      thead.innerHTML = "";
      tbody.innerHTML = '<tr><td class="loading-state">Sin datos</td></tr>';
      return;
    }

    const warningMap = {};
    data.warnings.forEach(w => {
      if (!warningMap[w.row]) warningMap[w.row] = {};
      warningMap[w.row][w.field] = w;
    });

    thead.innerHTML = "<tr>" + data.columns.map(c => `<th onclick="sortPreviewTable('${c}')">${c}</th>`).join("") + "</tr>";
    tbody.innerHTML = data.rows.map((row, i) => {
      const warns = warningMap[i];
      const hasError = warns && Object.values(warns).some(w => w.severity === "error");
      const hasWarning = warns && Object.values(warns).some(w => w.severity === "warning");
      let cls = "preview-row";
      if (hasError) cls += " preview-error-row";
      else if (hasWarning) cls += " preview-warning-row";
      const cells = data.columns.map(c => {
        let cell = `<td>${row[c] !== null && row[c] !== undefined ? String(row[c]) : '<span class="null-value">—</span>'}</td>`;
        if (warns && warns[c]) {
          cell = `<td class="cell-warning" title="${warns[c].message} (${warns[c].severity})">${row[c] !== null && row[c] !== undefined ? String(row[c]) : '<span class="null-value">—</span>'} <span class="cell-warning-icon">⚠️</span></td>`;
        }
        return cell;
      }).join("");
      return `<tr class="${cls}">${cells}</tr>`;
    }).join("");
  }

  window.sortPreviewTable = function(col) {
    if (!previewData) return;
    const rows = [...previewData.rows];
    rows.sort((a, b) => {
      const va = a[col], vb = b[col];
      if (va == null) return 1; if (vb == null) return -1;
      if (typeof va === "number" && typeof vb === "number") return va - vb;
      return String(va).localeCompare(String(vb));
    });
    previewData.rows = rows;
    renderPreviewTable(previewData);
  };

  window.closePreviewModal = function(e) {
    if (!e || e.target.id === "preview-modal") {
      document.getElementById("preview-modal").style.display = "none";
      previewData = null;
      previewScraperId = null;
    }
  };

  // ── Export from Preview ──
  window.exportFromPreview = async function(format) {
    if (!previewData) return;
    const transforms = [...document.querySelectorAll(".transform-check:checked")].map(c => c.value);
    await doExport(format, transforms);
  };

  window.showExportSubmodal = function() {
    document.getElementById("export-submodal").style.display = "flex";
  };

  window.closeExportSubmodal = function() {
    document.getElementById("export-submodal").style.display = "none";
  };

  window.confirmExport = async function() {
    const format = document.querySelector('input[name="sub-export-format"]:checked').value;
    const transforms = [...document.querySelectorAll(".sub-transform-check:checked")].map(c => c.value);
    await doExport(format, transforms);
    closeExportSubmodal();
  };

  async function doExport(format, transforms) {
    if (!previewData || !previewScraperId) return;
    try {
      const res = await fetch("/api/export", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          scraper_id: previewScraperId,
          format,
          transforms,
          preview_data: previewData.rows
        })
      });
      if (!res.ok) { appendLog("[Error] Error en exportación: " + res.statusText, "error"); return; }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = previewScraperId + "_" + new Date().toISOString().slice(0, 10) + "." + format;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      appendLog(`[Éxito] Exportado ${blob.size > 1024 ? Math.round(blob.size/1024) + "KB" : blob.size + "B"} como .${format}`, "success");
    } catch (err) {
      appendLog("[Error] Error de red al exportar: " + err.message, "error");
    }
  }

  // ── History ──
  async function loadHistory() {
    const tbody = document.getElementById("history-tbody");
    try {
      const [hRes, mRes, sRes] = await Promise.all([
        fetch("/api/history?limit=100"),
        fetch("/api/history/metrics"),
        fetch("/api/history/stats")
      ]);
      const history = await hRes.json();
      const metrics = await mRes.json();
      const stats = await sRes.json();

      document.getElementById("metric-total").textContent = metrics.total_runs || 0;
      const sr = metrics.total_runs > 0 ? Math.round((metrics.success_count || 0) / metrics.total_runs * 100) : 0;
      document.getElementById("metric-success-rate").textContent = sr + "%";
      document.getElementById("metric-avg-duration").textContent = metrics.avg_duration_ms ? Math.round(metrics.avg_duration_ms) + "ms" : "—";
      document.getElementById("metric-records").textContent = metrics.total_records || 0;

      const filter = document.getElementById("history-scraper-filter");
      const curVal = filter.value;
      const ids = [...new Set(stats.map(s => s.scraper_id))];
      filter.innerHTML = '<option value="">Todos los scrapers</option>' + ids.map(i => `<option value="${i}">${i}</option>`).join("");
      filter.value = curVal;

      tbody.innerHTML = history.length ? history.map(r => {
        const statusClass = r.status === "success" ? "status-ok" : "status-fail";
        const dur = r.duration_ms ? (r.duration_ms >= 1000 ? (r.duration_ms/1000).toFixed(1)+"s" : r.duration_ms+"ms") : "—";
        return `<tr>
          <td><strong>${r.scraper_id}</strong></td>
          <td>${r.started_at ? new Date(r.started_at).toLocaleString() : "—"}</td>
          <td>${dur}</td>
          <td><span class="${statusClass}">${r.status === "success" ? "✅ Éxito" : "❌ Error"}</span></td>
          <td>${r.records_count != null ? r.records_count : "—"}</td>
          <td>${r.sandbox ? '<span class="badge-sandbox">🧪 Sandbox</span>' : "—"}</td>
        </tr>`;
      }).join("") : '<tr><td colspan="6" class="loading-state" style="padding:24px">Sin ejecuciones registradas</td></tr>';

      renderHistoryCharts(stats);
    } catch { tbody.innerHTML = '<tr><td colspan="6" class="loading-state" style="color:var(--color-error)">Error cargando historial</td></tr>'; }
  }

  function renderHistoryCharts(stats) {
    const labels = stats.map(s => s.scraper_id);
    const successData = stats.map(s => s.success_count || 0);
    const errorData = stats.map(s => s.error_count || 0);
    const durationData = stats.map(s => s.avg_duration_ms ? Math.round(s.avg_duration_ms) : 0);

    if (historyChart) historyChart.destroy();
    if (durationChart) durationChart.destroy();

    const c1 = document.getElementById("chart-scraper-status").getContext("2d");
    historyChart = new Chart(c1, {
      type: "bar",
      data: { labels, datasets: [
        { label: "Éxitos", data: successData, backgroundColor: "rgba(16,185,129,0.7)", borderColor: "#10b981", borderWidth: 1 },
        { label: "Errores", data: errorData, backgroundColor: "rgba(244,63,94,0.7)", borderColor: "#f43f5e", borderWidth: 1 }
      ]},
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { labels: { color: "#94a3b8", font: { family: "Outfit" } } } }, scales: { x: { ticks: { color: "#94a3b8" }, grid: { color: "rgba(255,255,255,0.03)" } }, y: { beginAtZero: true, ticks: { color: "#94a3b8" }, grid: { color: "rgba(255,255,255,0.05)" } } } }
    });

    const colors = ["#10b981","#f43f5e","#6366f1","#f59e0b","#3b82f6","#8b5cf6","#ec4899"];
    const c2 = document.getElementById("chart-avg-duration").getContext("2d");
    durationChart = new Chart(c2, {
      type: "bar",
      data: { labels, datasets: [{ label: "Duración promedio (ms)", data: durationData, backgroundColor: labels.map((_,i) => colors[i%colors.length]+"b3"), borderColor: labels.map((_,i) => colors[i%colors.length]), borderWidth: 1 }] },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { labels: { color: "#94a3b8", font: { family: "Outfit" } } } }, scales: { x: { ticks: { color: "#94a3b8" }, grid: { color: "rgba(255,255,255,0.03)" } }, y: { beginAtZero: true, ticks: { color: "#94a3b8" }, grid: { color: "rgba(255,255,255,0.05)" } } } }
    });
  }

  document.getElementById("btn-refresh-history").addEventListener("click", loadHistory);
  document.getElementById("history-scraper-filter").addEventListener("change", async e => {
    const val = e.target.value;
    const url = val ? `/api/history?scraper_id=${encodeURIComponent(val)}&limit=100` : "/api/history?limit=100";
    try {
      const res = await fetch(url);
      renderHistoryTable(await res.json());
    } catch {}
  });

  function renderHistoryTable(rows) {
    const tbody = document.getElementById("history-tbody");
    tbody.innerHTML = rows.length ? rows.map(r => {
      const dur = r.duration_ms ? (r.duration_ms >= 1000 ? (r.duration_ms/1000).toFixed(1)+"s" : r.duration_ms+"ms") : "—";
      return `<tr>
        <td><strong>${r.scraper_id}</strong></td>
        <td>${r.started_at ? new Date(r.started_at).toLocaleString() : "—"}</td>
        <td>${dur}</td>
        <td><span class="${r.status === "success" ? "status-ok" : "status-fail"}">${r.status === "success" ? "✅ Éxito" : "❌ Error"}</span></td>
        <td>${r.records_count != null ? r.records_count : "—"}</td>
        <td>${r.sandbox ? '<span class="badge-sandbox">🧪 Sandbox</span>' : "—"}</td>
      </tr>`;
    }).join("") : '<tr><td colspan="6" class="loading-state" style="padding:24px">Sin ejecuciones registradas</td></tr>';
  }

  // ── Config ──
  window.saveCredential = function(service) {
    const input = document.getElementById("cred-" + service);
    const val = input.value.trim();
    if (!val) return;
    input.value = "";
    input.placeholder = "✅ Guardado (local)";
    try { localStorage.setItem("scrapycoco_cred_" + service, btoa(val)); } catch {}
  };

  window.saveProxies = function() {
    const el = document.getElementById("proxy-list");
    localStorage.setItem("scrapycoco_proxies", el.value);
    el.placeholder = "✅ Guardado";
  };

  document.getElementById("proxy-list").value = localStorage.getItem("scrapycoco_proxies") || "";
  ["fbref", "supabase", "sportmonks"].forEach(s => {
    try {
      const v = localStorage.getItem("scrapycoco_cred_" + s);
      if (v) document.getElementById("cred-" + s).placeholder = "🔒 Guardado";
    } catch {}
  });

  // ── Validation Panel ──
  let validationWarnings = [];

  function showValidationPanel(warnings) {
    validationWarnings = warnings;
    const panel = document.getElementById("validation-panel");
    const body = document.getElementById("validation-panel-body");
    const badge = document.getElementById("validation-badge");
    badge.textContent = warnings.length;
    if (!warnings.length) {
      body.innerHTML = '<p class="validation-empty">Sin advertencias</p>';
      panel.style.display = "none";
      return;
    }
    body.innerHTML = warnings.map((w, i) => `
      <div class="validation-item severity-${w.severity}">
        <div class="validation-item-header">
          <span class="validation-severity">${w.severity === "error" ? "❌" : "⚠️"}</span>
          <span class="validation-field">${w.field || "General"}</span>
          <span class="validation-row">Fila ${w.row + 1}</span>
        </div>
        <p class="validation-msg">${w.message}</p>
        ${w.suggestion ? `<div class="validation-suggestion">
          <input type="text" class="validation-input" value="${w.value || ""}" data-idx="${i}">
          <button class="btn btn-primary btn-sm" onclick="applyValidationFix(${i})">Corregir</button>
        </div>` : ""}
      </div>
    `).join("");
    panel.style.display = "flex";
  }

  window.closeValidationPanel = function() {
    document.getElementById("validation-panel").style.display = "none";
  };

  window.applyValidationFix = function(idx) {
    const w = validationWarnings[idx];
    if (!w) return;
    const input = document.querySelector(`.validation-input[data-idx="${idx}"]`);
    if (!input) return;
    const newVal = input.value.trim();
    if (previewData && w.row !== undefined && w.field && previewData.rows[w.row]) {
      previewData.rows[w.row][w.field] = newVal;
      renderPreviewTable(previewData);
    }
    validationWarnings.splice(idx, 1);
    showValidationPanel(validationWarnings);
    appendLog(`[Éxito] Corrección aplicada: ${w.field} → "${newVal}"`, "success");
  };

  // ── Scheduler ──
  let flatpickrInstance = null;

  window.showSchedulerForm = function() {
    document.getElementById("scheduler-modal-title").textContent = "Nueva Tarea Programada";
    document.getElementById("sched-cron").value = "";
    document.getElementById("sched-sandbox").checked = false;
    const sel = document.getElementById("sched-scraper");
    sel.innerHTML = "";
    fetch("/api/scrapers").then(r => r.json()).then(scrapers => {
      scrapers.forEach(s => {
        const opt = document.createElement("option");
        opt.value = s.id; opt.textContent = s.name;
        sel.appendChild(opt);
      });
    }).catch(() => {});
    document.getElementById("scheduler-modal").style.display = "flex";
    if (flatpickrInstance) flatpickrInstance.destroy();
    flatpickrInstance = flatpickr("#sched-datetime", {
      enableTime: true,
      dateFormat: "Y-m-d H:i",
      minDate: "today",
      time_24hr: true,
      onChange: function(selectedDates) {
        if (selectedDates.length) {
          const d = selectedDates[0];
          const cron = `${d.getMinutes()} ${d.getHours()} ${d.getDate()} ${d.getMonth() + 1} *`;
          document.getElementById("sched-cron").value = cron;
        }
      }
    });
  };

  window.closeSchedulerForm = function() {
    document.getElementById("scheduler-modal").style.display = "none";
    if (flatpickrInstance) { flatpickrInstance.destroy(); flatpickrInstance = null; }
  };

  window.saveSchedulerJob = async function() {
    const scraperId = document.getElementById("sched-scraper").value;
    const cron = document.getElementById("sched-cron").value.trim();
    if (!scraperId || !cron) { appendLog("[Error] Completa todos los campos", "error"); return; }
    try {
      const res = await fetch("/api/scheduler/add", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          scraper_id: scraperId,
          cron_expression: cron,
          params: { sandbox: document.getElementById("sched-sandbox").checked }
        })
      });
      if (!res.ok) throw new Error(res.statusText);
      appendLog(`[Éxito] Tarea programada: ${scraperId} (${cron})`, "success");
      closeSchedulerForm();
      loadSchedulerJobs();
    } catch (err) {
      appendLog("[Error] Error al programar: " + err.message, "error");
    }
  };

  async function loadSchedulerJobs() {
    const container = document.getElementById("scheduler-list");
    try {
      const res = await fetch("/api/scheduler/list");
      const jobs = await res.json();
      if (!jobs.length) {
        container.innerHTML = '<div class="loading-state" style="padding:40px">Sin tareas programadas. Crea una nueva.</div>';
        return;
      }
      container.innerHTML = jobs.map(j => {
        const nextRun = j.next_run_time ? new Date(j.next_run_time).toLocaleString() : "—";
        const lastRun = j.last_run_at ? new Date(j.last_run_at).toLocaleString() : "Nunca";
        const enabled = j.enabled === 1;
        return `<div class="scheduler-item ${enabled ? "" : "paused"}">
          <div class="scheduler-item-info">
            <strong>${j.scraper_id}</strong>
            <span class="scheduler-cron">${j.cron_expression}</span>
            <span class="scheduler-meta">Creado: ${new Date(j.created_at).toLocaleString()}</span>
            <span class="scheduler-meta">Última ejec: ${lastRun}</span>
            <span class="scheduler-meta">Próxima: ${nextRun}</span>
          </div>
          <div class="scheduler-item-actions">
            <span class="scheduler-status ${enabled ? "active" : "paused"}">${enabled ? "Activo" : "Pausado"}</span>
            <button class="btn btn-secondary btn-sm" onclick="schedulerRunNow(${j.id})">Ejecutar</button>
            ${enabled
              ? `<button class="btn btn-secondary btn-sm" onclick="schedulerPause(${j.id})">Pausar</button>`
              : `<button class="btn btn-secondary btn-sm" onclick="schedulerResume(${j.id})">Reanudar</button>`}
            <button class="btn btn-secondary btn-sm" onclick="schedulerDelete(${j.id})">Eliminar</button>
          </div>
        </div>`;
      }).join("");
    } catch {
      container.innerHTML = '<div class="loading-state" style="color:var(--color-error)">Error cargando tareas</div>';
    }
  }

  window.schedulerDelete = async function(id) {
    if (!confirm("¿Eliminar esta tarea programada?")) return;
    try {
      await fetch(`/api/scheduler/${id}`, { method: "DELETE" });
      appendLog("[Info] Tarea eliminada", "info");
      loadSchedulerJobs();
    } catch {}
  };

  window.schedulerPause = async function(id) {
    try {
      await fetch(`/api/scheduler/${id}/pause`, { method: "POST" });
      loadSchedulerJobs();
    } catch {}
  };

  window.schedulerResume = async function(id) {
    try {
      await fetch(`/api/scheduler/${id}/resume`, { method: "POST" });
      loadSchedulerJobs();
    } catch {}
  };

  window.schedulerRunNow = async function(id) {
    try {
      const res = await fetch(`/api/scheduler/${id}/run-now`, { method: "POST" });
      const data = await res.json();
      appendLog(`[Ejecución] Ejecución manual: ${data.status} (exit: ${data.exit_code})`, data.status === "success" ? "success" : "error");
      loadSchedulerJobs();
    } catch {}
  };

  // ── Diagnostic ──
  let diagnosticScraperId = null;

  window.openDiagnostic = async function(scraperId) {
    diagnosticScraperId = scraperId;
    document.getElementById("diagnostic-modal-title").textContent = `🔍 Diagnóstico: ${scraperId}`;
    document.getElementById("diagnostic-tree").innerHTML = '<div class="loading-state">Cargando...</div>';
    document.getElementById("diagnostic-summary").innerHTML = "";
    document.getElementById("diagnostic-history-list").innerHTML = "";
    document.getElementById("diagnostic-modal").style.display = "flex";
    try {
      const res = await fetch(`/api/diagnostic/run/${scraperId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: "" })
      });
      const data = await res.json();
      renderDiagnostic(data);
    } catch {
      document.getElementById("diagnostic-tree").innerHTML = '<div class="loading-state" style="color:var(--color-error)">Error ejecutando diagnóstico</div>';
    }
    loadDiagnosticHistory(scraperId);
  };

  window.closeDiagnosticModal = function() {
    document.getElementById("diagnostic-modal").style.display = "none";
    diagnosticScraperId = null;
  };

  window.runDiagnostic = function() {
    if (diagnosticScraperId) window.openDiagnostic(diagnosticScraperId);
  };

  function renderDiagnostic(data) {
    const summary = document.getElementById("diagnostic-summary");
    const tree = document.getElementById("diagnostic-tree");

    if (data.has_changes) {
      const sev = data.severity === "critical" ? "🔴" : data.severity === "warning" ? "🟡" : "🔵";
      summary.innerHTML = `<div class="diagnostic-summary-bar severity-${data.severity}">
        ${sev} Se detectaron cambios en la estructura (${data.severity}) — ${data.changes.length} cambios
      </div>`;
    } else {
      summary.innerHTML = '<div class="diagnostic-summary-bar severity-none">✅ Sin cambios detectados</div>';
    }

    let html = '<div class="diagnostic-section"><h4>📋 Estructura Detectada</h4>';
    html += `<p>Tablas: ${data.table_count || 0} | Pestañas: ${(data.tab_labels || []).join(", ") || "ninguna"}</p>`;
    html += '</div>';

    if (data.changes && data.changes.length) {
      html += '<div class="diagnostic-section"><h4>🔄 Cambios Detectados</h4><ul class="diagnostic-changes">';
      data.changes.forEach(c => {
        const icon = c.severity === "critical" ? "🔴" : c.severity === "warning" ? "🟡" : "🔵";
        html += `<li class="change-${c.severity}">${icon} <strong>${c.type}</strong>: ${c.selector} → ${c.new || c.old || ""}</li>`;
      });
      html += '</ul></div>';
    }

    if (data.class_hashes && Object.keys(data.class_hashes).length) {
      html += '<div class="diagnostic-section"><h4>🏷️ Class Hashes</h4><div class="hash-grid">';
      for (const [base, cls] of Object.entries(data.class_hashes)) {
        html += `<span class="hash-item" title="${cls}">${base}<span class="hash-suffix">_${cls.split("_").pop()}</span></span>`;
      }
      html += '</div></div>';
    }

    tree.innerHTML = html;
  }

  async function loadDiagnosticHistory(scraperId) {
    const container = document.getElementById("diagnostic-history-list");
    try {
      const res = await fetch(`/api/diagnostic/history/${scraperId}`);
      const snapshots = await res.json();
      if (!snapshots.length) {
        container.innerHTML = '<p class="validation-empty">Sin historial de snapshots</p>';
        return;
      }
      container.innerHTML = snapshots.map(s => {
        const d = new Date(s.created_at);
        const hash = s.html_hash ? s.html_hash.slice(0, 8) : "—";
        return `<div class="history-snapshot" onclick="compareSnapshots(${snapshots[0].id}, ${s.id})">
          <span class="snapshot-date">${d.toLocaleString()}</span>
          <span class="snapshot-hash">${hash}</span>
          ${s.url ? `<span class="snapshot-url">${s.url}</span>` : ""}
        </div>`;
      }).join("");
    } catch {
      container.innerHTML = '<p class="validation-empty">Error cargando historial</p>';
    }
  }

  window.compareSnapshots = async function(id1, id2) {
    try {
      const res = await fetch(`/api/diagnostic/compare/${id1}/${id2}`);
      const data = await res.json();
      renderDiagnostic(data);
    } catch {}
  };

  // ── Update tab system for scheduler ──
  const origTabHandler = document.querySelectorAll(".tab-btn");
  origTabHandler.forEach(btn => {
    btn.removeEventListener("click", () => {});
  });

  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
      btn.classList.add("active");
      const tab = document.getElementById("tab-" + btn.dataset.tab);
      if (tab) {
        tab.classList.add("active");
        if (btn.dataset.tab === "history") loadHistory();
        if (btn.dataset.tab === "scheduler") loadSchedulerJobs();
      }
    });
  });

  // ── Wire validation warnings from SSE ──
  // Patch startScraper to capture validation-error events
  const origStartScraper = startScraper;
  startScraper = function(scraperId) {
    const warnings = [];
    if (activeEventSource) activeEventSource.close();
    appendLog(`[Sistema] Iniciando scraper: "${scraperId}"...`, "system");
    document.querySelectorAll(".btn-run").forEach(b => b.disabled = true);
    const sandbox = chkSandbox.checked;
    let params = [];
    const mid = document.getElementById("custom-match-id").value;
    const tn = document.getElementById("custom-team-name").value;
    if (mid && mid.trim()) params.push("match_id=" + encodeURIComponent(mid.trim()));
    if (tn && tn.trim()) params.push("team_name=" + encodeURIComponent(tn.trim()));
    if (sandbox) params.push("sandbox=true");
    const qs = params.length ? "?" + params.join("&") : "";
    activeEventSource = new EventSource(`/api/run/${scraperId}${qs}`);
    runningScraperId = scraperId;

    activeEventSource.addEventListener("start", e => {
      try { appendLog(JSON.parse(e.data).message, "system"); } catch { appendLog(e.data, "system"); }
      loadScrapers();
    });
    activeEventSource.addEventListener("log", e => {
      try {
        const d = JSON.parse(e.data);
        const type = getLogLevel(d);
        appendLog((type === "error" ? "[Error] " : type === "warning" ? "[Advertencia] " : type === "success" ? "[Éxito] " : "") + d.message, type);
      } catch { appendLog(e.data); }
    });
    activeEventSource.addEventListener("validation-error", e => {
      try {
        const d = JSON.parse(e.data);
        warnings.push(d);
        showValidationPanel(warnings);
      } catch {}
    });
    activeEventSource.onmessage = e => appendLog(e.data);
    activeEventSource.addEventListener("end", e => {
      try {
        const d = JSON.parse(e.data);
        appendLog(d.message, d.level === "error" ? "error" : "success");
      } catch { appendLog(e.data, "success"); }
      cleanup();
    });
    activeEventSource.onerror = () => { appendLog("[Error] Conexión interrumpida.", "error"); cleanup(); };
    function cleanup() { if (activeEventSource) { activeEventSource.close(); activeEventSource = null; } runningScraperId = null; loadScrapers(); }
  };

  // ── Init ──
  loadScrapers();
  setInterval(loadScrapers, 5000);
});
