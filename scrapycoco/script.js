// ─── STATE ───────────────────────────────────────────────
const API_BASE = '/api';
const WS_BASE = API_BASE.replace('/api', '').replace('http', 'ws') + '/ws';

const APP_STATE = {
  theme: localStorage.getItem('scrapycoco-theme') || 'light',
  sidebarCollapsed: false,
  scrapers: [],
  jobs: [],
  selectedScrapers: new Set(),
  batchActive: false,
  charts: {},
  logs: [],
  activeTab: 'dashboard',
  autoScroll: true,
};

// ─── INIT ───────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', initApp);

async function initApp() {
  applyTheme(APP_STATE.theme);
  initTabs();
  initConsole();
  initThemeToggle();
  initSidebar();
  initBatchRunButton();
  initTransformCheckboxSync();
  loadDashboard();
  loadScrapers();
  loadHistory();
  loadSchedulerJobs();
  loadScraperFilter();
}

// ─── THEME ──────────────────────────────────────────────
function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  APP_STATE.theme = theme;
  localStorage.setItem('scrapycoco-theme', theme);
  document.querySelector('.sun-icon').style.display = theme === 'dark' ? 'none' : '';
  document.querySelector('.moon-icon').style.display = theme === 'dark' ? '' : 'none';
}

function toggleTheme() {
  applyTheme(APP_STATE.theme === 'light' ? 'dark' : 'light');
  Object.values(APP_STATE.charts).forEach(c => {
    if (c && c.update) c.update('none');
  });
}

function initThemeToggle() {
  document.getElementById('theme-toggle').addEventListener('click', toggleTheme);
}

// ─── SIDEBAR ────────────────────────────────────────────
function initSidebar() {
  const sidebar = document.getElementById('sidebar');
  const toggleBtn = document.getElementById('sidebar-toggle');
  const mobileBtn = document.getElementById('mobile-menu-btn');
  const overlay = document.getElementById('mobile-overlay');

  toggleBtn.addEventListener('click', () => {
    APP_STATE.sidebarCollapsed = !APP_STATE.sidebarCollapsed;
    sidebar.classList.toggle('collapsed', APP_STATE.sidebarCollapsed);
  });

  mobileBtn.addEventListener('click', () => {
    sidebar.classList.add('mobile-open');
    overlay.style.display = 'block';
    document.body.style.overflow = 'hidden';
  });
}

function closeMobileSidebar() {
  document.getElementById('sidebar').classList.remove('mobile-open');
  document.getElementById('mobile-overlay').style.display = 'none';
  document.body.style.overflow = '';
}

// ─── TABS ───────────────────────────────────────────────
function initTabs() {
  document.querySelectorAll('.nav-item[data-tab]').forEach(btn => {
    btn.addEventListener('click', () => {
      const tab = btn.dataset.tab;
      switchTab(tab);
      if (window.innerWidth <= 768) {
        closeMobileSidebar();
      }
    });
  });
}

function switchTab(tab) {
  APP_STATE.activeTab = tab;
  document.querySelectorAll('.nav-item[data-tab]').forEach(b => b.classList.remove('active'));
  document.querySelector(`.nav-item[data-tab="${tab}"]`)?.classList.add('active');
  document.querySelectorAll('.tab-content').forEach(s => s.classList.remove('active'));
  const section = document.getElementById(`tab-${tab}`);
  if (section) section.classList.add('active');
  document.getElementById('breadcrumb-current').textContent =
    document.querySelector(`.nav-item[data-tab="${tab}"] .nav-item-text`)?.textContent || tab;
}

// ─── API HELPERS ────────────────────────────────────────
async function apiGet(path) {
  const r = await fetch(`${API_BASE}${path}`);
  if (!r.ok) throw new Error(`GET ${path} -> ${r.status}`);
  return r.json();
}

async function apiPost(path, body) {
  const r = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!r.ok) throw new Error(`POST ${path} -> ${r.status}`);
  return r.json();
}

