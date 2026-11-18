/* Incident workflow. Independent review never receives predictions. */
const $ = (selector, root = document) => root.querySelector(selector);
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const shortCopy = value => value.trim().replace(/\.$/, '').replace(/\.\s+/g, ' · ');
const pct = value => value == null ? '—' : `${(value * 100).toFixed(1)}%`;
const storage = {
  get(key) {try {return localStorage.getItem(key);} catch {return null;}},
  set(key, value) {try {localStorage.setItem(key, value);} catch {}},
  remove(key) {try {localStorage.removeItem(key);} catch {}}
};
const state = {
  config: null, incidents: null, reviews: [], evidence: null, evidenceDataset: 'development', view: 'operations',
  method: storage.get('relay-method') === 'rules' ? 'rules' : 'learned',
  policy: storage.get('relay-policy') === 'standard' ? 'standard' : 'sensitive',
  filter: 'all', search: '', selected: null, mobileDetail: false, decisionDrafts: {}, pendingDecisions: new Set(),
  reviewIndex: 0,
  reviewer: storage.get('relay-reviewer') || '', reviewSource: 'quality'
};
let toastTimer, navigationVersion = 0, benchmarkVersion = 0, newPending = false;
let incidentRevision = 0;
const browserDemo = () => state.config?.storage === 'browser';
const demoStorageKey = 'relay-demo-incidents-v1';
const demoPredictions = new Map();

function readDemoState() {
  const raw = storage.get(demoStorageKey);
  return raw ? JSON.parse(raw) : {reports: [], decisions: {}};
}

function writeDemoState(data) {
  try {localStorage.setItem(demoStorageKey, JSON.stringify(data));}
  catch {throw new Error('Browser storage blocked · Allow site data or switch browsers');}
}

const paths = {
  inbox: '<path d="M4 5h16v14H4zM4 13h5l2 3h2l2-3h5"/>',
  urgent: '<path d="m13 3-8 11h6l-1 7 9-12h-6z"/>',
  review: '<circle cx="12" cy="12" r="8"/><path d="M12 7v5m0 4h.01"/>',
  done: '<circle cx="12" cy="12" r="8"/><path d="m8 12 3 3 5-6"/>',
  labels: '<path d="m4 4 9 0 8 8-9 9-8-8z"/><circle cx="9" cy="9" r="1"/>',
  chart: '<path d="M4 4v16h16M8 15v-3m5 3V7m5 8v-5"/>',
  search: '<circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 4 4"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  left: '<path d="m14 6-6 6 6 6"/>',
  right: '<path d="m10 6 6 6-6 6"/>',
  check: '<path d="m5 12 4 4L19 6"/>'
};
const icon = name => `<svg viewBox="0 0 24 24" aria-hidden="true">${paths[name]}</svg>`;
const iconButton = (id, name, label, disabled = false) => `<button type="button" id="${id}" class="icon-button" aria-label="${label}" title="${label}" ${disabled ? 'disabled' : ''}>${icon(name)}</button>`;
const header = (title, count = '', actions = '', className = '') => `<header class="page-header ${className}"><div class="page-title"><h1>${title}</h1>${count !== '' ? `<span class="total">${count}</span>` : ''}</div><div class="header-actions">${actions}</div></header>`;

async function api(path, options = {}) {
  let response;
  try {response = await fetch(path, {headers: {'Content-Type': 'application/json'}, ...options});}
  catch {throw new Error('Couldn’t reach Relay · Try again');}
  if (!response.ok) {
    let message = 'Request failed';
    try { const result = await response.json(); message = typeof result.detail === 'string' ? result.detail : result.detail?.[0]?.msg || message; } catch {}
    throw new Error(shortCopy(message));
  }
  return response.json();
}
function toast(message, error = false, reportId = null) {
  const el = $('#toast'); el.textContent = message; el.className = `toast show${error ? ' error' : ''}`;
  if (reportId) {
    const link = document.createElement('a'); link.href = '#operations/done'; link.textContent = 'View Done';
    link.onclick = event => {
      state.selected = reportId; state.search = ''; state.revealOnce = true;
      if (location.hash === '#operations/done') {event.preventDefault(); navigate();}
    }; el.append(link);
  }
  clearTimeout(toastTimer); toastTimer = setTimeout(() => el.classList.remove('show'), reportId ? 8000 : 4000);
}
function categoryOptions(selected = '', unclear = false, teams = false) {
  const entries = Object.entries(state.config.categories);
  if (unclear) entries.push(['unclear', {label: 'Unclear', team: 'Unclear'}]);
  return '<option value="">Select…</option>' + entries.map(([id, cat]) => `<option value="${id}" ${selected === id ? 'selected' : ''}>${esc(teams ? cat.team : cat.label)}</option>`).join('');
}
function reportParts(text) {
  const clean = text.replace(/^(?:Dispatch update: |Please check this report\. |Message from the receiving team: |Operations note — )/, '').replace(/ Please advise the next team\.$/, '');
  const match = clean.match(/^(.+?[.!?])(?:\s+|$)([\s\S]*)$/);
  return match ? {title: match[1].replace(/\.$/, ''), body: match[2]} : {title: clean, body: ''};
}
const isUrgent = row => Boolean(row.clarification?.urgent ?? row.prediction.urgent);
const needsReview = row => Boolean(row.clarification || row.prediction.review);
const compareIncidents = (a, b) => Boolean(a.decision) - Boolean(b.decision) || isUrgent(b) - isUrgent(a) ||
  needsReview(b) - needsReview(a) || a.id.localeCompare(b.id);