// ─── DASHBOARD ──────────────────────────────────────────
async function loadDashboard() {
  try {
    document.getElementById('dashboard-kpis').querySelectorAll('.kpi-value').forEach(el => el.textContent = '-');
    const [health, metrics, stats] = await Promise.all([
      apiGet('/health').catch(() => ({ status: 'unhealthy', uptime: 0, version: '?' })),
      apiGet('/history/metrics').catch(() => ({ total_runs: 0, success_count: 0, error_count: 0, avg_duration_ms: null, total_records: 0 })),
      apiGet('/history/stats').catch(() => []),
    ]);
    updateDashboardKPIs(metrics, health);
    renderDashboardCharts(stats || []);
    updateServerStatus(health);
  } catch (e) {
    addLog('error', `Dashboard: ${e.message}`);
    document.getElementById('dashboard-kpis').querySelectorAll('.kpi-value').forEach(el => el.textContent = 'Error');
  }
}

function updateDashboardKPIs(metrics, health) {
  document.getElementById('kpi-total-runs').textContent = metrics.total_runs ?? 0;
  document.getElementById('kpi-success-rate').textContent = metrics.total_runs
    ? `${((metrics.success_count / metrics.total_runs) * 100).toFixed(0)}%` : '0%';
  document.getElementById('kpi-avg-duration').textContent = metrics.avg_duration_ms != null
    ? `${metrics.avg_duration_ms.toFixed(0)}ms` : '—';
  document.getElementById('kpi-total-records').textContent = metrics.total_records ?? 0;
}

function renderDashboardCharts(stats) {
  const scraperNames = stats.map(s => s.scraper_id || 'unknown');

  const statusCtx = document.getElementById('chart-scraper-status');
  if (!statusCtx) return;

  if (APP_STATE.charts.statusChart) { APP_STATE.charts.statusChart.destroy(); }
  APP_STATE.charts.statusChart = new Chart(statusCtx, {
    type: 'bar',
    data: {
      labels: scraperNames,
      datasets: [
        { label: 'Exito', data: stats.map(s => s.success_count || 0), backgroundColor: '#10b981', borderRadius: 4 },
        { label: 'Fallos', data: stats.map(s => s.error_count || 0), backgroundColor: '#ef4444', borderRadius: 4 },
      ],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { position: 'top', labels: { boxWidth: 12, padding: 8, font: { size: 11 } } } },
      scales: {
        x: { grid: { display: false }, ticks: { font: { size: 10 } } },
        y: { beginAtZero: true, ticks: { stepSize: 1, font: { size: 10 } } },
      },
    },
  });

  const durCtx = document.getElementById('chart-avg-duration');
  if (!durCtx) return;

  if (APP_STATE.charts.durationChart) { APP_STATE.charts.durationChart.destroy(); }
  APP_STATE.charts.durationChart = new Chart(durCtx, {
    type: 'bar',
    data: {
      labels: scraperNames,
      datasets: [{ label: 'Duracion prom. (ms)', data: stats.map(s => s.avg_duration_ms || 0), backgroundColor: '#3b82f6', borderRadius: 4 }],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { display: false }, ticks: { font: { size: 10 } } },
        y: { beginAtZero: true, ticks: { font: { size: 10 }, callback: v => v + 'ms' } },
      },
    },
  });
}

// ─── SCRAPERS ───────────────────────────────────────────
async function loadScrapers() {
  try {
    const data = await apiGet('/scrapers');
    APP_STATE.scrapers = data || [];
    renderScrapers();
    document.getElementById('nav-scrapers-count').textContent = APP_STATE.scrapers.length;
  } catch (e) {
    addLog('error', `Scrapers: ${e.message}`);
    document.getElementById('scrapers-grid').innerHTML =
      `<div class="empty-state"><svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="var(--text-tertiary)" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg><p>Error al cargar scrapers</p></div>`;
  }
}

function renderScrapers() {
  const grid = document.getElementById('scrapers-grid');
  if (!APP_STATE.scrapers.length) {
    grid.innerHTML = `<div class="empty-state"><svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="var(--text-tertiary)" stroke-width="1.5"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg><p>No se encontraron scrapers registrados</p></div>`;
    return;
  }
  grid.innerHTML = APP_STATE.scrapers.map(s => renderScraperCard(s)).join('');
  APP_STATE.scrapers.forEach(s => {
    const sid = s.id || s.name;
    const cb = document.getElementById(`sel-${sid}`);
    if (cb) cb.addEventListener('change', () => toggleScraperSelection(sid));
  });
}