function rowStatus(row) {
  if (row.decision) return {name: 'Done', type: 'done', icon: 'done'};
  if (isUrgent(row)) return {name: 'Urgent', type: 'urgent', icon: 'urgent'};
  if (row.clarification) return {name: 'Clarification', type: 'review', icon: 'review'};
  if (needsReview(row)) return {name: 'Review', type: 'review', icon: 'review'};
  return {name: '', type: '', icon: ''};
}
function renderNavigation() {
  const open = (state.incidents || []).filter(r => !r.decision);
  const counts = {all: open.length, urgent: open.filter(isUrgent).length,
    review: open.filter(r => needsReview(r) && !isUrgent(r)).length, done: (state.incidents || []).length - open.length};
  $('#navigation').innerHTML = [['all', 'Inbox', 'inbox'], ['urgent', 'Urgent', 'urgent'], ['review', 'Needs review', 'review'], ['done', 'Done', 'done']].map(([id, name, symbol]) =>
    `<a class="nav-link ${id === 'all' ? 'mobile-inbox ' : ''}${id === 'all' && state.view === 'operations' ? 'section-active ' : ''}${state.view === 'operations' && state.filter === id ? 'active' : ''}" href="#operations/${id}" data-filter="${id}" ${state.view === 'operations' && state.filter === id ? 'aria-current="page"' : ''}>${icon(symbol)}<span>${name}</span>${state.incidents ? `<span class="nav-count">${counts[id]}</span>` : ''}</a>`).join('') +
    `<div class="nav-divider" role="separator"></div><a class="nav-link ${state.view === 'review' ? 'active' : ''}" href="#review" ${state.view === 'review' ? 'aria-current="page"' : ''}>${icon('labels')}<span>Reviews</span></a>
    <a class="nav-link ${state.view === 'evidence' ? 'active' : ''}" href="#evidence" ${state.view === 'evidence' ? 'aria-current="page"' : ''}>${icon('chart')}<span>Evaluation</span></a>`;
}
const triageReport = (text, method, policy, save = false) => api('/api/triage', {
  method: 'POST', body: JSON.stringify({text, method, policy, save})
});

async function incidentRows(method, policy) {
  const rows = await api(`/api/incidents?method=${method}&policy=${policy}`);
  if (!browserDemo()) return rows;

  const {reports, decisions, clarifications = {}} = readDemoState();
  const custom = await Promise.all(reports.map(async report => {
    const key = `${report.id}:${method}:${policy}`;
    if (!demoPredictions.has(key)) {
      const {prediction} = await triageReport(report.text, method, policy);
      demoPredictions.set(key, prediction);
    }
    return {...report, prediction: demoPredictions.get(key)};
  }));
  return [...rows, ...custom].map(row => ({...row, decision: decisions[row.id] || null,
    clarification: clarifications[row.id] || null})).sort(compareIncidents);
}

async function createIncident(text, method, policy) {
  const result = await triageReport(text, method, policy, !browserDemo());
  if (!browserDemo()) return result.id;

  const id = `NEW-${crypto.randomUUID().replace(/-/g, '').slice(0, 12).toUpperCase()}`;
  const data = readDemoState();
  data.reports.push({id, text: text.trim(), channel: 'Demo entry'});
  writeDemoState(data);
  demoPredictions.set(`${id}:${method}:${policy}`, result.prediction);
  return id;
}

async function saveIncidentAction(id, action, payload) {
  if (!browserDemo()) {
    const {created_at} = await api(`/api/incidents/${id}/${action}`, {method: 'POST', body: JSON.stringify(payload)});
    return {...payload, note: payload.note.trim(), created_at};
  }
  const data = readDemoState();
  const saved = {...payload, note: payload.note.trim(), created_at: new Date().toISOString()};
  if (action === 'clarification') {
    if (data.decisions[id]) throw new Error('Route already confirmed');
    (data.clarifications ??= {})[id] = saved;
  } else {
    data.decisions[id] = saved;
    delete data.clarifications?.[id];
  }
  writeDemoState(data);
  return saved;
}

async function refreshIncidents(method, policy, version, onReady) {
  while (version === navigationVersion) {
    const revision = incidentRevision;
    const rows = await incidentRows(method, policy);
    if (version === navigationVersion && revision === incidentRevision) return onReady(rows);
  }
}

function loadIncidents() {
  const method = state.method, policy = state.policy, version = navigationVersion;
  return refreshIncidents(method, policy, version, rows => {
    if (method === state.method && policy === state.policy) state.incidents = rows;
  });
}
function filteredIncidents() {
  return (state.incidents || []).filter(row => {
    if (state.filter === 'done' ? !row.decision : row.decision) return false;
    if (state.filter === 'urgent' && !isUrgent(row)) return false;
    if (state.filter === 'review' && (!needsReview(row) || isUrgent(row))) return false;
    const category = row.decision?.category || row.prediction.category;
    const team = state.config.categories[category];
    return !state.search.trim() || `${row.id} ${row.text} ${team.label} ${team.team}`.toLowerCase().includes(state.search.trim().toLowerCase());
  });
}
function queueMarkup(rows) {
  return rows.length ? rows.map(row => {
    const status = rowStatus(row);
    return `<button class="queue-row ${row.id === state.selected ? 'selected' : ''}" data-report="${row.id}" aria-pressed="${row.id === state.selected}"><span class="row-title">${esc(reportParts(row.text).title)}</span>
    <span class="row-meta"><span class="row-id">${row.id}</span>${status.name ? `<span class="row-state ${status.type}">${icon(status.icon)}${status.name}</span>` : ''}</span></button>`;
  }).join('') : `<div class="empty">${icon('check')}<p>${state.search ? 'No matching reports' : state.filter === 'done' ? 'No confirmed routes yet' : 'All clear'}</p>${state.search ? '<button type="button" class="button ghost" data-clear-search>Clear search</button>' : ''}</div>`;
}
function renderOperations() {
  const rows = filteredIncidents();
  if (!rows.some(r => r.id === state.selected)) state.selected = rows[0]?.id;
  const titles = {all: 'Inbox', urgent: 'Urgent', review: 'Needs review', done: 'Done'};
  $('#main').innerHTML = header(titles[state.filter], rows.length, `<button class="button" id="open-new">${icon('plus')}New report</button>`) +
    `<div class="desk ${state.mobileDetail ? 'mobile-detail' : ''}" id="desk"><aside class="queue" aria-label="Reports"><div class="queue-toolbar">${icon('search')}
    <input type="search" id="queue-search" aria-label="Search reports" placeholder="Search" value="${esc(state.search)}">
    <select class="mobile-filter" id="mobile-filter" aria-label="Filter reports">${Object.entries(titles).map(([id, label]) => `<option value="${id}" ${state.filter === id ? 'selected' : ''}>${label}</option>`).join('')}</select></div>
    <div class="queue-list" id="queue-list">${queueMarkup(rows)}</div></aside><article class="incident-detail" id="incident-detail" aria-label="Report"></article></div>`;
  renderNavigation(); renderDetail();
  $('.queue-row.selected')?.scrollIntoView({block: 'nearest'});
  $('#open-new').onclick = openNew;
  $('#queue-search').oninput = event => {state.search = event.target.value; updateQueue();};
  $('#mobile-filter').onchange = event => {location.hash = `operations/${event.target.value}`;};
  $('#queue-list').onclick = event => {
    if (event.target.closest('[data-clear-search]')) {state.search = ''; $('#queue-search').value = ''; updateQueue(); $('#queue-search').focus(); return;}
    const button = event.target.closest('[data-report]');
    if (button) {state.selected = button.dataset.report; state.mobileDetail = true; updateQueue(false); $('#desk').classList.add('mobile-detail'); $('#incident-detail h2')?.focus({preventScroll:true});}
  };
}
function updateQueue(autoSelect = true) {
  const rows = filteredIncidents();
  if (autoSelect && !rows.some(r => r.id === state.selected)) state.selected = rows[0]?.id;
  $('#queue-list').innerHTML = queueMarkup(rows);
  $('.page-title .total').textContent = rows.length;
  renderDetail();
  $('.queue-row.selected')?.scrollIntoView({block: 'nearest'});
}
function renderDetail() {
  const row = (state.incidents || []).find(r => r.id === state.selected);
  const detail = $('#incident-detail');
  if (!row) {detail.innerHTML = '<p class="empty">No report selected</p>'; return;}
  const rows = filteredIncidents(), index = rows.findIndex(r => r.id === row.id);
  const pred = row.prediction, decision = row.decision, clarification = row.clarification;
  const draft = state.decisionDrafts[row.id] || {category: decision?.category || pred.category,
    urgent: decision ? Boolean(decision.urgent) : isUrgent(row), note: decision?.note ?? clarification?.note ?? ''};
  const parts = reportParts(row.text);
  const status = decision ? {name: 'Done', type: 'done', symbol: 'done'} : clarification ?
    {name: 'Awaiting clarification', type: isUrgent(row) ? 'urgent' : 'review', symbol: isUrgent(row) ? 'urgent' : 'review'} : pred.urgent && pred.review ?
    {name: 'Urgent review', type: 'urgent', symbol: 'urgent'} : pred.review ?
    {name: 'Needs review', type: 'review', symbol: 'review'} : pred.urgent ? {name: 'Urgent', type: 'urgent', symbol: 'urgent'} : {name: 'Open', type: '', symbol: 'inbox'};
  detail.innerHTML = `<div class="detail-top"><div class="detail-location"><button class="icon-button back-button" id="back-to-list" aria-label="Back to reports">${icon('left')}</button><span class="detail-id">${row.id}</span></div>
    <div class="detail-pager"><span class="position">${index + 1} / ${rows.length}</span>${iconButton('prev-report', 'left', 'Previous report', index <= 0)}${iconButton('next-report', 'right', 'Next report', index >= rows.length - 1)}</div></div>
    <div class="detail-content"><div class="detail-status status ${status.type}">${icon(status.symbol)}${status.name}</div><h2 tabindex="-1">${esc(parts.title)}</h2>${parts.body ? `<p class="report-body">${esc(parts.body)}</p>` : ''}
    ${decision ? '' : renderRationale(pred)}
    <form id="decision-form"><div class="properties">
    <div class="property"><label for="decision-category">Team</label><select id="decision-category" required>${categoryOptions(draft.category, false, true)}</select></div>
    <div class="property"><label for="decision-urgency">Urgency</label><select id="decision-urgency"><option value="urgent" ${draft.urgent ? 'selected' : ''}>Urgent</option><option value="routine" ${!draft.urgent ? 'selected' : ''}>Routine</option></select></div></div>
    <div class="note-field"><label class="sr-only" for="decision-note">Note</label><textarea id="decision-note" maxlength="1000" rows="2" placeholder="Add a note…">${esc(draft.note)}</textarea></div>
    <div class="form-actions">${decision ? '' : `<button type="button" id="request-clarification" class="button ghost">${clarification ? 'Save clarification' : 'Request clarification'}</button>`}<button type="submit" class="button primary">${icon('check')}${decision ? 'Update' : 'Confirm route'}</button></div></form>
    ${decision ? `<details class="activity"><summary>Activity</summary><div class="activity-row">${icon('check')}<span>${esc(state.config.categories[decision.category].team)}</span><time datetime="${esc(decision.created_at)}">${esc(new Date(decision.created_at).toLocaleTimeString('en-SG', {hour: '2-digit', minute: '2-digit', timeZone: 'Asia/Singapore'}))}</time>${decision.note ? `<p>${esc(decision.note)}</p>` : ''}</div></details>` : ''}</div>`;
  $('#back-to-list').onclick = () => {state.mobileDetail = false; $('#desk').classList.remove('mobile-detail'); $('#queue-search').focus();};
  $('#prev-report').onclick = () => moveIncident(-1);
  $('#next-report').onclick = () => moveIncident(1);
  $('#decision-form').oninput = () => {
    state.decisionDrafts[row.id] = {category: $('#decision-category').value, urgent: $('#decision-urgency').value === 'urgent', note: $('#decision-note').value};
  };
  if (state.pendingDecisions.has(row.id)) {
    document.querySelectorAll('#decision-form select, #decision-form textarea, #decision-form button').forEach(el => el.disabled = true);
  }
  async function saveAction(action) {
    if (state.pendingDecisions.has(row.id)) return;
    const version = navigationVersion;
    const pending = action === 'clarification';
    const category = $('#decision-category').value;
    const payload = {urgent: $('#decision-urgency').value === 'urgent', note: $('#decision-note').value};
    if (pending && !payload.note.trim()) {
      toast('Add a clarification note', true);
      $('#decision-note').focus();
      return;
    }
    if (!pending) payload.category = category;
    state.pendingDecisions.add(row.id);
    document.querySelectorAll('#decision-form select, #decision-form textarea, #decision-form button').forEach(el => el.disabled = true);
    try {
      const saved = await saveIncidentAction(row.id, action, payload);
      // A successful save is final even if a later refresh loses its connection.
      incidentRevision++;
      const item = (state.incidents || []).find(incident => incident.id === row.id);
      if (item) {
        item[action] = saved;
        if (!pending) item.clarification = null;
        state.incidents.sort(compareIncidents);
      }
      if (pending && category !== pred.category) state.decisionDrafts[row.id] = {category, urgent: saved.urgent, note: saved.note};
      else delete state.decisionDrafts[row.id];
      state.pendingDecisions.delete(row.id);
      if (state.view === 'operations' && $('#queue-list')) {
        const sameView = version === navigationVersion;
        const selected = state.selected === row.id;
        const moved = selected && !filteredIncidents().some(incident => incident.id === row.id);
        if (pending && sameView && moved) {
          state.revealOnce = true;
          location.hash = `operations/${saved.urgent ? 'urgent' : 'review'}`;
        } else {
          if (moved) {
            state.mobileDetail = false;
            $('#desk').classList.remove('mobile-detail');
          }
          updateQueue();
          if (pending && sameView && selected) $('#request-clarification')?.focus({preventScroll: true});
        }
      }
      renderNavigation();
      toast(pending ? 'Clarification saved' : decision ? 'Route updated' : 'Route confirmed', false, pending ? null : row.id);
    } catch (error) {
      state.pendingDecisions.delete(row.id); toast(error.message, true);
      if (state.view === 'operations' && state.selected === row.id && $('#incident-detail')) renderDetail();
    }
  }
  $('#decision-form').onsubmit = event => {
    event.preventDefault();
    return saveAction('decision');
  };
  const clarificationButton = $('#request-clarification');
  if (clarificationButton) clarificationButton.onclick = () => saveAction('clarification');
}
function renderRationale(prediction) {
  const rationale = prediction.rationale;
  if (!rationale) return '';
  const rows = [['Team', rationale.team], ['Urgency', rationale.urgency], ['Review', rationale.review]];
  const seen = new Set();
  const details = rows.filter(([, reason]) => {
    if (!reason || seen.has(reason)) return false;
    seen.add(reason);
    return true;
  }).map(([label, reason]) => `<div><dt>${label}</dt><dd>${esc(reason)}</dd></div>`).join('');
  return details ? `<details class="route-rationale"><summary>${prediction.urgent || prediction.review ? 'Why flagged?' : 'Why this route?'}</summary><dl>${details}</dl></details>` : '';
}