function renderScraperCard(s) {
  const id = s.id || s.name || s;
  const name = s.name || s;
  const desc = s.description || s.desc || '';
  const status = s.status || 'idle';
  const selected = APP_STATE.selectedScrapers.has(id);
  const isIdle = status === 'idle' || status === 'done';
  return `<div class="scraper-card${selected ? ' selected' : ''}${isIdle ? '' : ' disabled'}">
    <div class="scraper-card-left">
      <input type="checkbox" id="sel-${id}" ${selected ? 'checked' : ''} ${isIdle ? '' : 'disabled'} class="scraper-checkbox">
      <div class="scraper-card-info">
        <div class="scraper-card-name">
          <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="var(--clr-primary-500)" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
          ${name}
        </div>
        <div class="scraper-card-desc">${desc || 'Sin descripcion'}</div>
      </div>
    </div>
    <div class="scraper-card-actions">
      <span class="status-badge ${status === 'running' ? 'neutral' : status === 'error' ? 'error' : 'success'}">${status}</span>
      <button class="btn btn-primary btn-sm" onclick="runScraper('${id}')" ${isIdle ? '' : 'disabled'}>
        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg>
        Ejecutar
      </button>
    </div>
  </div>`;
}

function toggleScraperSelection(id) {
  if (APP_STATE.selectedScrapers.has(id)) {
    APP_STATE.selectedScrapers.delete(id);
  } else {
    APP_STATE.selectedScrapers.add(id);
  }
  document.getElementById('batch-count').textContent = `${APP_STATE.selectedScrapers.size} seleccionados`;
  document.getElementById('btn-batch-run').disabled = APP_STATE.selectedScrapers.size === 0;
  renderScrapers();
}

function initBatchRunButton() {
  document.getElementById('btn-batch-run').addEventListener('click', runBatch);
}

async function runBatch() {
  if (APP_STATE.batchActive) return;
  APP_STATE.batchActive = true;
  const ids = [...APP_STATE.selectedScrapers];
  showBatchProgress(ids.length);

  const isSandbox = document.getElementById('chk-sandbox').checked;
  const matchId = document.getElementById('custom-match-id').value.trim() || undefined;
  const teamName = document.getElementById('custom-team-name').value.trim() || undefined;

  addLog('info', `Lote iniciado: ${ids.length} scrapers`);
  try {
    const resp = await fetch(`${API_BASE}/batch/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scraper_ids: ids, sandbox: isSandbox, match_id: matchId, team_name: teamName }),
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const ev = JSON.parse(line.slice(6));
            if (ev.message) addLog(ev.level || 'info', ev.message);
            if (ev.total && ev.completed !== undefined) {
              updateBatchProgress(ev.completed, ev.total, ev.current_scraper ? `${ev.current_scraper} (${ev.completed}/${ev.total})` : `${ev.completed}/${ev.total}`);
            }
          } catch (e) { /* skip parse errors */ }
        }
      }
    }
  } catch (e) {
    addLog('error', `Batch: ${e.message}`);
  }
  hideBatchProgress();
  APP_STATE.batchActive = false;
  addLog('success', 'Lote finalizado');
  loadHistory();
  loadDashboard();
}

async function runScraper(id) {
  const isSandbox = document.getElementById('chk-sandbox')?.checked || false;
  const matchId = document.getElementById('custom-match-id')?.value.trim() || undefined;
  const teamName = document.getElementById('custom-team-name')?.value.trim() || undefined;
  addLog('info', `[${id}] Iniciando...`);
  showBatchProgress(1);
  updateBatchProgress(0, 1, `Ejecutando ${id}...`);
  try {
    const params = new URLSearchParams({ sandbox: isSandbox });
    if (matchId) params.set('match_id', matchId);
    if (teamName) params.set('team_name', teamName);
    const resp = await fetch(`${API_BASE}/run/${id}?${params}`, { method: 'GET' });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const ev = JSON.parse(line.slice(6));
            if (ev.message) addLog(ev.level || 'info', `[${id}] ${ev.message}`);
          } catch (e) { /* skip */ }
        }
      }
    }
  } catch (e) {
    addLog('error', `[${id}] Error: ${e.message}`);
    showToast(`Error en ${id}: ${e.message}`, 'error');
  }
  hideBatchProgress();
  showToast(`${id} completado`, 'success');
  loadHistory();
  loadDashboard();
}

// ─── BATCH PROGRESS ─────────────────────────────────────
function showBatchProgress(total) {
  const el = document.getElementById('batch-progress');
  el.style.display = 'flex';
  document.getElementById('batch-progress-fill').style.width = '0%';
  document.getElementById('batch-progress-text').textContent = `0/${total} iniciado`;
}

function updateBatchProgress(current, total, text) {
  const pct = total > 0 ? (current / total) * 100 : 0;
  document.getElementById('batch-progress-fill').style.width = `${pct}%`;
  document.getElementById('batch-progress-text').textContent = text || `${current}/${total}`;
}

function hideBatchProgress() {
  document.getElementById('batch-progress').style.display = 'none';
}

// ─── VALIDATION PANEL ────────────────────────────────────
function showValidationPanel(warnings) {
  const panel = document.getElementById('validation-panel');
  panel.style.display = 'block';
  document.getElementById('validation-badge').textContent = warnings.length;
  document.getElementById('validation-panel-body').innerHTML = warnings.map(w =>
    `<div style="display:flex;align-items:center;gap:var(--space-2);padding:var(--space-2) 0;border-bottom:1px solid var(--border-color);font-size:var(--fs-sm)"><span class="status-badge warning">${w.type || 'warning'}</span><span>${w.message || w}</span></div>`
  ).join('');
  addLog('warning', `${warnings.length} advertencias de validacion`);
}

function closeValidationPanel() {
  document.getElementById('validation-panel').style.display = 'none';
}

// ─── HISTORY ────────────────────────────────────────────
async function loadHistory() {
  try {
    const [jobs, metrics] = await Promise.all([
      apiGet('/history').catch(() => []),
      apiGet('/history/metrics').catch(() => ({ total_runs: 0, success_count: 0, error_count: 0, avg_duration_ms: null, total_records: 0 })),
    ]);
    APP_STATE.jobs = jobs || [];
    renderHistoryMetrics(metrics);
    renderHistoryTable(filterHistoryByScraper(jobs || []));
  } catch (e) {
    addLog('error', `Historial: ${e.message}`);
  }
}

async function loadScraperFilter() {
  try {
    const data = await apiGet('/scrapers');
    const items = data || [];
    const sel = document.getElementById('history-scraper-filter');
    sel.innerHTML = '<option value="">Todos los scrapers</option>' + items.map(s => `<option value="${s.id}">${s.name}</option>`).join('');
    sel.addEventListener('change', () => {
      renderHistoryTable(filterHistoryByScraper(APP_STATE.jobs));
    });
  } catch (e) { /* ignore */ }
}

function filterHistoryByScraper(jobs) {
  const filter = document.getElementById('history-scraper-filter')?.value;
  if (!filter) return jobs;
  return jobs.filter(j => j.scraper_id === filter);
}

function renderHistoryMetrics(metrics) {
  document.getElementById('metric-total').textContent = metrics.total_runs ?? 0;
  document.getElementById('metric-success-rate').textContent = metrics.total_runs
    ? `${((metrics.success_count / metrics.total_runs) * 100).toFixed(0)}%` : '0%';
  document.getElementById('metric-avg-duration').textContent = metrics.avg_duration_ms != null
    ? `${metrics.avg_duration_ms.toFixed(0)}ms` : '0ms';
  document.getElementById('metric-records').textContent = metrics.total_records ?? 0;
}

function renderHistoryTable(entries) {
  const tbody = document.getElementById('history-tbody');
  if (!entries.length) {
    tbody.innerHTML = `<tr><td colspan="7" class="empty-state"><p>Sin ejecuciones registradas</p></td></tr>`;
    return;
  }
  tbody.innerHTML = entries.slice(0, 100).map(j => {
    const id = j.scraper_id || 'unknown';
    const status = j.status || 'pending';
    const records = j.records_count || 0;
    const started = j.started_at || '';
    const duration = j.duration_ms != null ? j.duration_ms : '—';
    const sandbox = j.sandbox ? `<span class="status-badge warning">Sandbox</span>` : '—';
    const badgeClass = status === 'success' ? 'success' : status === 'running' || status === 'pending' ? 'neutral' : 'error';
    return `<tr>
      <td><span class="badge badge-ghost">${id}</span></td>
      <td style="font-size:var(--fs-sm);color:var(--text-secondary)">${started ? new Date(started).toLocaleString() : '—'}</td>
      <td style="font-family:var(--font-mono);font-size:var(--fs-sm)">${duration}${duration !== '—' ? 'ms' : ''}</td>
      <td><span class="status-badge ${badgeClass}">${status}</span></td>
      <td style="font-family:var(--font-mono);font-size:var(--fs-sm)">${records}</td>
      <td>${sandbox}</td>
      <td>
        <button class="btn btn-ghost btn-sm" onclick="runScraper('${id}')" title="Re-ejecutar">
          <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
        </button>
        <button class="btn btn-ghost btn-sm" onclick="viewScraperDiagnostic('${id}')" title="Diagnostico">
          <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
        </button>
      </td>
    </tr>`;
  }).join('');
}

// ─── DIAGNOSTIC ─────────────────────────────────────────
function viewScraperDiagnostic(name) {
  document.getElementById('diagnostic-modal').style.display = 'flex';
  document.getElementById('diagnostic-modal-title').textContent = `Diagnostico: ${name}`;
  const summary = document.getElementById('diagnostic-summary');
  const tree = document.getElementById('diagnostic-tree');
  const historyList = document.getElementById('diagnostic-history-list');
  summary.innerHTML = `<div class="loading-state"><div class="spinner"></div><span>Cargando diagnostico...</span></div>`;
  tree.innerHTML = '';
  historyList.innerHTML = '';

  Promise.all([
    apiGet(`/diagnostic/run/${name}`).catch(() => null),
    apiGet(`/diagnostic/history/${name}`).catch(() => []),
  ]).then(([diag, snapshots]) => {
    if (diag) {
      summary.innerHTML = `
        <div class="kpi-grid" style="grid-template-columns:repeat(auto-fit,minmax(120px,1fr))">
          <div class="kpi-card"><span class="kpi-value">${diag.selector_count || 0}</span><span class="kpi-label">Selectores</span></div>
          <div class="kpi-card"><span class="kpi-value">${diag.active_selectors || 0}</span><span class="kpi-label">Activos</span></div>
          <div class="kpi-card"><span class="kpi-value">${diag.sample_count || 0}</span><span class="kpi-label">Muestras</span></div>
        </div>`;
      if (diag.sample_data && diag.sample_data.length) {
        tree.innerHTML = '<h4 style="font-size:var(--fs-sm);margin-bottom:var(--space-3);margin-top:var(--space-4)">Datos de Muestra</h4>' +
          renderSnapshotTree(diag.sample_data);
      }
    } else {
      summary.innerHTML = '<p style="color:var(--text-tertiary)">Sin datos de diagnostico</p>';
    }
    if (snapshots && snapshots.length) {
      historyList.innerHTML = snapshots.slice(0, 20).map(s =>
        `<div style="display:flex;justify-content:space-between;padding:var(--space-2);border-bottom:1px solid var(--border-color);font-size:var(--fs-sm)"><span>${new Date(s.timestamp || s.created_at || Date.now()).toLocaleString()}</span><span style="font-family:var(--font-mono);color:var(--text-secondary)">${s.records || s.items || 0} registros</span></div>`
      ).join('');
    } else {
      historyList.innerHTML = '<p style="color:var(--text-tertiary);font-size:var(--fs-sm)">Sin historial</p>';
    }
  }).catch(e => {
    summary.innerHTML = `<p style="color:var(--clr-red-500)">Error: ${e.message}</p>`;
  });
}

function renderSnapshotTree(items) {
  if (!items || !items.length) return '<p style="font-size:var(--fs-sm);color:var(--text-tertiary)">Sin datos en snapshot</p>';
  return `<ul style="list-style:none;padding:0;margin:0;font-size:var(--fs-sm);font-family:var(--font-mono)">${items.slice(0, 30).map(i =>
    `<li style="padding:var(--space-1) 0;border-bottom:1px solid var(--border-color);display:flex;justify-content:space-between"><span>${i.name || i.id || i.title || JSON.stringify(i).slice(0, 60)}</span><span style="color:var(--text-tertiary)">${i.league || i.competition || i.type || ''}</span></li>`
  ).join('')}</ul>`;
}

function closeDiagnosticModal() {
  document.getElementById('diagnostic-modal').style.display = 'none';
}

async function runDiagnostic() {
  const title = document.getElementById('diagnostic-modal-title').textContent;
  const name = title.replace('Diagnostico: ', '');
  addLog('info', `[${name}] Re-ejecutando diagnostico...`);
  viewScraperDiagnostic(name);
}

// ─── SCHEDULER ──────────────────────────────────────────
async function loadSchedulerJobs() {
  try {
    const data = await apiGet('/scheduler/list');
    renderSchedulerList(data || []);
  } catch (e) {
    addLog('warning', `Programador: ${e.message}`);
    document.getElementById('scheduler-list').innerHTML =
      `<div class="empty-state"><p>Programador no disponible</p></div>`;
  }
}

function renderSchedulerList(jobs) {
  const list = document.getElementById('scheduler-list');
  if (!jobs || !jobs.length) {
    list.innerHTML = `<div class="empty-state"><svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="var(--text-tertiary)" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg><p>Sin tareas programadas</p></div>`;
    return;
  }
  list.innerHTML = jobs.map(j =>
    `<div class="schedule-item">
      <div style="display:flex;align-items:center;gap:var(--space-3)">
        <span class="status-dot ${j.paused ? 'offline' : 'online'}"></span>
        <div>
          <div style="font-weight:600;font-size:var(--fs-sm)">${j.scraper_id || 'Sin nombre'}</div>
          <div style="font-size:var(--fs-xs);color:var(--text-tertiary);font-family:var(--font-mono);margin-top:var(--space-1)">${j.cron_expression || '—'}</div>
        </div>
      </div>
      <div style="display:flex;align-items:center;gap:var(--space-3)">
        <span class="status-badge ${j.paused ? 'neutral' : 'success'}">${j.paused ? 'Pausado' : 'Activo'}</span>
        <span style="font-size:var(--fs-xs);color:var(--text-tertiary)">${j.last_run || '—'}</span>
      </div>
    </div>`
  ).join('');
}

function showSchedulerForm() {
  const sel = document.getElementById('sched-scraper');
  sel.innerHTML = APP_STATE.scrapers.map(s => `<option value="${s.id}">${s.name}</option>`).join('');
  document.getElementById('scheduler-modal').style.display = 'flex';
}

function closeSchedulerForm() {
  document.getElementById('scheduler-modal').style.display = 'none';
}

async function saveSchedulerJob() {
  const scraperId = document.getElementById('sched-scraper').value;
  const cron = document.getElementById('sched-cron').value.trim();
  const sandbox = document.getElementById('sched-sandbox').checked;
  if (!cron) { showToast('Ingrese una expresion cron', 'error'); return; }
  try {
    await apiPost('/scheduler/add', { scraper_id: scraperId, cron_expression: cron, params: { sandbox } });
    showToast(`Tarea ${scraperId} creada`, 'success');
    closeSchedulerForm();
    loadSchedulerJobs();
  } catch (e) {
    showToast(`Error: ${e.message}`, 'error');
  }
}

// ─── SERVER STATUS ──────────────────────────────────────
function updateServerStatus(health) {
  const dot = document.getElementById('status-dot');
  const text = document.getElementById('status-text');
  if (health && (health.status === 'healthy' || health.status === 'ok')) {
    dot.className = 'status-dot online';
    text.textContent = `Conectado (${health.uptime ? formatUptime(health.uptime) : 'activo'})`;
  } else {
    dot.className = 'status-dot offline';
    text.textContent = 'Desconectado';
  }
}

function formatUptime(seconds) {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  return h ? `${h}h ${m}m` : `${m}m`;
}

// ─── CONSOLE ────────────────────────────────────────────
function initConsole() {
  const consoleOutput = document.getElementById('console-output');
  const drawer = document.getElementById('console-drawer');
  const autoScrollCheck = document.getElementById('chk-autoscroll');
  const clearBtn = document.getElementById('btn-clear-console');

  autoScrollCheck.addEventListener('change', () => {
    APP_STATE.autoScroll = autoScrollCheck.checked;
  });

  clearBtn.addEventListener('click', () => {
    APP_STATE.logs = [];
    consoleOutput.innerHTML = `<div class="console-line system-msg">[Sistema] Consola limpiada.</div>`;
  });

  // Log filter clicks
  document.querySelectorAll('.log-filter-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.log-filter-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      applyLogFilter();
    });
  });

  // Intercept console.log for streaming simulation
  consoleOutput.addEventListener('scroll', () => {
    const threshold = 20;
    const atBottom = consoleOutput.scrollHeight - consoleOutput.scrollTop - consoleOutput.clientHeight < threshold;
    if (!atBottom) APP_STATE.autoScroll = false;
    else APP_STATE.autoScroll = autoScrollCheck.checked;
  });
}

function addLog(level, message) {
  const entry = { level, message, timestamp: new Date().toISOString() };
  APP_STATE.logs.push(entry);
  renderLog(entry);
  updateConsoleBadge();
}

function renderLog(entry) {
  const output = document.getElementById('console-output');
  const levelMap = { info: 'log-info', warning: 'log-warning', error: 'log-error', success: 'log-success' };
  const line = document.createElement('div');
  line.className = `console-line ${levelMap[entry.level] || 'log-info'}`;
  const time = new Date(entry.timestamp).toLocaleTimeString();
  const levelLabel = entry.level.toUpperCase();
  line.textContent = `[${time}] [${levelLabel}] ${entry.message}`;
  output.appendChild(line);
  if (APP_STATE.autoScroll) {
    output.scrollTop = output.scrollHeight;
  }
}

function updateConsoleBadge() {
  const count = APP_STATE.logs.filter(l => l.level === 'error' || l.level === 'warning').length;
  // Optional: show count somewhere
}

function applyLogFilter() {
  const active = document.querySelector('.log-filter-btn.active');
  const level = active ? active.dataset.level : 'all';
  document.querySelectorAll('.console-line').forEach(line => {
    if (level === 'all') { line.style.display = ''; return; }
    const levelMap = { info: 'log-info', warning: 'log-warning', error: 'log-error', success: 'log-success' };
    const cls = levelMap[level];
    line.style.display = line.classList.contains(cls) || line.classList.contains('system-msg') ? '' : 'none';
  });
}

function toggleConsoleDrawer() {
  const drawer = document.getElementById('console-drawer');
  const isCollapsed = drawer.classList.toggle('collapsed');
  const btn = document.getElementById('console-drawer-header');
  if (btn) {
    btn.setAttribute('aria-expanded', !isCollapsed);
    const label = btn.querySelector('.console-toggle-btn');
    if (label) label.textContent = isCollapsed ? 'Ver Logs' : 'Ocultar';
  }
}

// ─── TOASTS ─────────────────────────────────────────────
function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  const colors = { info: 'var(--clr-blue-500)', success: 'var(--clr-green-500)', warning: 'var(--clr-amber-500)', error: 'var(--clr-red-500)' };
  const icons = {
    info: '<circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>',
    success: '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>',
    warning: '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>',
    error: '<circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>',
  };
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="${colors[type]}" stroke-width="2">${icons[type] || icons.info}</svg><span>${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.classList.add('toast-exit');
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// ─── PREVIEW & EXPORT ───────────────────────────────────
let previewData = [];

async function openPreviewModal(data) {
  previewData = data || [];
  document.getElementById('preview-modal').style.display = 'flex';
  document.getElementById('preview-count').textContent = `${data.length} registros`;
  if (!data.length) {
    document.getElementById('preview-thead').innerHTML = '';
    document.getElementById('preview-tbody').innerHTML = '<tr><td class="empty-state"><p>Sin datos</p></td></tr>';
    return;
  }
  const keys = Object.keys(data[0]).slice(0, 8);
  document.getElementById('preview-thead').innerHTML = `<tr>${keys.map(k => `<th>${k}</th>`).join('')}</tr>`;
  document.getElementById('preview-tbody').innerHTML = data.slice(0, 50).map(row =>
    `<tr>${keys.map(k => `<td style="font-size:var(--fs-xs);max-width:150px;overflow:hidden;text-overflow:ellipsis">${row[k] ?? '—'}</td>`).join('')}</tr>`
  ).join('');
}

function closePreviewModal(e) {
  if (e && e.target !== e.currentTarget) return;
  document.getElementById('preview-modal').style.display = 'none';
  previewData = [];
}

function exportFromPreview(format) {
  if (!previewData.length) { showToast('Sin datos para exportar', 'warning'); return; }
  downloadData(previewData, format || 'csv');
}

function showExportSubmodal() {
  // Sync transforms from main config
  document.querySelectorAll('.transform-check').forEach((cb, i) => {
    const sub = document.querySelectorAll('.sub-transform-check')[i];
    if (sub) sub.checked = cb.checked;
  });
  document.getElementById('export-submodal').style.display = 'flex';
}

function closeExportSubmodal() {
  document.getElementById('export-submodal').style.display = 'none';
}

function confirmExport() {
  const format = document.querySelector('input[name="sub-export-format"]:checked')?.value || 'csv';
  const transforms = [...document.querySelectorAll('.sub-transform-check:checked')].map(cb => cb.value);
  let data = [...previewData];
  // Apply transforms
  if (transforms.includes('normalize_teams')) data = data.map(r => ({ ...r, team: (r.team || '').toLowerCase().replace(/\s+/g, '_') }));
  if (transforms.includes('drop_empty')) data = data.filter(r => Object.values(r).some(v => v != null && v !== ''));
  downloadData(data, format);
  closeExportSubmodal();
}

function downloadData(data, format) {
  let content, mime, ext;
  if (format === 'json') {
    content = JSON.stringify(data, null, 2);
    mime = 'application/json';
    ext = 'json';
  } else if (format === 'xlsx') {
    showToast('Excel requiere libreria adicional. Descargando CSV.', 'warning');
    format = 'csv';
  }
  if (format === 'csv' || !ext) {
    const keys = Object.keys(data[0] || {});
    const rows = data.map(r => keys.map(k => {
      const v = r[k];
      return v == null ? '' : typeof v === 'string' && v.includes(',') ? `"${v}"` : v;
    }).join(','));
    content = [keys.join(','), ...rows].join('\n');
    mime = 'text/csv';
    ext = 'csv';
  }
  const blob = new Blob([content], { type: `${mime};charset=utf-8` });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `scrapycoco_export_${Date.now()}.${ext}`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
  showToast(`Exportado como ${ext.toUpperCase()}`, 'success');
}

// ─── CONFIG ─────────────────────────────────────────────
async function saveCredential(service) {
  const value = document.getElementById(`cred-${service}`).value.trim();
  if (!value) { showToast('Ingrese un valor', 'warning'); return; }
  try {
    await apiPost('/admin/credentials', { service, value });
    showToast(`${service} actualizada`, 'success');
    document.getElementById(`cred-${service}`).value = '';
  } catch (e) {
    showToast(`Error: ${e.message}`, 'error');
  }
}

async function saveProxies() {
  const text = document.getElementById('proxy-list').value.trim();
  const enabled = document.getElementById('chk-proxies-enabled').checked;
  const proxies = text.split('\n').filter(Boolean);
  if (enabled && !proxies.length) { showToast('Agregue al menos un proxy', 'warning'); return; }
  try {
    await apiPost('/admin/proxies', { proxies, enabled });
    showToast(`${proxies.length} proxies guardados`, 'success');
  } catch (e) {
    showToast(`Error: ${e.message}`, 'error');
  }
}

// ─── TRANSFORM CHECKBOX SYNC ────────────────────────────
function initTransformCheckboxSync() {
  // Sync main config checkboxes to submodal on open
  const origShow = showExportSubmodal;
  showExportSubmodal = function() {
    document.querySelectorAll('.transform-check').forEach((cb, i) => {
      const sub = document.querySelectorAll('.sub-transform-check')[i];
      if (sub) sub.checked = cb.checked;
    });
    origShow();
  };
}

// ─── SANDBOX TOGGLE VISUAL INDICATOR ────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const sandboxChk = document.getElementById('chk-sandbox');
  const indicator = document.getElementById('sandbox-indicator');
  if (sandboxChk && indicator) {
    sandboxChk.addEventListener('change', () => {
      indicator.style.display = sandboxChk.checked ? 'inline-flex' : 'none';
      addLog(sandboxChk.checked ? 'warning' : 'info', sandboxChk.checked ? 'Modo Sandbox activado' : 'Modo Sandbox desactivado');
    });
  }
});

// ─── ERROR BOUNDARY ─────────────────────────────────────
window.addEventListener('unhandledrejection', e => {
  addLog('error', `Error no manejado: ${e.reason?.message || e.reason || 'Desconocido'}`);
});

window.addEventListener('error', e => {
  addLog('error', `Error: ${e.message}`);
});