function moveIncident(delta) {
  if (!$('#queue-list')) return;
  const rows = filteredIncidents(), index = rows.findIndex(r => r.id === state.selected);
  if (rows[index + delta]) {state.selected = rows[index + delta].id; updateQueue(false); $('#incident-detail h2')?.focus({preventScroll:true});}
}
function renderEvidence() {
  const result = state.evidence;
  const dataset = state.evidenceDataset;
  const fresh = dataset === 'fresh' || dataset === 'fresh2';
  const metricsOpen = $('#all-metrics')?.open ? 'open' : '';
  const methodOpen = $('#evaluation-method')?.open ? 'open' : '';
  const datasets = result.available_datasets || [{id:'development',label:'Development'}];
  const benchmarkVersionLabel = result.revision || (dataset === 'test' ? 'v1' : '');
  const denominators = result.methods[0];
  const count = value => Number.isFinite(value) ? value : '—';
  const ratio = (numerator, total) => Number.isInteger(numerator) && Number.isInteger(total) ? `${numerator}/${total}` : '—';
  const caught = (total, missed) => Number.isInteger(missed) ? ratio(total - missed, total) : '—';
  const standard = result.methods.find(row => row.method === 'learned' && row.policy === 'standard');
  const sensitive = result.methods.find(row => row.method === 'learned' && row.policy === 'sensitive');
  const comparison = [
    ['Review flags', row => ratio(row.review_count, row.n)],
    ['Required reviews flagged', row => caught(row.review_required_n, row.required_review_automated)],
    ['False urgent flags', row => count(row.false_urgent)],
    ['Urgent cases caught', row => caught(row.urgent_total, row.urgent_misses)]
  ];
  const benchmarkMethod = {
    fresh: 'Implementation frozen before test reports',
    fresh2: 'Implementation frozen before test reports',
    test: 'Original frozen test',
    retest: 'Diagnostic retest · previously seen reports',
    development: 'Development held-out split · author labels'
  }[dataset];
  const referenceLabels = dataset === 'development' ? '' : `<a class="button ghost" href="#review/${fresh ? dataset : 'auto'}">Labels</a>`;
  $('#main').innerHTML = header('Evaluation') + `<div class="content-page evaluation-page">
    <div class="evaluation-toolbar">
      <label for="benchmark" class="sr-only">Benchmark</label>
      <select id="benchmark">${datasets.map(item => `<option value="${esc(item.id)}" ${dataset === item.id ? 'selected' : ''}>${esc(item.label)}</option>`).join('')}</select>
      <div class="evaluation-meta"><span>${count(result.evaluation_n)} reports</span>
      ${benchmarkVersionLabel ? `<span class="evaluation-version"><span class="sr-only">Benchmark version </span>${esc(benchmarkVersionLabel)}</span>` : ''}</div>
      ${referenceLabels}
    </div>
    <table class="evaluation-comparison">
      <caption>Policy comparison</caption>
      <thead><tr><th scope="col">Text model</th><th scope="col">Standard</th><th scope="col">Sensitive</th></tr></thead>
      <tbody>${comparison.map(([label, value]) => `<tr><th scope="row">${label}</th>${[standard, sensitive].map(row => `<td>${row ? value(row) : '—'}</td>`).join('')}</tr>`).join('')}</tbody>
    </table>
    <details class="evaluation-details" id="all-metrics" ${metricsOpen}><summary>All metrics</summary>
      <div class="table-wrap" role="region" aria-label="Benchmark metrics" tabindex="0"><table>
      <thead><tr><th scope="col">Model</th><th scope="col">Policy</th><th scope="col">Team accuracy</th><th scope="col">Macro F1</th><th scope="col">Urgent recall</th><th scope="col">Urgent missed</th><th scope="col">Review flags</th><th scope="col">Coverage</th><th scope="col">Cost · 30 per miss</th><th scope="col">Cost · 100 per miss</th><th scope="col">p95 ms</th></tr></thead>
      <tbody>${result.methods.map(row => `<tr><td>${row.method === 'rules' ? 'Rules' : 'Text model'}</td><td>${row.policy === 'standard' ? 'Standard' : 'Sensitive'}</td><td>${pct(row.category_accuracy)}</td><td>${row.macro_f1?.toFixed(3) ?? '—'}</td><td>${pct(row.urgent_recall)}</td><td>${ratio(row.urgent_misses, row.urgent_total)}</td><td>${ratio(row.review_count, row.n)}</td><td>${pct(row.automation_coverage)}</td><td>${count(row.cost_units_standard)}</td><td>${count(row.cost_units_sensitive)}</td><td>${row.p95_ms?.toFixed(3) ?? '—'}</td></tr>`).join('')}</tbody></table></div>
    </details>
    <details class="evaluation-details" id="evaluation-method" ${methodOpen}><summary>Method</summary>
      <dl class="evaluation-method">
        <div><dt>Reports</dt><dd>Synthetic · ${benchmarkMethod}</dd></div>
        ${dataset !== 'development' ? '<div><dt>Labels</dt><dd>Independent agent · same model family · operator validation pending</dd></div>' : ''}
        <div><dt>Training</dt><dd>${count(result.train_n)} reports</dd></div>
        <div><dt>Known labels</dt><dd>Team ${ratio(denominators.category_n, result.evaluation_n)} · Urgency ${ratio(denominators.urgency_n, result.evaluation_n)}</dd></div>
        <div><dt>Cost units</dt><dd>Review 1 · Wrong team or required review missed 6 · False urgent 2 · Urgent missed 30 or 100</dd></div>
        <div><dt>p95</dt><dd>Warm inference · ${count(denominators.latency_samples)} runs per model and policy</dd></div>
      </dl>
    </details>
    <section class="evaluation-settings" aria-labelledby="inbox-settings">
      <div class="evaluation-settings-heading"><h2 id="inbox-settings">Inbox settings</h2>${state.config?.revision ? `<span class="evaluation-version"><span class="sr-only">Live version </span>${esc(state.config.revision)}</span>` : ''}</div>
      <form class="model-form" id="model-form">
        <div><label for="method">Model</label><select id="method"><option value="rules" ${state.method === 'rules' ? 'selected' : ''}>Rules</option><option value="learned" ${state.method === 'learned' ? 'selected' : ''}>Text model</option></select></div>
        <div><label for="policy">Policy</label><select id="policy"><option value="standard" ${state.policy === 'standard' ? 'selected' : ''}>Standard</option><option value="sensitive" ${state.policy === 'sensitive' ? 'selected' : ''}>Sensitive</option></select></div>
        <button class="button" id="apply-settings" type="submit" ${state.settingsPending ? 'disabled' : ''}>Apply</button>
      </form>
    </section></div>`;
  renderNavigation();
  if ($('#benchmark')) $('#benchmark').onchange = async event => {
    const dataset = event.target.value, request = ++benchmarkVersion, version = navigationVersion;
    try {const evidence = await api(`/api/evidence?dataset=${dataset}`);
      if (request === benchmarkVersion && version === navigationVersion) {state.evidenceDataset = dataset; state.evidence = evidence; renderEvidence(); $('#benchmark').focus();}}
    catch (error) {if (request === benchmarkVersion && version === navigationVersion) {event.target.value = state.evidenceDataset; toast(error.message, true);}}
  };
  $('#model-form').onsubmit = async event => {
    event.preventDefault();
    if (state.settingsPending) return;
    state.settingsPending = true;
    $('#apply-settings').disabled = true;
    const method = $('#method').value, policy = $('#policy').value, version = navigationVersion;
    try {
      await refreshIncidents(method, policy, version, incidents => {
        Object.assign(state, {method, policy, incidents});
        storage.set('relay-method', method); storage.set('relay-policy', policy);
        if ($('#model-form') !== event.target) {$('#method').value = method; $('#policy').value = policy;}
        renderNavigation(); toast('Settings applied');
      });
    } catch (error) {
      if (version === navigationVersion) toast(error.message, true);
    } finally {
      state.settingsPending = false;
      const apply = $('#apply-settings');
      if (apply) apply.disabled = false;
    }
  };
}
function reviewDraft(row) {
  if (row.readonly) return row.review;
  let draft = null; try {draft = JSON.parse(storage.get(`relay-draft-${row.id}`) || 'null');} catch {}
  return draft && typeof draft === 'object' ? draft : row.review || {};
}
function renderReview() {
  const last = state.reviews.length - 1;
  if (last < 0) {$('#main').innerHTML = header('Reviews') + '<div class="empty"><p>No reviews available</p></div>'; renderNavigation(); return;}
  state.reviewIndex = Math.max(0, Math.min(last, Number.isFinite(state.reviewIndex) ? state.reviewIndex : 0));
  const row = state.reviews[state.reviewIndex], draft = reviewDraft(row), readonly = !!row.readonly;
  const source = ['quality', 'fresh', 'fresh2'].includes(state.reviewSource) ? state.reviewSource : readonly ? 'independent' : 'human';
  const count = state.reviews.filter(r => r.review).length, parts = reportParts(row.text);
  const clarification = draft.clarification === true || draft.clarification === 1 ? 'yes' : draft.clarification === false || draft.clarification === 0 ? 'no' : '';
  const sourceOptions = [['quality','Latest review'],['fresh2','Fresh 2'],['fresh','Fresh 1'],['auto','Original']];
  if (!browserDemo()) sourceOptions.push(['human','Your review']);
  const pager = `${iconButton('review-prev', 'left', 'Previous report', state.reviewIndex === 0)}<button type="button" class="button ${readonly ? '' : 'ghost'}" id="review-next" ${state.reviewIndex === last ? 'disabled' : ''}>Next${icon('right')}</button>`;
  $('#main').innerHTML = header('Reviews', `${count} / ${state.reviews.length}`, `<label for="review-source" class="sr-only">Report set</label><select id="review-source">${sourceOptions.map(([id,label]) => `<option value="${id}" ${state.reviewSource === id ? 'selected' : ''}>${label}</option>`).join('')}</select><button class="button ghost" id="open-guide">Guide</button><a class="button" href="/api/review/export?source=${source}" download>Export</a>`, 'review-header') +
    `<div class="review-page"><div class="review-meta"><div class="review-location"><span>${esc(row.id)}</span>${row.review ? `<span class="saved-state">${icon('check')}${readonly ? 'Reviewed' : 'Saved'}</span>` : ''}</div><button type="button" class="button ghost" id="open-jump" aria-label="Choose report">${state.reviewIndex + 1} / ${state.reviews.length}${icon('labels')}</button></div>
    <article class="review-report"><h2>${esc(parts.title)}</h2>${parts.body ? `<p class="report-body">${esc(parts.body)}</p>` : ''}</article>
    ${readonly ? `<dl class="review-verdict"><div><dt>Team</dt><dd>${esc(state.config.categories[draft.category]?.team || 'Unclear')}</dd></div><div><dt>Urgency</dt><dd class="${draft.urgency === 'urgent' ? 'urgent-text' : ''}">${draft.urgency === 'urgent' ? icon('urgent') : ''}${esc(draft.urgency[0].toUpperCase() + draft.urgency.slice(1))}</dd></div><div><dt>Clarification</dt><dd>${clarification === 'yes' ? 'Needed' : 'Not needed'}</dd></div></dl>
      <section class="review-explanation"><h3>Reason</h3><p>${esc(draft.reason)}</p></section>
      ${draft.agrees_with_reference === false ? `<details class="review-difference"><summary>Review difference</summary><p>${esc(draft.disagreement_note)}</p></details>` : ''}
      <div class="review-footer review-pagination"><div class="right">${pager}</div></div>` :
      `<form id="review-form"><div class="review-fields"><div><label for="review-category">Team</label><select id="review-category" required>${categoryOptions(draft.category || '', true, true)}</select></div>
      <div><label for="review-urgency">Urgency</label><select id="review-urgency" required><option value="">Select…</option>${['urgent','routine','unclear'].map(u => `<option value="${u}" ${draft.urgency === u ? 'selected' : ''}>${u[0].toUpperCase() + u.slice(1)}</option>`).join('')}</select></div>
      <div><label for="review-clarify">Clarification</label><select id="review-clarify" required><option value="">Select…</option><option value="yes" ${clarification === 'yes' ? 'selected' : ''}>Needed</option><option value="no" ${clarification === 'no' ? 'selected' : ''}>Not needed</option></select></div></div>
      <div class="review-note"><label for="review-reason">Reason</label><textarea id="review-reason" maxlength="1000" rows="3">${esc(draft.reason || '')}</textarea></div><div class="form-error" id="review-error" role="alert"></div>
      <div class="reviewer-field"><label for="reviewer-name">Reviewer</label><input id="reviewer-name" required autocomplete="name" maxlength="80" value="${esc(state.reviewer)}"></div>
      <div class="review-footer"><div class="right">${pager}</div><button class="button primary" type="submit">${state.reviewIndex === last ? 'Save review' : 'Save & next'}${icon('check')}</button></div></form>`}</div>`;
  renderNavigation();
  $('#review-source').onchange = event => {location.hash = `review/${event.target.value}`;};
  $('#open-guide').onclick = () => {
    const credit = source === 'quality' ? 'Agent second review · Earlier labels visible' : 'Independent agent review · Reports and guide only';
    $('#guide-content').innerHTML = state.config.guide.map(([name, definition]) => `<dt>${esc(name)}</dt><dd>${esc(shortCopy(definition))}</dd>`).join('') + (readonly ? `<dt>Review source</dt><dd>${credit}</dd>` : '<dt>Your review</dt><dd>Use Unclear for missing facts · Add a reason</dd>');
    $('#guide-dialog').showModal();
  };
  $('#open-jump').onclick = () => {
    $('#jump-content').innerHTML = state.reviews.map((r, i) => `<button type="button" data-review-index="${i}" class="${r.review ? 'done ' : ''}${i === state.reviewIndex ? 'current' : ''}" aria-label="Report ${i + 1}${r.review ? ', reviewed' : ''}" ${i === state.reviewIndex ? 'aria-current="true"' : ''}>${i + 1}</button>`).join(''); $('#jump-dialog').showModal();
  };
  $('#review-prev').onclick = () => moveReview(state.reviewIndex - 1, 'review-prev');
  $('#review-next').onclick = () => moveReview(state.reviewIndex + 1, 'review-next');
  if (readonly) return;
  $('#review-form').oninput = () => storage.set(`relay-draft-${row.id}`, JSON.stringify({category: $('#review-category').value,
    urgency: $('#review-urgency').value, clarification: $('#review-clarify').value === '' ? null : $('#review-clarify').value === 'yes', reason: $('#review-reason').value}));
  $('#reviewer-name').oninput = event => {state.reviewer = event.target.value; storage.set('relay-reviewer', state.reviewer);};
  $('#review-form').onsubmit = async event => {
    event.preventDefault(); const button = $('button[type=submit]', event.target), error = $('#review-error'); if (button.disabled) return; error.textContent = '';
    const version = navigationVersion, index = state.reviewIndex, savedDraft = storage.get(`relay-draft-${row.id}`);
    const payload = {category: $('#review-category').value, urgency: $('#review-urgency').value,
      clarification: $('#review-clarify').value === 'yes', reason: $('#review-reason').value, reviewer: state.reviewer.trim()};
    if (!payload.reviewer) {error.textContent = 'Enter your name'; $('#reviewer-name').focus(); return;}
    if ((payload.category === 'unclear' || payload.urgency === 'unclear' || payload.clarification) && !payload.reason.trim()) {error.textContent = 'Add the facts you still need to check'; $('#review-reason').focus(); return;}
    button.disabled = true;
    try {
      await api(`/api/review/${row.id}`, {method: 'POST', body: JSON.stringify(payload)});
      if (storage.get(`relay-draft-${row.id}`) === savedDraft) storage.remove(`relay-draft-${row.id}`);
      if (version === navigationVersion && state.reviewSource === 'human') {
        row.review = payload;
        if (state.reviewIndex === index) moveReview(Math.min(last, index + 1));
      }
      toast('Review saved');
    } catch (err) {error.textContent = err.message; button.disabled = false; toast(err.message, true);}
  };
}
function moveReview(index, focusId = 'open-jump') {
  state.reviewIndex = Math.max(0, Math.min(state.reviews.length - 1, index));
  storage.set(`relay-review-index-${state.reviewSource}`, state.reviewIndex); renderReview();
  const target = document.getElementById(focusId); (target?.disabled ? $('#open-jump') : target)?.focus({preventScroll:true});
}
async function navigate() {
  const version = ++navigationVersion, [view, filter] = location.hash.slice(1).split('/');
  state.view = ['operations', 'evidence', 'review'].includes(view) ? view : 'operations';
  state.filter = ['all', 'urgent', 'review', 'done'].includes(filter) ? filter : 'all';
  state.mobileDetail = !!state.revealOnce; state.revealOnce = false; renderNavigation();
  $('#main').innerHTML = '<div class="loading" role="status">Loading…</div>';
  try {
    if (state.view === 'operations') {
      await loadIncidents(); if (version === navigationVersion) renderOperations();
    } else if (state.view === 'evidence') {
      const evidence = await api(`/api/evidence?dataset=${state.evidenceDataset}`);
      if (version === navigationVersion) {state.evidence = evidence; renderEvidence();}
    } else {
      const validSource = ['fresh', 'fresh2', 'auto', 'quality'].includes(filter) || (filter === 'human' && !browserDemo());
      const source = validSource ? filter : 'quality';
      const reviews = await api(`/api/review?source=${source}`);
      if (version === navigationVersion) {
        state.reviewSource = source; state.reviews = reviews;
        state.reviewIndex = Number(storage.get(`relay-review-index-${source}`)) || 0; renderReview();
      }
    }
  } catch (error) {
    if (version !== navigationVersion) return;
    $('#main').innerHTML = `<div class="fatal"><p>${esc(error.message)}</p><button class="button" id="retry-load">Try again</button></div>`; $('#retry-load').onclick = navigate;
  }
}
function openNew() {if (newPending) return; $('#new-error').textContent = ''; $('#new-report').showModal(); $('#new-text').focus();}
$('.skip').onclick = event => {event.preventDefault(); $('#main').focus();};
$('#close-dialog').onclick = $('#cancel-new').onclick = () => {if (!newPending) $('#new-report').close();};
$('#new-report').oncancel = event => {if (newPending) event.preventDefault();};
document.querySelectorAll('[data-close]').forEach(button => button.onclick = () => document.getElementById(button.dataset.close).close());
$('#jump-content').onclick = event => {
  const button = event.target.closest('[data-review-index]'); if (button) {$('#jump-dialog').close(); moveReview(Number(button.dataset.reviewIndex));}
};
$('#new-form').onsubmit = async event => {
  event.preventDefault(); const button = $('#new-submit'); if (button.disabled) return; button.disabled = true; $('#new-error').textContent = '';
  newPending = true;
  document.querySelectorAll('#new-form textarea, #new-form button').forEach(el => el.disabled = true);
  try {
    const id = await createIncident($('#new-text').value, state.method, state.policy);
    $('#new-report').close(); event.target.reset();
    state.selected = id; state.search = ''; state.revealOnce = true;
    history.replaceState(null, '', '#operations/all'); await navigate(); toast('Report created');
  } catch (error) {$('#new-error').textContent = error.message;}
  finally {newPending = false; document.querySelectorAll('#new-form textarea, #new-form button').forEach(el => el.disabled = false); button.disabled = false;}
};
window.addEventListener('hashchange', navigate);
window.addEventListener('keydown', event => {
  if (event.metaKey || event.ctrlKey || event.altKey || event.target.closest('input,textarea,select,[contenteditable]') || document.querySelector('dialog[open]')) return;
  if (state.view === 'operations' && $('#queue-list')) {
    if (event.key === 'j') {event.preventDefault(); moveIncident(1);}
    if (event.key === 'k') {event.preventDefault(); moveIncident(-1);}
    if (event.key === 'n') {event.preventDefault(); openNew();}
    if (event.key === 'Escape') {state.mobileDetail = false; $('#desk')?.classList.remove('mobile-detail');}
  }
});
(async () => {
  try {
    state.config = await api('/api/config');
    $('#browser-save-notice').hidden = !browserDemo();
    state.evidenceDataset = state.config.default_evidence_dataset || 'development';
    await navigate();
  }
  catch (error) {$('#main').innerHTML = `<div class="fatal"><p>${esc(error.message)}</p><button class="button" onclick="location.reload()">Reload</button></div>`;}
})();
