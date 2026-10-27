/* SPARC — Smart Supply Chain Performer Copilot — application. Vanilla JS; every call goes through the governed FastAPI gateway. */
(() => {
  const { esc, fmt, statusBadge } = window.Charts;
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
  const local = {
    get(k) { try { return localStorage.getItem(k) || ''; } catch { return ''; } },
    set(k, v) { try { v ? localStorage.setItem(k, v) : localStorage.removeItem(k); } catch { /* storage unavailable */ } },
  };
  const session = {
    get(k) { try { return sessionStorage.getItem(k) || ''; } catch { return ''; } },
    set(k, v) { try { v ? sessionStorage.setItem(k, v) : sessionStorage.removeItem(k); } catch { /* storage unavailable */ } },
  };
  const state = { key: session.get('apiKey'), role: '', cfg: {}, insights: [], filter: 'all', recFilter: 'pending_review', persona: local.get('persona'), focus: local.get('focus'), product: '', kinds: {}, products: null,
    tenant: local.get('tenant'), catalogue: null, snapshot: null, sites: null, site: local.get('site') };

  // ------------------------------------------------------------------ helpers
  const toast = (msg) => { const t = $('#toast'); t.textContent = msg; t.classList.add('show'); clearTimeout(t._h); t._h = setTimeout(() => t.classList.remove('show'), 4200); };
  const chip = (text) => `<span class="chip">${esc(text)}</span>`;
  const STATUS_OF = {
    ready: 'good', on_track: 'good', matched: 'good', covered: 'good', accepted: 'good', executed: 'good', up: 'good', low: 'good', released: 'good', explained: 'info',
    at_risk: 'warning', depends_on_inbound: 'warning', within_tolerance: 'info', medium: 'warning', timing_gap: 'warning', order_this_week: 'warning', inspection: 'warning',
    replenish_safety_stock: 'info', plan: 'info', pending_review: 'info', disabled: 'info', not_configured: 'info',
    not_ready: 'critical', high: 'critical', short: 'critical', late: 'critical', investigate: 'critical', down: 'critical', rejected: 'critical', blocked: 'critical', expired: 'critical', model_missing: 'warning',
  };
  // Status = color + icon + label, never color alone.
  const pill = (level, label) => { const s = window.Charts.STATUS[level] || window.Charts.STATUS.info; return `<span class="status" style="--dot:${s.color}"><i></i>${s.icon} ${esc(label ?? s.label)}</span>`; };
  const badge = (value, label) => pill(STATUS_OF[value] || 'info', label ?? String(value).replaceAll('_', ' '));
  const table = (cols, rows, opts = {}) => (rows.length
    ? `<div class="scroll"><table><thead><tr>${cols.map((c) => `<th class="${c[2] || ''}">${esc(c[0])}</th>`).join('')}</tr></thead><tbody>${rows.map((r, i) => `<tr${opts.click ? ` class="clickable" data-i="${i}"` : ''}>${cols.map((c) => `<td class="${c[2] || ''}">${c[1](r)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`
    : '<div class="empty">No rows.</div>');
  const num = (v, d = 0) => (v === null || v === undefined || v === '' ? '—' : Number(v).toLocaleString(undefined, { maximumFractionDigits: d }));

  function md(text) {
    const lines = esc(text || '').split('\n');
    let html = '', list = null;
    const inline = (s) => s.replace(/\*\*(.+?)\*\*/g, '<b>$1</b>').replace(/`([^`]+)`/g, '<code>$1</code>');
    const close = () => { if (list) { html += `</${list}>`; list = null; } };
    for (const raw of lines) {
      const line = raw.trimEnd(); let m;
      if ((m = line.match(/^#{1,4}\s+(.*)/))) { close(); html += `<h4>${inline(m[1])}</h4>`; }
      else if ((m = line.match(/^\s*[-*]\s+(.*)/))) { if (list !== 'ul') { close(); list = 'ul'; html += '<ul>'; } html += `<li>${inline(m[1])}</li>`; }
      else if ((m = line.match(/^\s*\d+\.\s+(.*)/))) { if (list !== 'ol') { close(); list = 'ol'; html += '<ol>'; } html += `<li>${inline(m[1])}</li>`; }
      else if (!line.trim()) close();
      else { close(); html += `<p>${inline(line)}</p>`; }
    }
    close();
    return `<div class="md">${html}</div>`;
  }

  async function api(path, opts = {}) {
    const headers = { 'Content-Type': 'application/json', ...(state.key ? { 'X-API-Key': state.key } : {}), ...(state.tenant ? { 'X-Tenant': state.tenant } : {}) };
    const res = await fetch(path, { method: opts.method || (opts.body ? 'POST' : 'GET'), headers, body: opts.body ? JSON.stringify(opts.body) : undefined });
    const text = await res.text();
    let data; try { data = text ? JSON.parse(text) : {}; } catch { data = { detail: text }; }
    if (!res.ok) throw new Error(`${res.status}: ${data?.error?.message || (typeof data?.detail === 'string' ? data.detail : JSON.stringify(data?.detail || data)).slice(0, 300)}`);
    return data;
  }
  async function busy(button, fn) {
    if (!button) return fn();
    const label = button.innerHTML;
    button.disabled = true; button.innerHTML = `<span class="spinner"></span>${label}`;
    try { return await fn(); } catch (e) { toast(e.message); return null; } finally { button.disabled = false; button.innerHTML = label; }
  }
  const formData = (form) => Object.fromEntries(new FormData(form).entries());
  function modal(title, html) {
    const back = document.createElement('div');
    back.className = 'modal-backdrop';
    back.innerHTML = `<div class="modal" role="dialog" aria-label="${esc(title)}"><h2>${esc(title)}</h2>${html}<div class="row" style="justify-content:flex-end;margin-top:14px"><button class="ghost" data-close>Close</button></div></div>`;
    back.addEventListener('click', (e) => { if (e.target === back || e.target.matches('[data-close]')) back.remove(); });
    document.body.appendChild(back);
    return back;
  }
  const fmtValue = (v, unit) => (v === null || v === undefined ? '—' : unit === '€' ? `€${num(v)}` : `${num(v, 1)}${unit ? esc(unit) : ''}`);
  function kpiTiles(target, kpis) {
    const colors = { critical: 'var(--critical)', warning: 'var(--warning)', good: 'var(--good)', info: 'var(--info)' };
    const flags = { critical: ['Act now', 'var(--critical-text)', 'var(--critical-soft)'], warning: ['Watch', 'var(--ink)', 'color-mix(in srgb, var(--warning) 22%, transparent)'] };
    const host = typeof target === 'string' ? $(target) : target;
    host.innerHTML = kpis.map((k, i) => {
      const na = k.available === false;
      const flag = !na && flags[k.status] ? `<span class="flag" style="--flag-text:${flags[k.status][1]};--flag-bg:${flags[k.status][2]}">${flags[k.status][0]}</span>` : '';
      return `<div class="kpi${na ? ' na' : ''}${k.definition ? ' explain' : ''}" data-k="${i}" style="--kpi-color:${na ? 'var(--axis)' : colors[k.status] || 'var(--axis)'}">
        <div class="label"><i></i>${esc(k.label)}${flag}</div>
        <div class="value">${na ? '<span class="na-text">needs data</span>' : fmtValue(k.value, k.unit)}</div>
        ${k.target !== null && k.target !== undefined && !na ? `<div class="target">target ${k.direction === 'down' ? '≤' : '≥'} ${fmtValue(k.target, k.unit)}</div>` : ''}
        ${k.hint ? `<div class="hint">${esc(k.hint)}</div>` : ''}</div>`;
    }).join('');
    $$('[data-k]', host).forEach((el) => {
      const k = kpis[Number(el.dataset.k)];
      if (!k.definition) return;
      el.tabIndex = 0; el.setAttribute('role', 'button'); el.setAttribute('aria-label', `${k.label}: definition`);
      const show = () => modal(k.label, `<p>${esc(k.definition)}</p><dl class="kv"><dt>Formula</dt><dd>${esc(k.formula)}</dd><dt>SAP source</dt><dd>${esc(k.source)}</dd>
        <dt>Target</dt><dd>${k.target === null || k.target === undefined ? 'to be agreed' : `${k.direction === 'down' ? '≤' : '≥'} ${fmtValue(k.target, k.unit)} (${k.direction === 'down' ? 'lower' : 'higher'} is better)`}</dd>
        <dt>Now</dt><dd>${k.available === false ? `not in this SAP snapshot — needs ${esc(k.source)}` : `${fmtValue(k.value, k.unit)} ${pill(k.status)}`}</dd></dl>
        <p class="note">Targets are demo targets until the customer agrees its own definitions, reporting periods and source records.</p>`);
      el.addEventListener('click', show);
      el.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); show(); } });
    });
  }
  function renderChart(spec) {
    const card = document.createElement('div');
    card.className = 'card';
    if (spec.type === 'bar' && spec.rows?.length && spec.rows.every((r) => !r.value)) {  // nothing to plot yet: say so instead of drawing empty axes
      card.innerHTML = `<h2>${esc(spec.title)}</h2><p class="sub">${esc(spec.subtitle || '')}</p><div class="empty">Nothing here yet for this selection.</div>`;
      return card;
    }
    card.appendChild(window.Charts[spec.type](spec));
    return card;
  }

  // ------------------------------------------------------------------ theme, nav, auth
  const applyTheme = (t) => { if (t) document.documentElement.dataset.theme = t; else delete document.documentElement.dataset.theme; };
  applyTheme(local.get('theme'));
  const applyLook = (look) => {
    document.documentElement.dataset.look = look === 'sap' ? 'sap' : 'apple';
    $$('.look-switch button').forEach((b) => { b.classList.toggle('on', b.dataset.look === document.documentElement.dataset.look); b.setAttribute('aria-pressed', String(b.dataset.look === document.documentElement.dataset.look)); });
  };
  const lookParam = new URLSearchParams(location.search).get('look');  // shareable: /?look=sap
  if (lookParam) local.set('look', lookParam);
  applyLook(lookParam || local.get('look'));
  $$('.look-switch button').forEach((b) => b.addEventListener('click', () => { local.set('look', b.dataset.look); applyLook(b.dataset.look); }));
  $('#theme-toggle').addEventListener('click', () => {
    const dark = document.documentElement.dataset.theme ? document.documentElement.dataset.theme === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches;
    const next = dark ? 'light' : 'dark'; local.set('theme', next); applyTheme(next);
  });
  $('#menu-toggle').addEventListener('click', () => $('#sidebar').classList.toggle('open'));

  const PAGES = {
    command: ['Command center', loadCommand], dashboard: ['My role', loadDashboard], moat: ['Intelligence moat', loadMoat], products: ['Product 360', loadProducts], sites: ['Warehouse 360', loadSites],
    map: ['Network map', loadMap],
    inventory: ['Inventory & balancing', () => { if (!$('#balance-out').innerHTML) $('#form-balance').requestSubmit(); }],
    sales: ['Sales order management', loadSales], stocktake: ['Stocktake management', loadStocktake], production: ['Production readiness', loadProduction],
    suppliers: ['Suppliers, quality & logistics', loadSuppliersPage], approvals: ['Approvals & execution', loadApprovals], watches: ['Watchlists', loadWatches],
    chat: ['Copilot chat', null], compare: ['Flowise ⇄ LangGraph', null], workflow: ['Business workflow (LangGraph)', null], research: ['Deep Agent research', loadHarness],
    platform: ['Status & access', loadPlatform], erp: ['ERP / SAP Setup', loadErp], code: ['Backend code', loadCode], rag: ['RAG Tuning', loadRag],
  };
  function route() {
    const [page, arg, arg2] = (location.hash || '#command').slice(1).split('/');
    // Deep links: #dashboard/<persona>[/<material>], #products/<material>
    if (page === 'dashboard' && arg) { state.persona = arg; local.set('persona', arg); }
    if (page === 'dashboard' && arg2 !== undefined) { state.focus = arg2.toUpperCase(); local.set('focus', state.focus); }
    if (page === 'products' && arg) state.product = arg.toUpperCase();
    if (page === 'sites' && arg) { state.site = arg.toUpperCase(); local.set('site', state.site); }
    if (page === 'code' && arg) state.codeKey = decodeURIComponent(arg);
    const [title, loader] = PAGES[page] || PAGES.command;
    $$('.page').forEach((p) => p.classList.toggle('active', p.id === `page-${page}`));
    $$('#nav a').forEach((a) => a.classList.toggle('active', a.dataset.page === page));
    $('#page-title').textContent = title;
    renderPageActions(page in PAGES ? page : 'command');
    $('#sidebar').classList.remove('open');
    if (loader && state.key) loader();
  }
  // One clear primary call to action per page (filled), plus at most one secondary (tinted).
  const PAGE_ACTIONS = {
    command: () => [['Refresh', 'link', loadCommand], ['Review approvals', 'ghost', () => go('approvals')]],  // the spotlight owns the primary CTA
    dashboard: () => [['Open product detail', 'ghost', () => go(state.focus ? `products/${state.focus}` : 'products')],
      [`Ask the ${state.roleView?.agent?.name || 'role agent'}`, 'arrow', () => openDrawer(state.roleView?.agent?.starters?.[0], state.persona)]],
    moat: () => [['Refresh', 'ghost', loadMoat]],
    products: () => [['Ask about this product', 'ghost', () => openDrawer(`What should I do about ${state.product} this week?`)],
      ['Plan stock transfer', 'arrow', () => act({ kind: 'stock_balance', params: { material: state.product } })]],
    sites: () => [['See on map', 'ghost', () => go('map')], ['Ask about this site', 'arrow', () => openDrawer(`What needs attention at ${state.site} this week?`)]],
    map: () => [['Ask about suppliers', 'ghost', () => openDrawer('Which suppliers are delivering later than SAP promises and what should we do?')], ['Open warehouses', 'arrow', () => go('sites')]],
    approvals: () => [['Refresh', 'ghost', loadApprovals]],
    watches: () => [['Check now', '', loadWatches]],
    chat: () => [['New conversation', '', () => $('#new-thread').click()]],
    compare: () => [['New conversations', 'ghost', () => $('#compare-reset').click()]],
  };
  function renderPageActions(page) {
    const host = $('#page-actions');
    const items = (PAGE_ACTIONS[page] || (() => [['Ask copilot', 'ghost', () => openDrawer()]]))();
    host.innerHTML = items.map(([label, cls], i) => `<button type="button" class="${cls}" data-pa="${i}">${esc(label)}</button>`).join('');
    $$('[data-pa]', host).forEach((b) => b.addEventListener('click', () => busy(b, async () => items[Number(b.dataset.pa)][2]())));
  }
  window.addEventListener('hashchange', route);
  const go = (page) => { if (location.hash === `#${page}`) route(); else location.hash = page; };

  async function signIn(key, quiet) {
    state.key = key; session.set('apiKey', key);
    try { await api('/api/v1/kpis'); } catch (e) { state.key = ''; session.set('apiKey', ''); setRole(''); if (!quiet) toast('Sign-in failed: ' + e.message); route(); return; }
    try { await api('/api/v1/audit?limit=1'); setRole('manager'); } catch { setRole('planner'); }
    await loadSuppliers();
    envLine();
    refreshBadges();
    route();
  }
  function setRole(role) {
    state.role = role;
    $('#role-chip').textContent = role || 'signed out';
    if (!state.persona) state.persona = role === 'manager' ? 'executive' : 'inventory';
  }
  $('#login').addEventListener('submit', (e) => { e.preventDefault(); const k = $('#api-key').value.trim(); if (k) signIn(k); $('#api-key').value = ''; });

  // ================================================================ BACKEND CODE (full source of each backend component + its app-type template; edit in VS Code)
  state.codeSide = local.get('codeSide') === '1';
  async function loadCode() {
    if (!state.codeIndex) {
      state.codeIndex = await api('/api/v1/code/files').catch((e) => { toast(e.message); return null; });
      if (!state.codeIndex) return;
    }
    const idx = state.codeIndex;
    const apps = Object.fromEntries(idx.components.map((c) => [c.id, c]));
    const app = state.codeApp && apps[state.codeApp] ? state.codeApp : idx.components[0].id;
    state.codeApp = app;
    $('#code-apps').innerHTML = idx.components.map((c) => `<button class="pill${c.id === app ? ' on' : ''}" data-app="${c.id}">${esc(c.name)} <span class="code-id">${esc(c.kind)} · :${c.port}</span></button>`).join('');
    $$('#code-apps .pill').forEach((b) => b.addEventListener('click', () => { state.codeApp = b.dataset.app; state.codeKey = ''; loadCode(); }));
    const c = apps[app];
    const q = $('#code-q').value.trim().toLowerCase();
    const files = idx.files.filter((f) => f.apps.includes(app) && (!q || f.path.toLowerCase().includes(q) || f.summary.toLowerCase().includes(q)));
    $('#code-count').innerHTML = `<b>${esc(c.name)}</b> (${esc(c.kind)}, port ${c.port}) · ${c.files.length} files · started with <code>${esc(c.start)}</code>
      <label style="display:block;margin-top:6px"><input type="checkbox" id="code-side" ${state.codeSide ? 'checked' : ''}> show the ${esc(c.kind)} template side by side</label>`;
    $('#code-side').addEventListener('change', (e) => { state.codeSide = e.target.checked; local.set('codeSide', state.codeSide ? '1' : ''); showCode(state.codeKey || c.entry.split('::')[0]); });
    // the app-type templates are pinned above the real files
    $('#code-items').innerHTML = `<div class="code-file">Template${c.templates.length > 1 ? 's' : ''} for a ${esc(c.kind)} app</div>`
      + c.templates.map((t) => `<div class="code-item code-tpl${state.codeKey === `tpl:${t}` ? ' on' : ''}" data-path="tpl:${esc(t)}">📄 ${esc(t)}</div>`).join('')
      + `<div class="code-file">Real code (${files.length})</div>`
      + (files.map((f) => `<div class="code-item${f.path === state.codeKey ? ' on' : ''}" data-path="${esc(f.path)}" title="${esc(f.summary)}">${esc(f.path.replace('backend/', ''))} <span class="code-id">${f.lines}</span></div>`).join('') || '<div class="empty">No match.</div>');
    $$('#code-items .code-item').forEach((el) => el.addEventListener('click', () => { location.hash = `code/${encodeURIComponent(el.dataset.path)}`; }));
    const want = state.codeKey && (state.codeKey.startsWith('tpl:') || state.codeKey.endsWith('.py')) ? state.codeKey.split('::')[0] : c.entry.split('::')[0];
    showCode(want);
  }
  let codeTimer;
  $('#code-q').addEventListener('input', () => { clearTimeout(codeTimer); codeTimer = setTimeout(loadCode, 200); });

  const codeLines = (source) => `<pre class="code-view">${source.split('\n').map((line) => `<span>${esc(line) || ' '}</span>`).join('\n')}</pre>`;
  const vscodeLink = (path) => (state.codeIndex.vscode_base ? `<a class="button" href="${esc(`${state.codeIndex.vscode_base.replace(/\/$/, '')}/${path}`)}">Open in VS Code</a>` : '');
  async function codePane(path) {
    // one pane: a real file (backend/...) or a template (tpl:<name>)
    const tpl = path.startsWith('tpl:');
    const f = await api(tpl ? `/api/v1/code/template?name=${encodeURIComponent(path.slice(4))}` : `/api/v1/code/file?path=${encodeURIComponent(path)}`);
    const meta = tpl ? f : (state.codeIndex.files.find((x) => x.path === f.path) || { apps: [] });
    const names = Object.fromEntries(state.codeIndex.components.map((c) => [c.id, c.name]));
    const run = tpl ? (f.source.match(/^(?:Run it|Serve it):\s*(.+)$/m) || [])[1] : '';
    return `<div class="code-pane"><div class="row" style="justify-content:space-between;align-items:center">
        <div><h2 style="margin:0">${tpl ? `${badge('plan', 'template')} ` : ''}${esc(f.path)}</h2>
          <p class="sub">${f.lines} lines · ${tpl ? 'starter template, not part of the running app' : `runs in ${meta.apps.map((a) => chip(names[a] || a)).join(' ') || 'no app'}`}${meta.summary ? ` · ${esc(meta.summary)}` : ''}</p>
          ${run ? `<p class="note">Run it: <code>${esc(run.trim())}</code></p>` : ''}</div>
        <div class="row">${vscodeLink(f.path)}<button class="ghost small" data-copy="${esc(f.path)}">Copy path</button></div></div>
      ${codeLines(f.source)}</div>`;
  }
  async function showCode(path) {
    const host = $('#code-detail');
    state.codeKey = path;
    $$('#code-items .code-item').forEach((el) => el.classList.toggle('on', el.dataset.path === path));
    const app = state.codeIndex.components.find((c) => c.id === state.codeApp);
    const side = state.codeSide && !path.startsWith('tpl:') && app?.templates.length;
    try {
      const panes = await Promise.all([codePane(path), ...(side ? [codePane(`tpl:${app.templates[0]}`)] : [])]);
      host.innerHTML = side ? `<div class="code-split">${panes.join('')}</div>` : panes[0];
    } catch (e) { host.innerHTML = `<div class="empty">${esc(e.message)}</div>`; return; }
    $$('[data-copy]', host).forEach((b) => b.addEventListener('click', () => { navigator.clipboard?.writeText(b.dataset.copy).then(() => toast('Path copied.'), () => toast(b.dataset.copy)); }));
  }

  // ================================================================ RAG TUNING (Company RAG Search; SCInsight API through the gateway)
  const RAG = '/api/v1/rag-tuning';
  state.ragTab = 'knowledge';
  const ragPane = () => $('#rag-pane');
  // Every tunable setting, the stage it belongs to and how it is edited. cold = needs a new index, hot = query time.
  const RAG_FIELDS = {
    category_filter: { stage: 'knowledge', label: 'Document categories searched', type: 'categories', help: 'Empty = every category the caller may read. Can only narrow access, never widen it.' },
    chunk_strategy: { stage: 'chunking', label: 'Chunking strategy', type: 'select', options: ['section', 'clause', 'fixed'], help: 'section = split on ## headings, then windows · clause = whole sentences (keeps a rule with its condition) · fixed = windows over the whole document' },
    chunk_size: { stage: 'chunking', label: 'Chunk size (characters)', type: 'number', min: 50, max: 4000, step: 50, help: 'Presets: small 300 · medium 600 · large 1000 (starting points, not optimal values)' },
    chunk_overlap: { stage: 'chunking', label: 'Overlap (characters)', type: 'number', min: 0, max: 2000, step: 10, help: 'Repeated between neighbouring chunks; must be smaller than the chunk size' },
    preserve_headings: { stage: 'chunking', label: 'Prefix "title — section"', type: 'bool', help: 'Gives short sections their context' },
    preserve_source_ids: { stage: 'chunking', label: 'Prefix [doc id + version]', type: 'bool', help: 'Puts the citation id inside the chunk text' },
    embedding_model: { stage: 'embeddings', label: 'Embedding model', type: 'model', help: 'Approved models only; another model always gets its own index' },
    top_k: { stage: 'retrieval', label: 'Top-K passages', type: 'number', min: 1, max: 10, step: 1, help: 'Presets 3 / 5 / 8' },
    similarity_threshold: { stage: 'retrieval', label: 'Similarity threshold', type: 'nullnum', min: -1, max: 1, step: 0.01, help: 'Blank = none. Cosine similarity of this model (not a probability)' },
    retrieval_mode: { stage: 'retrieval', label: 'Retrieval mode', type: 'select', options: ['semantic', 'keyword', 'hybrid'], help: 'keyword = query-term overlap · hybrid = weighted mix' },
    hybrid_alpha: { stage: 'retrieval', label: 'Hybrid semantic weight', type: 'number', min: 0, max: 1, step: 0.05, help: 'Only used in hybrid mode' },
    rerank: { stage: 'retrieval', label: 'Reranking', type: 'select', options: ['none', 'lexical'], help: 'lexical = deterministic term-overlap reorder of the candidates' },
    candidate_k: { stage: 'retrieval', label: 'Candidates before filtering', type: 'number', min: 1, max: 100, step: 1, help: 'Scored before access filter / rerank; at least Top-K' },
    max_context_tokens: { stage: 'retrieval', label: 'Max context tokens', type: 'nullnum', min: 50, max: 8000, step: 50, help: 'Blank = no budget (approximate tokens = characters / 4)' },
  };
  const isCold = (f) => (state.rag?.cold_fields || []).includes(f);
  const same = (a, b) => JSON.stringify(a ?? null) === JSON.stringify(b ?? null);
  const fmtVal = (v) => (v === null || v === undefined ? '—' : Array.isArray(v) ? (v.length ? v.join(', ') : 'all') : typeof v === 'boolean' ? (v ? 'yes' : 'no') : String(v));
  const cfgLine = (c) => c ? `${esc(c.chunk_strategy)} ${c.chunk_size}/${c.chunk_overlap} chars · ${esc(c.embedding_model)} · top ${c.top_k} · ${esc(c.retrieval_mode)}${c.similarity_threshold !== null && c.similarity_threshold !== undefined ? ` · threshold ${c.similarity_threshold}` : ''}${c.rerank !== 'none' ? ` · rerank ${esc(c.rerank)}` : ''}` : '—';
  const diffKeys = (a, b) => Object.keys(RAG_FIELDS).filter((k) => !same(a?.[k], b?.[k]));
  const diffChips = (c, base) => { const d = diffKeys(base, c); return d.length ? d.map((k) => `<span class="chip rag-chg">${esc(RAG_FIELDS[k].label)}: ${esc(fmtVal(base[k]))} → <b>${esc(fmtVal(c[k]))}</b></span>`).join(' ') : '<span class="note">same as active</span>'; };
  const sev = (s) => pill(s === 'error' ? 'critical' : s === 'warning' ? 'warning' : 'info', s);
  async function pollJob(job, onDone, host) {
    const show = (j) => { if (host) host.innerHTML = `<p class="note">Job ${esc(j.id)} · ${esc(j.kind)} · <b>${esc(j.status)}</b>${j.error ? ` · ${esc(j.error)}` : ''}</p>`; };
    let j = job;
    for (let i = 0; i < 400 && (j.status === 'running' || j.status === 'queued'); i += 1) {
      show(j);
      await new Promise((r) => setTimeout(r, 1500));
      j = await api(`${RAG}/jobs/${j.id}`);
    }
    show(j);
    if (j.status === 'failed') { toast(`${j.kind} failed: ${j.error}`); return null; }
    if (onDone) onDone(j.result);
    return j.result;
  }

  async function loadRag() {
    if (!state.role) { ragPane().innerHTML = '<div class="empty">Sign in to use RAG tuning.</div>'; return; }
    try {
      state.rag = await api(`${RAG}/config`);
    } catch (e) { ragPane().innerHTML = `<div class="empty">${esc(e.message)}</div>`; return; }
    const a = state.rag.active;
    // the working draft starts as a copy of the active configuration and survives tab changes
    if (!state.ragDraft || state.ragDraftBase !== a.id) { state.ragDraft = JSON.parse(JSON.stringify(a.config)); state.ragDraftBase = a.id; }
    $('#rag-active').innerHTML = `<div class="grid g3">
      <div><div class="eyebrow">Active configuration (live)</div><b>${esc(a.id)}</b> ${esc(a.name)} ${badge('ready', 'active')}<div class="note">since ${esc(a.published_at || a.created_at)} by ${esc(a.published_by || a.created_by)}</div></div>
      <div><div class="eyebrow">Index version</div><b>${esc(a.index_version)}</b><div class="note">${cfgLine(a.config)}</div></div>
      <div><div class="eyebrow">Units</div><div class="note">Chunk sizes in <b>${esc(state.rag.chunk_unit)}</b>. Score: ${esc(state.rag.score_metric)}.</div></div></div>`;
    $('#rag-path').innerHTML = state.rag.retrieval_path.map((p) => `<li>${esc(p)}</li>`).join('');
    renderDraftBar();
    renderRagTab();
  }
  $$('#rag-tabs .pill').forEach((b) => b.addEventListener('click', () => {
    state.ragTab = b.dataset.tab;
    $$('#rag-tabs .pill').forEach((x) => x.classList.toggle('on', x === b));
    renderRagTab();
  }));
  function renderRagTab() {
    ({ knowledge: ragKnowledge, chunking: ragChunking, embeddings: ragEmbeddings, retrieval: ragRetrieval, evaluation: ragEvaluation, publish: ragPublish })[state.ragTab]()
      .catch((e) => { ragPane().innerHTML = `<div class="empty">${esc(e.message)}</div>`; });
  }
  async function ragDocs(fresh) { if (fresh || !state.ragDocs) state.ragDocs = await api(`${RAG}/documents`); return state.ragDocs; }

  // ---- working draft: one profile edited across every stage, saved as one configuration
  function renderDraftBar() {
    const a = state.rag.active.config, d = state.ragDraft;
    const changed = diffKeys(a, d);
    const cold = changed.filter(isCold);
    $('#rag-draftbar').innerHTML = changed.length
      ? `<div class="card rag-draft"><div class="row" style="justify-content:space-between;align-items:center">
          <div><b>Working draft</b>: ${changed.length} change${changed.length > 1 ? 's' : ''} vs active ${cold.length ? badge('at_risk', 'needs a new index') : badge('ready', 'query-time only')}<div style="margin-top:6px">${diffChips(d, a)}</div></div>
          <div class="row"><input id="rag-draft-name" placeholder="Profile name (e.g. threshold 0.66)" style="min-width:240px"><button id="rag-draft-save">Save as profile</button><button class="ghost" id="rag-draft-reset">Reset to active</button></div></div>
          <div id="rag-draft-msg"></div></div>`
      : '<p class="note rag-draft-empty">Working draft = active configuration. Edit the settings in any stage below; your changes are collected here and saved as one profile.</p>';
    if (!changed.length) return;
    $('#rag-draft-reset').addEventListener('click', () => { state.ragDraft = JSON.parse(JSON.stringify(a)); renderDraftBar(); renderRagTab(); });
    $('#rag-draft-save').addEventListener('click', (e) => busy(e.currentTarget, async () => {
      if (d.chunk_overlap >= d.chunk_size) { toast('Overlap must be smaller than the chunk size.'); return; }
      const name = $('#rag-draft-name').value.trim() || changed.map((k) => `${k} ${fmtVal(d[k])}`).join(', ').slice(0, 80);
      await ragSaveDraft({ ...d, candidate_k: Math.max(d.candidate_k, d.top_k) }, '#rag-draft-msg', name);
    }));
  }
  async function ragSaveDraft(cfg, target, name) {
    const r = await api(`${RAG}/draft`, { method: 'PUT', body: { config: cfg, name } });
    const d = r.diff;
    $(target).innerHTML = `<div class="note" style="margin-top:8px"><b>Profile ${esc(r.id)} · ${esc(r.name)}</b> saved. ${d.needs_new_index
      ? `It changes index settings (${d.rebuild_required.map(chip).join(' ')}): build its candidate index, then benchmark it.` : 'Query-time change only: it reuses the active index.'}
      <button class="small" id="rag-build-${esc(r.id)}">Build candidate index</button> <span id="rag-job-${esc(r.id)}"></span></div>`;
    $(`#rag-build-${r.id}`).addEventListener('click', (e) => busy(e.currentTarget, async () => {
      const job = await api(`${RAG}/index/build-candidate`, { body: { config_id: r.id } });
      await pollJob(job, (res) => toast(res.reused ? `${r.id} reuses the active index — next: Evaluation lab.` : `Index ${res.index_version}: ${res.documents} documents, ${res.chunks} chunks — next: Evaluation lab.`), $(`#rag-job-${r.id}`));
    }));
    return r;
  }
  // Editable settings of one stage: active value | working draft | effect | help. Changed rows are highlighted.
  function settingsCard(stage, extra = {}) {
    const a = state.rag.active.config, d = state.ragDraft;
    const input = (k, f) => {
      const v = d[k];
      if (f.type === 'select') return `<select data-f="${k}">${f.options.map((o) => `<option ${o === v ? 'selected' : ''}>${o}</option>`).join('')}</select>`;
      if (f.type === 'model') return `<select data-f="${k}">${(extra.models || [{ id: v }]).map((m) => `<option value="${esc(m.id)}" ${m.id === v ? 'selected' : ''}>${esc(m.id)}${m.dims ? ` (${m.dims} dims${m.installed === false ? ', not installed' : ''})` : ''}</option>`).join('')}</select>`;
      if (f.type === 'bool') return `<input type="checkbox" data-f="${k}" ${v ? 'checked' : ''}>`;
      if (f.type === 'categories') return (extra.categories || []).map((c) => `<label class="chip"><input type="checkbox" data-cat="${esc(c)}" ${(v || []).includes(c) ? 'checked' : ''}> ${esc(c)}</label>`).join(' ') || '<span class="note">no categories</span>';
      return `<input type="number" data-f="${k}" min="${f.min}" max="${f.max}" step="${f.step}" value="${v ?? ''}" ${f.type === 'nullnum' ? 'placeholder="none"' : ''} style="width:120px">`;
    };
    const rows = Object.entries(RAG_FIELDS).filter(([, f]) => f.stage === stage);
    return `<div class="rag-settings"><h4 style="margin-top:0">Current settings — ${esc(stage)} <span class="note">(active ${esc(state.rag.active.id)} · edit the right column; changes go to the working draft)</span></h4>
      <div class="scroll"><table><thead><tr><th>Setting</th><th>Active (live)</th><th>Working draft</th><th>Takes effect</th><th>Notes</th></tr></thead><tbody>
      ${rows.map(([k, f]) => `<tr data-row="${k}" class="${same(a[k], d[k]) ? '' : 'rag-changed'}"><td><b>${esc(f.label)}</b><br><span class="note">${k}</span></td><td>${esc(fmtVal(a[k]))}</td><td>${input(k, f)}</td>
        <td>${isCold(k) ? badge('at_risk', 'new index') : badge('ready', 'query time')}</td><td class="note">${esc(f.help || '')}</td></tr>`).join('')}
      </tbody></table></div></div>`;
  }
  function bindSettings(host) {
    const update = (k, v) => {
      state.ragDraft[k] = v;
      const row = $(`[data-row="${k}"]`, host);
      if (row) row.classList.toggle('rag-changed', !same(state.rag.active.config[k], v));
      renderDraftBar();
    };
    $$('[data-f]', host).forEach((el) => el.addEventListener('change', () => {
      const k = el.dataset.f, f = RAG_FIELDS[k];
      update(k, f.type === 'bool' ? el.checked : f.type === 'number' ? +el.value : f.type === 'nullnum' ? (el.value === '' ? null : +el.value) : el.value);
    }));
    $$('[data-cat]', host).forEach((el) => el.addEventListener('change', () => update('category_filter', $$('[data-cat]', host).filter((x) => x.checked).map((x) => x.dataset.cat))));
  }

  // ---- 1. knowledge & metadata
  async function ragKnowledge() {
    const inv = await ragDocs(true);
    const categories = [...new Set(inv.documents.map((d) => d.category))].sort();
    ragPane().innerHTML = `${settingsCard('knowledge', { categories })}
      <div class="row" style="justify-content:space-between;margin-top:14px"><p class="note">${inv.summary.documents} documents of tenant <b>${esc(inv.tenant)}</b> · ${inv.summary.chunks} chunks in index <b>${esc(inv.index_version)}</b> (${esc(inv.embedding_model)}) · ${inv.summary.with_issues} with issues · ${inv.summary.rejected} rejected. Other tenants' documents are never listed. Metadata comes from each document's front matter (data/scinsight/knowledge).</p>
      <button id="rag-validate">Run metadata &amp; source-quality checks</button></div>
      ${table([['Document', (d) => `<b>${esc(d.doc_id)}</b><br><span class="note">${esc(d.title)}</span>`], ['Source', (d) => `<span class="note">${esc(d.source)}</span>`],
        ['Tenant', (d) => esc(d.tenant)], ['Type', (d) => esc(d.category)], ['Version', (d) => esc(d.version)], ['Effective', (d) => `${esc(d.valid_from)} → ${esc(d.valid_to || 'open')}`],
        ['Approval', (d) => d.approval_status ? esc(d.approval_status) : '<span class="note">missing</span>'], ['Access', (d) => d.access_roles.map(chip).join(' ')],
        ['Ingested', (d) => `<span class="note">${esc(d.ingested_at || 'not indexed')}</span>${d.indexed_sha_matches ? '' : ' ' + badge('at_risk', 'changed since indexing')}`],
        ['Metadata used', (d) => `${d.metadata.map((m) => `<span class="chip${m.used_for === 'stored only' ? ' rag-meta-stored' : ''}" title="${esc(m.field)} = ${esc(m.value)} · ${esc(m.used_for)}">${esc(m.field)}</span>`).join(' ')}${d.metadata_missing.length ? `<div class="note">missing: ${esc(d.metadata_missing.join(', '))}</div>` : ''}`],
        ['Chunks', (d) => num(d.chunks), 'num'], ['Index', (d) => esc(d.index_version)], ['Flowise RAG DB', (d) => d.in_flowise_rag_db ? 'yes' : 'no'],
        ['Issues', (d) => d.issues.length ? d.issues.map((i) => sev(i.severity)).join(' ') : badge('ready', 'none')],
        ['', (d) => `<button class="ghost small" data-src="${esc(d.doc_id)}">Preview</button>`]], inv.documents)}
      <h4>Metadata by document type</h4>
      ${table([['Document type', (t) => `<b>${esc(t.category)}</b>`], ['Documents', (t) => t.documents, 'num'],
        ['Fields used → what the search does with them', (t) => t.fields.map((f) => `<span class="chip${f.used_for === 'stored only' ? ' rag-meta-stored' : ''}">${esc(f.field)} <span class="note">→ ${esc(f.used_for)}</span></span>`).join(' ')],
        ['Missing (required / recommended)', (t) => t.missing.length ? esc(t.missing.join(', ')) : badge('ready', 'none')]], inv.metadata_by_type)}
      ${inv.rejected.length ? `<h4>Rejected by ingestion</h4>${table([['File', (r) => esc(r.source)], ['Problem', (r) => esc(r.error)], ['Fields present', (r) => esc(r.present_fields.join(', ') || 'none')]], inv.rejected)}` : ''}
      <div id="rag-issues"></div>`;
    bindSettings(ragPane());
    $$('[data-src]', ragPane()).forEach((b) => b.addEventListener('click', async () => {
      const s = await api(`${RAG}/documents/${encodeURIComponent(b.dataset.src)}/source`).catch((e) => toast(e.message));
      if (s) modal(`${s.doc_id} · ${s.source}`, `<p class="note">${esc(JSON.stringify(s.meta))}</p><pre class="code-box">${esc(s.body)}</pre>`);
    }));
    $('#rag-validate').addEventListener('click', (e) => busy(e.currentTarget, async () => {
      const r = await api(`${RAG}/metadata/validate`, { method: 'POST' });
      $('#rag-issues').innerHTML = `<h4>Checks on ${esc(r.business_date)}: ${r.errors} errors, ${r.warnings} warnings</h4><p class="note">${Object.entries(r.by_check).map(([k, v]) => `${esc(k)}: ${v}`).join(' · ')}</p>
        ${table([['Document', (i) => esc(i.doc_id)], ['Severity', (i) => sev(i.severity)], ['Check', (i) => esc(i.check)], ['Detail', (i) => esc(i.detail)]], r.issues)}`;
    }));
  }

  // ---- 2. chunking
  async function ragChunking() {
    const inv = await ragDocs();
    ragPane().innerHTML = `${settingsCard('chunking')}
      <div class="row" style="margin-top:10px">${Object.entries(state.rag.presets).map(([k, v]) => `<button class="ghost small" data-preset="${k}">${esc(k)} ${v.chunk_size}/${v.chunk_overlap}</button>`).join('')}
        <label>Document <select id="rag-doc">${inv.documents.map((d) => `<option value="${esc(d.doc_id)}" ${d.doc_id === 'POL-PROC-001' ? 'selected' : ''}>${esc(d.doc_id)} · ${esc(d.title)}</option>`).join('')}</select></label>
        <button id="rag-chunk-preview">Preview working draft vs active</button></div>
      <p class="note">Preview only: nothing is written. Sizes are characters; token counts are approximate.</p>
      <div class="grid g2" id="rag-chunk-out"></div>`;
    bindSettings(ragPane());
    $$('[data-preset]').forEach((b) => b.addEventListener('click', () => { Object.assign(state.ragDraft, state.rag.presets[b.dataset.preset]); renderDraftBar(); ragChunking(); }));
    const col = (title, p) => `<div><h4>${esc(title)}: ${p.count} chunks · avg ${p.avg_chars} chars</h4>${p.chunks.map((c) => `<div class="card" style="margin:6px 0;padding:10px">
      <div class="note"><b>${esc(c.chunk_id)}</b> · ${esc(c.section)} · ${c.chars} chars · ~${c.approx_tokens} tokens${c.overlap_with_previous ? ` · ${c.overlap_with_previous} chars overlap with previous` : ''}</div>
      <pre class="code-box" style="min-height:0;max-height:180px">${esc(c.text)}</pre></div>`).join('')}</div>`;
    $('#rag-chunk-preview').addEventListener('click', (e) => busy(e.currentTarget, async () => {
      const cfg = { ...state.ragDraft, candidate_k: Math.max(state.ragDraft.candidate_k, state.ragDraft.top_k) };
      if (cfg.chunk_overlap >= cfg.chunk_size) { toast('Overlap must be smaller than the chunk size.'); return; }
      const r = await api(`${RAG}/chunks/preview`, { body: { doc_id: $('#rag-doc').value, config: cfg, compare_with: state.rag.active.config } });
      $('#rag-chunk-out').innerHTML = col('Working draft', r.preview) + col(`Active (${state.rag.active.id})`, r.compare);
    }));
  }

  // ---- 3. embeddings
  async function ragEmbeddings() {
    const m = await api(`${RAG}/embedding-models`);
    ragPane().innerHTML = `${settingsCard('embeddings', { models: m.models })}
      <p class="note" style="margin-top:12px">${esc(m.note)} The Flowise chatflow RAG DB can only follow BAAI/bge-small-en-v1.5 (the model the gateway serves).</p>
      ${table([['Model', (x) => `<b>${esc(x.id)}</b>${x.active ? ' ' + badge('ready', 'active') : ''}<br><span class="note">${esc(x.role)}</span>`], ['Provider', (x) => esc(x.provider)],
        ['Dimensions', (x) => num(x.dims), 'num'], ['Languages', (x) => esc(x.languages)], ['Installed', (x) => x.installed ? badge('ready', 'installed') : badge('not_configured', 'not installed')],
        ['', (x) => `<button class="ghost small" data-test="${esc(x.id)}">Test loading</button>`]], m.models)}
      <div id="rag-emb-out"></div>`;
    bindSettings(ragPane());
    $$('[data-test]').forEach((b) => b.addEventListener('click', (e) => busy(e.currentTarget, async () => {
      const job = await api(`${RAG}/embedding-models/test`, { body: { model: b.dataset.test } });
      await pollJob(job, (r) => { $('#rag-emb-out').innerHTML = `<div class="card"><h4>${esc(r.model)}</h4><p>Loaded in ${num(r.load_ms, 1)} ms · ${num(r.embed_ms_per_text, 2)} ms per text · dimensions ${esc(r.dims.join(', '))} (expected ${r.expected_dims}) ${r.dims_ok ? badge('ready', 'dimensions ok') : badge('blocked', 'dimension mismatch')} · norms ${esc(r.norms.join(', '))}</p><p class="note">first values: ${esc(JSON.stringify(r.sample_head))}</p></div>`; }, $('#rag-emb-out'));
    })));
  }

  // ---- 4. retrieval
  async function ragRetrieval() {
    const pendingCold = diffKeys(state.rag.active.config, state.ragDraft).filter(isCold);
    ragPane().innerHTML = `${settingsCard('retrieval')}
      <div class="row" style="margin-top:10px">${state.rag.top_k_presets.map((k) => `<button class="ghost small" data-k="${k}">Top-K ${k}</button>`).join('')}</div>
      <form id="rag-q" class="grid g3" onsubmit="return false">
        <label style="grid-column:1/-1">Procurement question <input name="query" value="Who must approve a warehouse stock transfer?"></label>
        <label>Retrieve as role (access test) <select name="role">${state.role === 'manager' ? '<option value="">my roles (director)</option>' : ''}${['planner', 'warehouse_manager', 'procurement_manager', 'quality_manager', 'production_planner', 'agent_service'].map((r) => `<option>${r}</option>`).join('')}</select></label>
      </form>
      ${pendingCold.length ? `<p class="note">${badge('at_risk', 'note')} The working draft also changes index settings (${pendingCold.map(chip).join(' ')}): this preview runs on the active index with the draft's query-time settings. Save the profile and build its index to test those.</p>` : ''}
      <div class="row"><button id="rag-run">Retrieve with the working draft</button></div>
      <div id="rag-r-out"></div>`;
    bindSettings(ragPane());
    const f = $('#rag-q');
    $$('[data-k]').forEach((b) => b.addEventListener('click', () => { state.ragDraft.top_k = +b.dataset.k; state.ragDraft.candidate_k = Math.max(state.ragDraft.candidate_k, state.ragDraft.top_k); renderDraftBar(); ragRetrieval(); }));
    $('#rag-run').addEventListener('click', (e) => busy(e.currentTarget, async () => {
      const d = state.ragDraft;
      const overrides = Object.fromEntries(state.rag.hot_fields.map((k) => [k, d[k]]));
      overrides.candidate_k = Math.max(d.candidate_k, d.top_k);
      const r = await api(`${RAG}/retrieve/preview`, { body: { query: f.query.value, overrides, roles: f.role.value ? [f.role.value] : [] } });
      $('#rag-r-out').innerHTML = `<p class="note">Index ${esc(r.index_version)} · ${esc(r.embedding_model)} · roles ${esc(r.roles_used.join(', '))} · latency: embed ${r.latency_ms.embed} ms, retrieve ${r.latency_ms.retrieve} ms, total ${r.latency_ms.total} ms</p>
        <p class="note">${esc(r.score_note)}</p>
        ${table([['#', (h) => h._rank, 'num'], ['Document', (h) => `<b>${esc(h.citation.doc_id)}</b> v${esc(h.citation.version)}`], ['Title · section', (h) => `${esc(h.citation.title)}<br><span class="note">${esc(h.citation.section)} · chunk ${h.citation.chunk}</span>`],
          ['Score', (h) => num(h.score, 4), 'num'], ['Semantic', (h) => num(h.semantic_score, 4), 'num'], ['Keyword', (h) => num(h.keyword_score, 2), 'num'], ['Rerank', (h) => h.rerank_score === null ? '—' : num(h.rerank_score, 2), 'num'],
          ['Text', (h) => `<span class="note">${esc(h.text.slice(0, 260))}${h.text.length > 260 ? '…' : ''}</span>${h.flags.length ? ' ' + badge('at_risk', 'instruction-like text') : ''}`],
          ['Metadata', (h) => `${esc(h.category)} · ${esc(h.citation.valid_from)}→${esc(h.citation.valid_to || 'open')} · ~${h.approx_tokens} tok`], ['Access', () => badge('ready', 'allowed')]], r.results.map((h, i) => ({ ...h, _rank: i + 1 })))}
        <h4>Excluded (${r.excluded.length})</h4>${table([['Document', (x) => esc(x.doc_id)], ['Section', (x) => esc(x.section)], ['Score', (x) => num(x.score, 4), 'num'], ['Reason', (x) => badge(x.reason === 'below threshold' || x.reason === 'context budget' ? 'plan' : 'blocked', x.reason)]], r.excluded.slice(0, 30))}`;
    }));
  }

  // ---- 5. evaluation lab: profiles, their settings, their latest results, and a named comparison
  const METRICS = [
    ['hit_rate', 'Hit rate@K', 'a relevant policy is among the passages returned', 1], ['recall', 'Recall@K', 'share of the relevant policies found', 1],
    ['precision', 'Precision@K', 'share of the K slots filled by a relevant policy (fewer passages lower it)', 1], ['mrr', 'MRR', '1 = the first passage is relevant', 1],
    ['evidence_coverage', 'Evidence', 'expected facts present in the passages', 1], ['no_evidence_pass', 'No-evidence', 'nothing returned when no policy answers the question', 1],
    ['version_accuracy', 'Version', 'cites the effective policy version', 1], ['leakage', 'Leakage', 'passages the role / tenant must not see (must be 0)', -1],
    ['latency_mean_ms', 'Mean ms', 'average time per question', -1], ['latency_p95_ms', 'P95 ms', '95% of questions are faster than this', -1],
    ['answer_fact_coverage', 'Answer facts', 'Qwen answer contains the expected facts', 1], ['citation_correctness', 'Answer citations', 'Qwen cites retrieved, relevant policies', 1],
  ];
  async function ragEvaluation() {
    const [hist, ex] = await Promise.all([api(`${RAG}/history`), api(`${RAG}/experiments`)]);
    const active = hist.versions.find((v) => v.status === 'active');
    const profiles = hist.versions.filter((v) => v.status !== 'failed');
    const latest = {};
    ex.experiments.forEach((e) => { if (!latest[e.config_id]) latest[e.config_id] = e; });
    const byId = Object.fromEntries(profiles.map((v) => [v.id, v]));
    const name = (id) => byId[id] ? `${byId[id].name} (${id})` : id;
    const s = (e, k, d = 3) => (e ? num(e.summary[k], d) : '—');
    const candidates = profiles.filter((v) => v.id !== active.id && latest[v.id]);
    ragPane().innerHTML = `<div class="card rag-explain"><b>How it works.</b> A <b>profile</b> is one saved configuration (chunking + embeddings + retrieval settings). The lab runs the same 15 labelled questions (dataset <b>v1</b>, incl. one the corpus cannot answer, one about another tenant and one a role may not read) through the live search with each profile, then compares the <b>active</b> profile with a <b>candidate</b>.</div>
      <h4>1 · Profiles and their latest benchmark</h4>
      ${table([['', (v) => `<input type="checkbox" class="rag-pick" value="${esc(v.id)}" ${v.status === 'active' || !latest[v.id] ? 'checked' : ''}>`],
        ['Profile', (v) => `<b>${esc(v.name)}</b> ${v.status === 'active' ? badge('ready', 'active') : badge('plan', v.status)}<br><span class="note">${esc(v.id)} · index ${esc(v.index_version || 'not built')}</span>`],
        ['Settings', (v) => `<span class="note">${cfgLine(v.config)}</span>`], ['Differs from active', (v) => v.id === active.id ? '<span class="note">reference</span>' : diffChips(v.config, active.config)],
        ['Benchmarked', (v) => latest[v.id] ? `<span class="note">${esc(latest[v.id].created_at)}</span>` : '<span class="note">not yet</span>'],
        ['Hit@K', (v) => s(latest[v.id], 'hit_rate'), 'num'], ['Recall@K', (v) => s(latest[v.id], 'recall'), 'num'], ['No-evidence', (v) => s(latest[v.id], 'no_evidence_pass'), 'num'],
        ['Leakage', (v) => (latest[v.id] ? (latest[v.id].summary.leakage ? badge('blocked', String(latest[v.id].summary.leakage)) : '0') : '—'), 'num'], ['P95 ms', (v) => s(latest[v.id], 'latency_p95_ms', 1), 'num']], profiles)}
      <div class="row"><button id="rag-bench">Benchmark the ticked profiles</button><label><input type="checkbox" id="rag-answers"> also generate answers with Qwen (slow)</label></div>
      <div id="rag-bench-job"></div>
      <h4>2 · Compare</h4>
      <div class="row"><label>Reference <select id="rag-ref">${profiles.filter((v) => latest[v.id]).map((v) => `<option value="${esc(v.id)}" ${v.id === active.id ? 'selected' : ''}>${esc(v.name)} · ${esc(v.status)} (${esc(v.id)})</option>`).join('')}</select></label>
        <span>vs</span><label>Candidate <select id="rag-cand">${candidates.map((v, i) => `<option value="${esc(v.id)}" ${i === 0 ? 'selected' : ''}>${esc(v.name)} · ${esc(v.status)} (${esc(v.id)})</option>`).join('') || '<option value="">benchmark a candidate first</option>'}</select></label>
        <button id="rag-compare">Compare latest results</button></div>
      <div id="rag-compare-out"></div>
      <details class="more"><summary>All benchmark runs (${ex.experiments.length})</summary>
        ${table([['Run', (e) => `<b>${esc(e.id)}</b><br><span class="note">${esc(e.created_at)}</span>`], ['Profile', (e) => esc(name(e.config_id))], ['Settings', (e) => `<span class="note">${cfgLine(e.params.config)}</span>`],
          ...METRICS.slice(0, 10).map(([k, label, , dir]) => [label, (e) => (k === 'leakage' ? String(e.summary.leakage) : s(e, k, dir < 0 ? 1 : 3)), 'num'])], ex.experiments)}</details>
      <details class="more"><summary>Grid experiment (chunk presets × Top-K)</summary>
        <div class="row">${Object.keys(state.rag.presets).map((p) => `<label class="chip"><input type="checkbox" data-gp="${p}" checked> ${p}</label>`).join('')} ${state.rag.top_k_presets.map((k) => `<label class="chip"><input type="checkbox" data-gk="${k}" checked> top ${k}</label>`).join('')}
          <button class="ghost" id="rag-grid">Estimate workload</button></div><div id="rag-grid-out"></div></details>`;
    $('#rag-bench').addEventListener('click', (e) => busy(e.currentTarget, async () => {
      const ids = $$('.rag-pick', ragPane()).filter((x) => x.checked).map((x) => x.value);
      if (!ids.length) { toast('Tick at least one profile.'); return; }
      const job = await api(`${RAG}/evaluate`, { body: { config_ids: ids, with_answers: $('#rag-answers').checked } });
      await pollJob(job, () => ragEvaluation(), $('#rag-bench-job'));
    }));
    $('#rag-compare').addEventListener('click', (e) => busy(e.currentTarget, async () => {
      const ref = $('#rag-ref').value, cand = $('#rag-cand').value;
      if (!ref || !cand || !latest[ref] || !latest[cand]) { toast('Benchmark both profiles first.'); return; }
      const c = await api(`${RAG}/experiments/compare?active=${latest[ref].id}&candidate=${latest[cand].id}`);
      const row = Object.fromEntries(c.rows.map((r) => [r.metric, r]));
      const better = (k, dir) => { const r = row[k]; if (!r || typeof r.active !== 'number' || typeof r.candidate !== 'number' || r.active === r.candidate) return '<span class="note">same</span>'; return (r.candidate - r.active) * dir > 0 ? badge('ready', 'candidate better') : badge('at_risk', 'reference better'); };
      $('#rag-compare-out').innerHTML = `<div class="card"><h4>${c.passed ? badge('ready', 'meets the publish criteria') : badge('blocked', 'does not meet the publish criteria')} ${esc(byId[cand].name)} vs ${esc(byId[ref].name)}</h4>
        <p><b>${esc(c.recommendation)}</b></p>
        <p class="note">What changes: ${diffChips(byId[cand].config, byId[ref].config)}</p>
        ${table([['Metric', (m) => `<b>${esc(m[1])}</b>`], ['What it means', (m) => `<span class="note">${esc(m[2])}</span>`], [`Reference · ${byId[ref].name}`, (m) => esc(fmtVal(row[m[0]]?.active)), 'num'],
          [`Candidate · ${byId[cand].name}`, (m) => esc(fmtVal(row[m[0]]?.candidate)), 'num'], ['', (m) => better(m[0], m[3])]], METRICS.filter((m) => row[m[0]]))}
        <details class="more"><summary>Publish criteria</summary>${table([['Check', (x) => esc(x.check)], ['Result', (x) => x.ok ? badge('ready', 'pass') : badge('blocked', 'fail')], ['Detail', (x) => esc(x.detail)]], c.checks)}</details>
        <p class="note">${esc(c.basis)}</p></div>`;
    }));
    $('#rag-grid').addEventListener('click', (e) => busy(e.currentTarget, async () => {
      const body = { presets: $$('[data-gp]').filter((x) => x.checked).map((x) => x.dataset.gp), top_k: $$('[data-gk]').filter((x) => x.checked).map((x) => +x.dataset.gk) };
      const w = await api(`${RAG}/evaluate/grid`, { body });
      $('#rag-grid-out').innerHTML = `<p>${w.workload.configurations} profiles · ${w.workload.index_builds} index builds · ${w.workload.queries} queries · about ${w.workload.estimated_seconds} s (${esc(w.workload.basis)})</p><button id="rag-grid-run">Run this grid</button><div id="rag-grid-job"></div>`;
      $('#rag-grid-run').addEventListener('click', (ev) => busy(ev.currentTarget, async () => {
        const job = await api(`${RAG}/evaluate/grid`, { body: { ...body, confirm: true } });
        await pollJob(job, () => ragEvaluation(), $('#rag-grid-job'));
      }));
    }));
  }

  // ---- 6. publish, history, rollback, monitoring
  async function ragPublish() {
    const [hist, fl, mt] = await Promise.all([api(`${RAG}/history`), api(`${RAG}/flowise`), api(`${RAG}/metrics`)]);
    const canPublish = state.role === 'manager';
    const active = hist.versions.find((v) => v.status === 'active');
    ragPane().innerHTML = `<p class="note">Lifecycle: Draft → Preview → Benchmark → Validate → <b>Publish</b> → Monitor → Rollback. Publishing re-indexes the chatflow's RAG DB in Flowise first; the switch happens only after it is verified, otherwise the current configuration stays active.</p>
      ${table([['Profile', (v) => `<b>${esc(v.name)}</b><br><span class="note">${esc(v.id)}</span>`], ['Status', (v) => badge(v.status === 'active' ? 'ready' : v.status === 'failed' ? 'blocked' : 'plan', v.status)], ['Index', (v) => esc(v.index_version || '—')],
        ['Settings', (v) => `<span class="note">${cfgLine(v.config)}</span>`], ['Differs from active', (v) => v.status === 'active' ? '<span class="note">live</span>' : diffChips(v.config, active.config)],
        ['Published', (v) => `<span class="note">${esc(v.published_at || '—')} ${esc(v.published_by || '')}</span>`],
        ['Validation', (v) => v.validation ? (v.validation.ok ? badge('ready', 'passed') : badge('blocked', 'failed')) : '—'],
        ['', (v) => v.status === 'active' ? '' : `<button class="ghost small" data-load="${esc(v.id)}">Edit as draft</button> <button class="ghost small" data-val="${esc(v.id)}">Validate</button> ${canPublish && v.status === 'candidate' ? `<button class="small" data-pub="${esc(v.id)}">Publish</button>` : ''} ${canPublish && v.status === 'retired' && v.published_at ? `<button class="small" data-rb="${esc(v.id)}">Roll back</button>` : ''}`]], hist.versions)}
      ${canPublish ? '' : '<p class="note">Publish and roll back are reserved for managers (Supply Chain Director): they change the live Company RAG Search for everyone. Every other step is open to your role.</p>'}
      <div id="rag-pub-out"></div>
      <div class="grid g2"><div class="card"><h4>Flowise chatflow RAG DB</h4>${fl.reachable === false || !fl.configured ? `<p class="note">${esc(fl.detail)}</p>` : `<p>${esc(fl.chatflow)} · tool <code>${esc(fl.retriever_tool)}</code> · splitter ${fl.chunk_size}/${fl.chunk_overlap} chars · top ${fl.top_k} · ${esc(fl.embedding_model)} · table ${esc(fl.table)}</p><p class="note">rows by configuration tag: ${esc(JSON.stringify(fl.table_rows))} · loader tag ${esc(fl.rag_config_version || 'none (deploy settings)')}</p>`}</div>
        <div class="card"><h4>Monitoring (recent queries)</h4>${table([['Profile', (r) => esc(r.config_id)], ['Source', (r) => esc(r.source)], ['Queries', (r) => r.queries, 'num'], ['Empty', (r) => r.empty, 'num'], ['Mean ms', (r) => num(r.latency_mean_ms, 1), 'num']], mt.summary)}</div></div>
      <h4>Indexes</h4>${table([['Index', (i) => esc(i.index_version)], ['Model', (i) => esc(i.embedding_model)], ['Documents', (i) => i.documents, 'num'], ['Chunks', (i) => i.chunks, 'num'], ['Status', (i) => esc(i.status)], ['Profile', (i) => esc(i.config_id || '—')]], hist.indexes)}`;
    const out = $('#rag-pub-out');
    const checks = (r) => table([['Check', (x) => esc(x.check)], ['Result', (x) => x.ok ? badge('ready', 'pass') : badge('blocked', 'fail')], ['Detail', (x) => esc(x.detail)]], r.checks || []);
    $$('[data-load]').forEach((b) => b.addEventListener('click', () => {
      const v = hist.versions.find((x) => x.id === b.dataset.load);
      state.ragDraft = JSON.parse(JSON.stringify(v.config)); renderDraftBar(); toast(`${v.name} loaded into the working draft: edit it in any stage.`);
    }));
    $$('[data-val]').forEach((b) => b.addEventListener('click', (e) => busy(e.currentTarget, async () => { const r = await api(`${RAG}/validate`, { body: { config_id: b.dataset.val } }); out.innerHTML = `<div class="card"><h4>${esc(r.config_id)}: ${r.ok ? badge('ready', 'ready to publish') : badge('blocked', 'not ready')}</h4>${checks(r)}</div>`; })));
    const act = (attr, path, verb) => $$(`[${attr}]`).forEach((b) => b.addEventListener('click', (e) => busy(e.currentTarget, async () => {
      const id = b.getAttribute(attr);
      if (!window.confirm(`${verb} ${id}? This changes the live Company RAG Search (API and Flowise chatflow RAG DB).`)) return;
      const r = await api(`${RAG}/${path}`, { body: { config_id: id, confirm: true } });
      toast(`${verb}: ${r.active} is active (previous ${r.previous}).`);
      out.innerHTML = `<div class="card"><h4>${esc(verb)} done</h4><pre class="code-box" style="min-height:0">${esc(JSON.stringify(r.flowise, null, 1))}</pre></div>`;
      await loadRag();
    })));
    act('data-pub', 'publish', 'Publish');
    act('data-rb', 'rollback', 'Roll back');
  }

  // ================================================================ COMMAND CENTER
  const SEV = { critical: 'critical', warning: 'warning', info: 'info', good: 'good' };
  async function loadCommand() {
    const hour = new Date().getHours();
    $('#page-title').textContent = `${hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening'}`;
    try {
      const [ins, ns] = await Promise.all([api('/api/v1/insights'), api('/api/v1/northstar')]);
      state.insights = ins.insights;
      const c = ins.counts;
      $('#hero-line').innerHTML = c.critical || c.warning
        ? `<b>${c.critical} critical</b> and <b>${c.warning} warning${c.warning === 1 ? '' : 's'}</b> today. Start with the one below.`
        : 'Everything is on track today.';
      renderSpotlight();
      kpiTiles('#cc-kpis', ns.platform_kpis);
      renderNorthStar(ns);
      renderFilters(); renderFeed();
      ccWatches(); ccApprovals(); ccForecast();
      refreshBadges();
    } catch (e) { toast(e.message); }
  }
  function renderNorthStar(ns) {
    const comp = (c) => `<div class="ns-item"><div class="ns-value">${fmtValue(c.value, c.unit)}</div><div class="ns-label">${esc(c.label)}</div><div class="ns-hint">${esc(c.hint)}</div></div>`;
    $('#northstar').innerHTML = `<section class="northstar">
      <div class="ns-col"><div class="eyebrow">North Star · how well the business operates</div><h2>${esc(ns.statement)}</h2><div class="ns-row">${ns.components.map(comp).join('')}</div></div>
      <div class="ns-col learn"><div class="eyebrow">Learning KPI · how much better the AI is getting</div><h2>${esc(ns.learning)}</h2><div class="ns-row">${ns.learning_components.map(comp).join('')}</div>
        <button class="link small arrow" onclick="location.hash='moat'">Open the intelligence moat</button></div></section>`;
    const ind = ns.industry;
    $('#cc-industry').innerHTML = `<h2>${esc(state.snapshot?.tenant?.industry_label || ind.industry)} KPIs</h2><p class="sub">${esc(ind.rules)}</p><div class="kpis compact" id="cc-ind-kpis"></div>`;
    kpiTiles('#cc-ind-kpis', ind.kpis);
  }
  // The single most urgent insight, with one big primary button.
  function renderSpotlight() {
    const top = state.insights[0];
    const host = $('#spotlight');
    state.calm = !top || top.severity === 'good' || top.severity === 'info';
    if (state.calm) {
      host.innerHTML = `<section class="spotlight calm"><div><div class="eyebrow">${statusBadge('good')}</div><h2>No urgent issues</h2><p>Stock, orders, counts and suppliers are within their targets. Watches keep checking for you.</p></div>
        <div class="cta"><button class="large arrow" data-go="dashboard">Open my dashboard</button></div></section>`;
    } else {
      host.innerHTML = `<section class="spotlight" style="--dot:var(--${SEV[top.severity]});--dot-text:var(--${top.severity === 'critical' ? 'critical-text' : 'ink-2'})">
        <div><div class="eyebrow">Most urgent · ${esc(top.category)}</div><h2>${esc(top.title)}</h2><p>${esc(top.detail)}</p></div>
        <div class="cta"><button class="large arrow" data-sp="act">${esc(top.action.label)}</button><button class="ghost" data-sp="why">Why?</button><button class="link" data-sp="ask">Ask copilot</button></div></section>`;
      $('[data-sp=act]', host).addEventListener('click', () => act(top.action));
      $('[data-sp=ask]', host).addEventListener('click', () => openDrawer(top.ask));
      $('[data-sp=why]', host).addEventListener('click', () => whyModal(top));
    }
    $$('[data-go]', host).forEach((b) => b.addEventListener('click', () => go(b.dataset.go)));
    const counts = (cat) => state.insights.filter((i) => i.category === cat && i.severity === 'critical').length;
    const shortcuts = [...new Set(state.insights.map((i) => i.category))].map((cat) => [cat, counts(cat)]).filter(([, n]) => n);
    $('#next-up').innerHTML = shortcuts.map(([cat, n]) => `<button data-cat="${esc(cat)}">${esc(cat)} <b>${n}</b></button>`).join('');
    $$('#next-up [data-cat]').forEach((b) => b.addEventListener('click', () => { state.filter = b.dataset.cat; renderFilters(); renderFeed(); $('#insight-filters').scrollIntoView({ behavior: 'smooth', block: 'start' }); }));
  }
  function whyModal(i) {
    modal('Why this insight?', `<p>${esc(i.detail)}</p>${table([['Evidence', (e) => esc(e.label)], ['Value', (e) => esc(String(e.value))]], i.evidence)}<p class="note">Deterministic: computed from SAP snapshot data by the rules engine — no language model involved.</p>`);
  }
  function renderFilters() {
    const cats = ['all', ...new Set(state.insights.map((i) => i.category))];
    $('#insight-filters').innerHTML = cats.map((c) => `<button class="${state.filter === c ? 'on' : ''}" data-f="${esc(c)}">${esc(c === 'all' ? `All (${state.insights.length})` : `${c} (${state.insights.filter((i) => i.category === c).length})`)}</button>`).join('');
    $$('#insight-filters button').forEach((b) => b.addEventListener('click', () => { state.filter = b.dataset.f; renderFilters(); renderFeed(); }));
  }
  function renderFeed() {
    // The spotlight already shows the top insight, so the unfiltered feed lists the rest.
    const items = state.insights.filter((i, n) => (state.filter === 'all' ? n > 0 || state.calm : i.category === state.filter));
    $('#feed').innerHTML = items.length ? items.map((i, n) => `<article class="insight" style="--dot:var(--${SEV[i.severity]})"><div class="bar"></div>
      <div class="top">${statusBadge(SEV[i.severity])} ${chip(i.category)} <span class="metric">${esc(i.metric.label)} <b>${esc(String(i.metric.value))}</b></span></div>
      <h3>${esc(i.title)}</h3><p>${esc(i.detail)}</p>
      <div class="actions"><button class="ghost small arrow" data-act="${n}">${esc(i.action.label)}</button><button class="link small" data-why="${n}">Why?</button>
      <button class="link small" data-ask="${n}">Ask copilot</button><button class="link small" data-watch="${n}">Watch</button></div></article>`).join('') : '<div class="empty">Nothing else needs attention — all clear.</div>';
    const pick = (b, attr) => items[Number(b.dataset[attr])];
    $$('#feed [data-why]').forEach((b) => b.addEventListener('click', () => whyModal(pick(b, 'why'))));
    $$('#feed [data-ask]').forEach((b) => b.addEventListener('click', () => openDrawer(pick(b, 'ask').ask)));
    $$('#feed [data-act]').forEach((b) => b.addEventListener('click', () => act(pick(b, 'act').action)));
    $$('#feed [data-watch]').forEach((b) => b.addEventListener('click', () => busy(b, async () => {
      const i = pick(b, 'watch');
      const p = i.action.params || {};
      const body = i.action.kind === 'stock_balance' && p.warehouse
        ? { name: `${p.material} @ ${p.warehouse} cover`, kind: 'days_of_cover', params: { material: p.material, warehouse: p.warehouse }, threshold: 7 }
        : i.category === 'Suppliers' ? { name: `${p.supplier} risk`, kind: 'supplier_risk', params: { supplier: p.supplier }, threshold: 50 }
          : i.category === 'Sales orders' ? { name: 'Sales orders at risk', kind: 'sales_orders_at_risk', params: {}, threshold: 1 }
            : { name: i.title.slice(0, 110), kind: 'question', params: { question: i.ask }, threshold: 0 };
      await api('/api/v1/watches', { body }); toast(`Watching: ${body.name}`); ccWatches();
    })));
  }
  function act(action) {
    const p = action.params || {};
    if (action.kind === 'go') { go(p.page); return; }
    if (action.kind === 'ask') { openDrawer(p.question, state.persona); return; }
    if (action.kind === 'stock_balance') { go('inventory'); $('#form-balance [name=material]').value = p.material; $('#form-balance').requestSubmit(); }
    else if (action.kind === 'factory_readiness') {
      go('production'); const f = $('#form-readiness');
      f.plant.value = p.plant; f.material.value = p.material; f.quantity.value = p.quantity; f.need_by.value = p.need_by; f.requestSubmit();
    } else if (action.kind === 'supplier') { go('suppliers'); $('#supplier-select').value = p.supplier; $('#form-supplier').requestSubmit(); }
    else go({ sales_orders: 'sales', stocktake: 'stocktake', suppliers: 'suppliers' }[action.kind] || 'command');
  }
  async function ccWatches() {
    try {
      const r = await api('/api/v1/watches/evaluate', { body: {} });
      $('#cc-watches').innerHTML = r.watches.length ? r.watches.map((w) => `<div class="row" style="margin:0 0 8px;align-items:center">${w.kind === 'question' ? chip('question') : pill(w.triggered ? 'critical' : 'good', w.triggered ? 'Triggered' : 'OK')}
        <span class="grow">${esc(w.name)}<br><span class="note">${esc(w.text)}${w.changed ? ` · changed from ${esc(String(w.previous_value))}` : ''}</span></span>
        ${w.kind === 'question' ? `<button class="ghost small" data-q="${esc(w.params.question)}">Ask</button>` : ''}</div>`).join('')
        : '<div class="empty">No watches yet — use “Watch” on any insight.</div>';
      $$('#cc-watches [data-q]').forEach((b) => b.addEventListener('click', () => openDrawer(b.dataset.q)));
    } catch (e) { $('#cc-watches').innerHTML = `<div class="empty">${esc(e.message)}</div>`; }
  }
  async function ccApprovals() {
    const recs = await api('/api/v1/recommendations?status=pending_review').catch(() => []);
    const accepted = await api('/api/v1/recommendations?status=accepted').catch(() => []);
    $('#cc-approvals').innerHTML = `<p style="margin:0 0 8px"><b>${recs.length}</b> pending review · <b>${accepted.length}</b> accepted, ready to execute</p>` +
      recs.slice(0, 4).map((r) => `<div class="note" style="margin:0 0 4px">#${r.id} ${esc(r.kind.replaceAll('_', ' '))} · ${r.actions.length} action(s) · via ${esc(r.source)}</div>`).join('') +
      `<button class="ghost small arrow" onclick="location.hash='approvals'">${recs.length ? 'Review now' : 'Open approvals'}</button>`;
  }
  // The busiest finished good / warehouse of the selected customer (drives default forecasts and forms).
  function headlineProduct() {
    const demand = state.snapshot?.warehouse_demand_daily || {};
    let best = null;
    for (const [material, byDc] of Object.entries(demand)) for (const [dc, v] of Object.entries(byDc)) if (!best || v > best.v) best = { material, dc, v };
    return best || { material: '', dc: '' };
  }
  async function ccForecast() {
    try {
      const h = headlineProduct();
      if (!h.material) return;
      const desc = state.snapshot.materials.find((m) => m.code === h.material)?.description || h.material;
      const f = await api(`/api/v1/analysis/forecast-vs-actuals?material=${encodeURIComponent(h.material)}&warehouse=${encodeURIComponent(h.dc)}`);
      const box = $('#cc-forecast'); box.innerHTML = '';
      box.appendChild(window.Charts.line({ title: `Forecast vs actuals — ${desc}, ${h.dc}`, subtitle: `XGBoost back-test MAPE ${f.holdout_mape_pct}% over the last ${f.backtest.length} days`, today: state.cfg.as_of,
        series: [{ name: 'Actual demand', label: 'actual', points: f.actual }, { name: 'Back-test forecast', label: 'back-test', points: f.backtest }, { name: 'Forecast', label: 'forecast', points: f.forecast, color: 'var(--s3)' }] }));
    } catch { /* optional */ }
  }
  async function refreshBadges() {
    try {
      const [ins, recs] = await Promise.all([api('/api/v1/insights'), api('/api/v1/recommendations?status=pending_review')]);
      const b1 = $('#badge-critical'); b1.textContent = ins.counts.critical; b1.hidden = !ins.counts.critical;
      const b2 = $('#badge-approvals'); b2.textContent = recs.length; b2.hidden = !recs.length;
    } catch { /* ignore */ }
  }

  // ================================================================ ROLE DASHBOARDS
  const OLD_PERSONA = { executive: 'director', inventory: 'warehouse', sales: 'demand', stocktake: 'warehouse' };
  const ROLE_SHORT = { director: 'Director', demand: 'Demand', production: 'Production', procurement: 'Procurement', warehouse: 'Warehouse',
    logistics: 'Logistics', quality: 'Quality', finance: 'Finance', mlops: 'AI / MLOps' };
  // Business role -> API permission. Only the Supply Chain Director accepts/rejects and executes in the SAP sandbox.
  const ROLE_ACCESS = { director: 'manager' };
  async function choosePersona(id) {
    state.persona = id; local.set('persona', id);
    if ($('#role-select').value !== id) $('#role-select').value = id;
    const access = ROLE_ACCESS[id] || 'planner';
    const switching = state.demoKeys && access !== state.role;
    if (switching) { state.key = state.demoKeys[access]; session.set('apiKey', state.key); setRole(access); refreshBadges(); }
    const target = `dashboard/${id}/${state.focus || ''}`;  // keep the product focus when switching roles
    if (location.hash.startsWith('#dashboard')) { if (location.hash !== `#${target}`) location.hash = target; else loadDashboard(); }
    else if (switching) route();
  }
  const SEVERITY_LABEL = { critical: 'Critical', warning: 'Warning', info: 'Info' };
  const when = (p) => (p.when ? `<span class="when"><b>${p.in_days === null || p.in_days === undefined ? '' : p.in_days < 0 ? `${-p.in_days} d ago` : p.in_days === 0 ? 'today' : `in ${p.in_days} d`}</b> · ${esc(p.when)}</span>` : '<span class="when">ongoing</span>');
  async function loadDashboard() {
    try {
      if (!state.roleCat) state.roleCat = await api('/api/v1/roles');
      state.persona = OLD_PERSONA[state.persona] || state.persona;
      if (!state.roleCat.some((r) => r.id === state.persona)) state.persona = state.role === 'manager' ? 'director' : 'demand';
      if ($('#role-select').value !== state.persona) $('#role-select').value = state.persona;  // deep links keep the top-bar role in sync
      const access = ROLE_ACCESS[state.persona] || 'planner';
      if (state.demoKeys && access !== state.role) { state.key = state.demoKeys[access]; session.set('apiKey', state.key); setRole(access); refreshBadges(); }
      $('#persona-pills').innerHTML = state.roleCat.map((r) => `<button class="${r.id === state.persona ? 'on' : ''}" data-p="${r.id}" title="${esc(r.title)} · ${esc(r.agent)}">${esc(ROLE_SHORT[r.id] || r.title)}${r.mvp ? '' : ' <span class="later">later</span>'}</button>`).join('');
      $$('#persona-pills button').forEach((b) => b.addEventListener('click', () => choosePersona(b.dataset.p)));
      if (!state.products) state.products = await api('/api/v1/products');
      $('#product-focus').innerHTML = '<option value="">All products</option>' + state.products.map((p) =>
        `<option value="${esc(p.material)}">${esc(p.description)} · ${esc(p.material)} — ${p.health === 'critical' ? '▲ critical' : p.health === 'warning' ? '◆ warning' : '✓ good'}</option>`).join('');
      if (state.focus && !state.products.some((p) => p.material === state.focus)) state.focus = '';
      $('#product-focus').value = state.focus || '';
      $('#role-head').innerHTML = '<p class="note"><span class="spinner"></span>Building your view…</p>';
      const v = await api(`/api/v1/roles/${state.persona}${state.focus ? `?material=${encodeURIComponent(state.focus)}` : ''}`);
      state.roleView = v;
      renderPageActions('dashboard');
      $('#persona-task').textContent = `${v.focus}${v.product ? ` · focus: ${v.product.description}` : ' · whole network'} · as of ${v.as_of}`;
      // header: who this is for and the agent working for them
      const top = v.actions[0];
      $('#role-head').innerHTML = `<section class="role-head"><div><div class="eyebrow">${v.mvp ? `MVP role ${v.priority} of 5` : 'Integrates as data becomes available'} · ${esc(v.agent.name)}</div>
        <h2>${esc(v.title)}</h2><p>${esc(v.agent.mission)}.</p></div>
        <div class="cta">${top ? `<button class="large arrow" data-top>${esc(top.action.label)}</button><span class="note">${esc(top.title)}</span>` : '<span class="note">No action needed right now.</span>'}</div></section>`;
      $('[data-top]', $('#role-head'))?.addEventListener('click', () => act(top.action));
      // 1. what matters
      kpiTiles('#dash-kpis', v.kpis);
      // 2. what is likely to go wrong
      $('#role-predictions').innerHTML = v.predictions.length ? `<div class="predictions">${v.predictions.map((p) => `<div class="prediction" style="--tone:var(--${p.severity === 'critical' ? 'critical' : p.severity === 'warning' ? 'warning' : 'info'})">
        ${statusBadge(p.severity)}<div class="what"><b>${esc(p.what)}</b><span>${esc(p.basis)}</span></div>${when(p)}${p.at_risk_eur ? `<span class="risk">€${num(p.at_risk_eur)}</span>` : '<span class="risk"></span>'}</div>`).join('')}</div>`
        : '<div class="empty">Nothing is predicted to go wrong in the next 60 days.</div>';
      // 3. what it will cost
      const c = v.cost;
      $('#role-cost').innerHTML = `<h2>What it will cost</h2><p class="sub">if nothing is done vs the fixes proposed</p>
        <div class="cost-big"><span>Value at risk</span><b>€${num(c.at_risk_eur)}</b></div>
        <div class="cost-big fix"><span>Known cost of the fixes</span><b>€${num(c.fix_cost_eur)}</b><em>${c.fixes_with_cost} of ${c.fixes} fixes priced</em></div>
        ${c.at_risk_eur && c.fix_cost_eur ? `<p class="ratio">Every €1 spent on the priced fixes protects about <b>€${num(c.at_risk_eur / c.fix_cost_eur)}</b> at risk.</p>` : ''}
        <p class="note">${esc(c.note)}</p>`;
      // 4. what to do next
      $('#role-actions').innerHTML = v.actions.length ? `<div class="issues">${v.actions.map((a, n) => `<div class="issue-row" style="--tone:var(--${a.severity === 'critical' ? 'critical' : a.severity === 'warning' ? 'warning' : 'info'})">
        <div class="sev">${statusBadge(a.severity)}${a.area ? `<span class="chip">${esc(a.area)}</span>` : ''}</div>
        <div class="what"><b>${esc(a.title)}</b><span>${esc(a.why)}</span></div>
        <div class="fix"><span class="fix-label">Impact</span>${a.at_risk_eur ? `protects €${num(a.at_risk_eur)}` : 'risk not priced'}${a.fix_cost_eur ? ` · costs €${num(a.fix_cost_eur)}` : ''}</div>
        <div class="go"><button class="${n === 0 ? '' : 'ghost'} small arrow" data-ra="${n}">${esc(a.action.label)}</button></div></div>`).join('')}</div>`
        : '<div class="empty">Nothing to do right now — the agent keeps watching.</div>';
      $$('[data-ra]').forEach((b) => b.addEventListener('click', () => act(v.actions[Number(b.dataset.ra)].action)));
      // your agent
      const tools = Array.isArray(v.agent.tools) ? v.agent.tools : [v.agent.tools];
      $('#role-agent').innerHTML = `<div class="agent-top"><div class="agent-avatar"><svg class="ico"><use href="#i-spark"/></svg></div><div><h2>${esc(v.agent.name)}</h2>
        <p class="sub" style="margin:0">Works for the ${esc(v.title)} · ${esc(v.agent.mission)} · LangGraph + Qwen, read-only tools</p></div></div>
        <div class="agent-tools">${tools.map((x) => `<span class="chip">${esc(x)}</span>`).join('')}</div>
        <div class="starters">${v.agent.starters.map((q, i) => `<button class="ghost" data-sq="${i}">${esc(q)}</button>`).join('')}</div>`;
      $$('[data-sq]').forEach((b) => b.addEventListener('click', () => openDrawer(v.agent.starters[Number(b.dataset.sq)], state.persona)));
      // details: product brief, sales outlook, charts
      const brief = $('#dash-brief');
      $('#dash-role-title').hidden = false;
      $('#dash-role-title').innerHTML = `<h2>Details</h2><span class="note">${v.product ? 'product brief, sales rates, calendar and charts' : 'charts and tables for this role'}</span>`;
      if (v.product) await renderBrief(v.product.material, brief); else brief.innerHTML = '';
      if (v.product || ['director', 'demand', 'warehouse', 'logistics'].includes(v.role)) {
        renderOutlook($('#dash-outlook'), state.focus).catch((e) => { $('#dash-outlook').innerHTML = `<div class="empty">${esc(e.message)}</div>`; });
      } else $('#dash-outlook').innerHTML = '';
      const charts = $('#dash-charts'); charts.innerHTML = '';
      v.charts.forEach((ch) => charts.appendChild(renderChart(ch)));
      if (v.forecast) {
        const f = await api(`/api/v1/analysis/forecast-vs-actuals?material=${v.forecast.material}&warehouse=${v.forecast.warehouse}`);
        charts.appendChild(renderChart({ type: 'line', title: `Forecast vs actuals — ${v.forecast.material} @ ${v.forecast.warehouse}`, subtitle: `back-test MAPE ${f.holdout_mape_pct}%`, today: state.cfg.as_of,
          series: [{ name: 'Actual', label: 'actual', points: f.actual }, { name: 'Back-test', label: 'back-test', points: f.backtest }, { name: 'Forecast', label: 'forecast', points: f.forecast, color: 'var(--s3)' }] }));
      }
      $('#dash-tables').innerHTML = (v.tables || []).map((tb) => `<div class="card"><h2>${esc(tb.title)}</h2>${table(tb.columns.map((col, i) => [col, (r) => (STATUS_OF[r[i]] ? badge(r[i]) : esc(typeof r[i] === 'number' ? num(r[i], 2) : r[i] ?? '—'))]), tb.rows)}</div>`).join('');
      $('#dash-product').innerHTML = v.product ? `<div class="row" style="justify-content:center;margin-top:8px"><button class="ghost arrow" onclick="location.hash='products/${esc(v.product.material)}'">Open the full analysis for ${esc(v.product.description)}</button></div>` : '';
    } catch (e) { toast(e.message); }
  }

  // ================================================================ PRODUCT 360
  async function loadProducts() {
    try {
      const products = await api('/api/v1/products');
      if (!products.some((p) => p.material === state.product)) state.product = products[0].material;
      // Product picker: a dropdown (scales to any number of products) + one summary card for the selected product
      const select = $('#product-select');
      select.innerHTML = products.map((p) => `<option value="${esc(p.material)}" ${p.material === state.product ? 'selected' : ''}>` +
        `${esc(p.description)} · ${esc(p.material)} · ${esc(p.health)} · ${num(p.network_days_of_cover, 1)} days of cover</option>`).join('');
      select.onchange = () => { location.hash = `products/${select.value}`; };  // the router reloads this page (and the link is shareable)
      const critical = products.filter((p) => p.health === 'critical').length;
      $('#product-count').textContent = `${products.length} product${products.length === 1 ? '' : 's'}${critical ? ` · ${critical} critical` : ''}`;
      const p = products.find((x) => x.material === state.product);
      $('#product-cards').innerHTML = `<div class="product on" style="cursor:default">
        <div class="row" style="justify-content:space-between;margin:0"><h3>${esc(p.description)}</h3>${statusBadge(p.health)}</div>
        <div class="note" style="margin:0">${esc(p.material)} · made at ${esc(p.producing_plant)}</div>
        <div class="big">${num(p.network_on_hand)} <span class="note">units · ${num(p.network_days_of_cover, 1)} days of cover</span></div>
        <div class="note" style="margin:0">${p.first_stockout ? `First stock-out <b>${esc(p.first_stockout)}</b>` : 'No stock-out in 60 days'}</div></div>`;
      await renderBrief(state.product, $('#product-brief'));
      await renderProduct(state.product);
    } catch (e) { toast(e.message); }
  }
  // ---------------------------------------------------------------- sales rates + out-of-stock calendar
  const spark = (values) => {
    const w = 96, h = 24, max = Math.max(...values), min = Math.min(...values), span = max - min || 1;
    const pts = values.map((v, i) => `${((i / (values.length - 1)) * w).toFixed(1)},${(h - 2 - ((v - min) / span) * (h - 4)).toFixed(1)}`).join(' ');
    return `<svg class="spark" viewBox="0 0 ${w} ${h}" width="${w}" height="${h}" aria-hidden="true"><polyline points="${pts}"/></svg>`;
  };
  const EVENT = {
    stockout: { icon: '▲', label: 'Out of stock', cls: 'ev-critical' }, below_safety: { icon: '◆', label: 'Below safety stock', cls: 'ev-warning' },
    arrival: { icon: '↓', label: 'Shipment arrives', cls: 'ev-info' }, production: { icon: '⚙', label: 'Production lands', cls: 'ev-good' },
  };
  async function renderOutlook(box, material) {
    box.innerHTML = '<p class="note"><span class="spinner"></span>Loading sales rates and the out-of-stock calendar…</p>';
    const o = await api(`/api/v1/sales/outlook${material ? `?material=${encodeURIComponent(material)}` : ''}`);
    const short = (e) => (state.products?.find((p) => p.material === e.material)?.description || e.description).replace(/\s+\d+\s?(ml|g|l|kg)$/i, '');
    const trend = (r) => (r.trend === 'up' ? pill('good', `▲ +${num(r.trend_pct, 1)}%`) : r.trend === 'down' ? pill('warning', `▼ ${num(r.trend_pct, 1)}%`) : `<span class="status"><i></i>→ ${num(r.trend_pct, 1)}%</span>`);
    // Calendar: weeks from the Monday of "today" to the end of the prediction horizon.
    const today = new Date(`${o.as_of}T00:00:00`);
    const start = new Date(today); start.setDate(today.getDate() - ((today.getDay() + 6) % 7));
    const end = new Date(`${o.end}T00:00:00`);
    const iso = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
    const byDay = {}; o.calendar.forEach((e, i) => (byDay[e.date] ||= []).push(i));
    let cells = '';
    for (let d = new Date(start); d <= end || d.getDay() !== 1; d.setDate(d.getDate() + 1)) {
      const key = iso(d), evs = byDay[key] || [], past = d < today, weekend = d.getDay() === 0 || d.getDay() === 6;
      const label = d.getDate() === 1 || +d === +start ? `${d.toLocaleString(undefined, { month: 'short' })} ${d.getDate()}` : d.getDate();
      cells += `<div class="cal-day${past ? ' past' : ''}${weekend ? ' weekend' : ''}${key === o.as_of ? ' today' : ''}"><div class="cal-date">${label}${key === o.as_of ? ' <b>Today</b>' : ''}</div>
        ${evs.slice(0, 3).map((i) => { const e = o.calendar[i], k = EVENT[e.kind]; return `<button class="ev ${k.cls}" data-ev="${i}" title="${esc(`${k.label} · ${e.description} @ ${e.warehouse} — ${e.fix}`)}">${k.icon} ${esc(e.warehouse === 'all DCs' ? 'Prod.' : e.warehouse)} ${esc(short(e))}</button>`; }).join('')}
        ${evs.length > 3 ? `<button class="ev ev-more" data-day="${key}">+${evs.length - 3} more</button>` : ''}</div>`;
    }
    const outs = o.calendar.filter((e) => e.kind === 'stockout');
    box.innerHTML = `
      <div class="card"><div class="chart-head"><div><h2>Current sales rates</h2><p class="sub">Units per day by product and warehouse · last 28 days of actual sales · ${esc(o.model_scope)}</p></div></div>
        ${table([['Product · warehouse', (r) => `<b>${esc(r.description)}</b><br><span class="note">${esc(r.material)} · ${esc(r.warehouse)} ${esc(r.name)}</span>`], ['Last 28 days', (r) => spark(r.sparkline)],
          ['Today’s rate (7 d)', (r) => `<b>${num(r.last_7d_per_day, 1)}</b>/day`, 'num'], ['28-day average', (r) => `${num(r.last_28d_per_day, 1)}/day`, 'num'],
          ['Forecast next 14 d', (r) => `${num(r.forecast_14d_per_day, 1)}/day`, 'num'], ['Trend', trend],
          ['Out of stock in', (r) => (r.days_to_stockout === null ? pill('good', '60+ days') : pill(r.days_to_stockout <= 14 ? 'critical' : r.days_to_stockout <= 30 ? 'warning' : 'info', `${r.days_to_stockout} days`)), 'num']], o.sales_rates)}</div>
      <div class="card"><div class="chart-head"><div><h2>Out-of-stock calendar</h2><p class="sub">Predicted from today’s stock, forecast sales, inbound shipments and planned production · next ${o.horizon_days} days · ${outs.length} predicted stock-out${outs.length === 1 ? '' : 's'}</p></div></div>
        <div class="legend">${Object.values(EVENT).map((k) => `<span class="ev ${k.cls}" style="cursor:default">${k.icon} ${k.label}</span>`).join('')}</div>
        <div class="scroll"><div class="calendar"><div class="cal-head">Mon</div><div class="cal-head">Tue</div><div class="cal-head">Wed</div><div class="cal-head">Thu</div><div class="cal-head">Fri</div><div class="cal-head">Sat</div><div class="cal-head">Sun</div>${cells}</div></div>
        <details class="more"><summary>List view (${o.calendar.length} events)</summary>
          ${table([['Date', (e) => `<span class="nowrap">${esc(e.date)}</span>`], ['In', (e) => `${e.days_from_today} d`, 'num'], ['Event', (e) => `<span class="ev ${EVENT[e.kind].cls}">${EVENT[e.kind].icon} ${EVENT[e.kind].label}</span>`],
            ['Product', (e) => esc(e.description)], ['Where', (e) => esc(e.warehouse)], ['Fix / detail', (e) => esc(e.fix)]], o.calendar)}</details></div>`;
    const open = (idxs, title) => modal(title, table([['Event', (e) => `<span class="ev ${EVENT[e.kind].cls}">${EVENT[e.kind].icon} ${EVENT[e.kind].label}</span>`], ['Product', (e) => `${esc(e.description)}<br><span class="note">${esc(e.material)}</span>`],
      ['Where', (e) => esc(e.warehouse)], ['Fix / detail', (e) => esc(e.fix)]], idxs.map((i) => o.calendar[i])) +
      `<div class="row" style="margin-top:12px">${[...new Set(idxs.map((i) => o.calendar[i].material))].map((m) => `<button class="arrow" onclick="location.hash='products/${esc(m)}';document.querySelector('.modal-backdrop')?.remove()">Open ${esc(m)} brief</button>`).join('')}</div>`);
    $$('[data-ev]', box).forEach((b) => b.addEventListener('click', () => { const e = o.calendar[Number(b.dataset.ev)]; open(byDay[e.date], e.date); }));
    $$('[data-day]', box).forEach((b) => b.addEventListener('click', () => open(byDay[b.dataset.day], b.dataset.day)));
  }

  // ---------------------------------------------------------------- product brief: status, reserve, time to out-of-stock, issues -> fixes
  async function renderBrief(material, box) {
    box.innerHTML = '<p class="note"><span class="spinner"></span>Building the product brief…</p>';
    const b = await api(`/api/v1/products/${encodeURIComponent(material)}/brief`);
    const s = b.supply, r = b.reserve, t = b.time_to_out_of_stock, c = b.issue_counts;
    const tone = (level) => ({ critical: 'var(--critical)', warning: 'var(--warning)', good: 'var(--good)', info: 'var(--info)' }[level] || 'var(--axis)');
    const oosLevel = t.days === null ? 'good' : t.days <= 14 ? 'critical' : t.days <= 30 ? 'warning' : 'good';
    const top = b.issues[0];
    const stat = (label, value, sub, level) => `<div class="brief-stat" style="--tone:${tone(level)}"><div class="label"><i></i>${esc(label)}</div><div class="value">${value}</div><div class="hint">${sub}</div></div>`;
    const issueRow = (i, n) => `<div class="issue-row" style="--tone:${tone(i.severity)}">
        <div class="sev">${statusBadge(i.severity)}<span class="chip">${esc(i.area)}</span></div>
        <div class="what"><b>${esc(i.issue)}</b><span>${esc(i.impact)}</span></div>
        <div class="fix"><span class="fix-label">Proposed fix</span>${esc(i.fix)}</div>
        <div class="go"><button class="ghost small arrow" data-issue="${n}">${esc(i.action.label)}</button></div></div>`;
    const urgent = b.issues.filter((i) => i.severity !== 'info'), later = b.issues.filter((i) => i.severity === 'info');
    box.innerHTML = `
      <section class="spotlight${b.status === 'good' ? ' calm' : ''}" style="--dot:${tone(b.status)};--dot-text:var(--${b.status === 'critical' ? 'critical-text' : b.status === 'good' ? 'good-text' : 'ink-2'})">
        <div><div class="eyebrow">Product brief · ${esc(b.material)} · made at ${esc(b.producing_plant || '—')} · as of ${esc(b.as_of)}</div>
          <h2>${esc(b.description)}</h2><p>${esc(b.headline)}</p></div>
        <div class="cta">${top && b.status !== 'good' ? `<button class="large arrow" data-issue="0">${esc(top.action.label)}</button>` : ''}
          <button class="ghost" data-brief-ask>Ask copilot</button></div></section>
      <div class="brief-stats">
        ${stat('Supply now', `${num(s.on_hand)} <small>units</small>`, `+${num(s.in_transit)} in transit · +${num(s.from_planned_production)} from planned production · ${num(s.days_of_cover, 1)} d of cover`, 'info')}
        ${stat('Reserve above safety stock', `${num(r.units_above_safety)} <small>units</small>`, `${num(r.days, 1)} days of sales · safety stock ${num(r.safety_stock_total)} (${num(r.safety_stock_per_dc)} per DC)`, r.status)}
        ${stat('Time to out-of-stock', t.days === null ? 'None <small>in 60 d</small>' : `${t.days} <small>days</small>`, t.days === null ? 'every warehouse covered for 60 days' : `first at ${esc(t.warehouse)} on ${esc(t.date)}`, oosLevel)}
        ${stat('Open issues', `${c.critical + c.warning} <small>to act on</small>`, `${c.critical} critical · ${c.warning} warning${c.warning === 1 ? '' : 's'} · ${c.info} for information`, b.status)}
      </div>
      <div class="card">
        <div class="chart-head"><div><h2>Issues and proposed fixes</h2><p class="sub">Most urgent first. Each fix is computed from SAP data (stock, orders, POs, lanes, supplier performance) — no language model.</p></div></div>
        <div class="issues">${urgent.length ? urgent.map((i) => issueRow(i, b.issues.indexOf(i))).join('') : '<div class="empty">No issues need action — supply is on track.</div>'}</div>
        ${later.length ? `<details class="more"><summary>${later.length} more for information</summary><div class="issues">${later.map((i) => issueRow(i, b.issues.indexOf(i))).join('')}</div></details>` : ''}
      </div>
      <div class="grid g2">
        <div class="card" data-oos></div>
        <div class="card"><h2>Top suppliers</h2><p class="sub">Recommended source per component — fastest qualified option within 10% of the cheapest landed cost</p>
          ${table([['Component', (o) => esc(o.material)], ['Supplier', (o) => `<b>${esc(o.supplier)}</b>${o.type === 'alternative' ? ' <span class="chip">alternative</span>' : ''}`],
            ['Time to deliver', (o) => `${num(o.time_to_deliver_days, 1)} d`, 'num'], ['Landed €/unit', (o) => `€${num(o.landed_cost_per_unit_eur, 2)}`, 'num'],
            ['OTIF', (o) => (o.otif_pct === null ? 'quote' : `${num(o.otif_pct, 1)}%`), 'num']], b.top_suppliers)}
          <h2 style="margin-top:18px">Top warehouses</h2><p class="sub">Best → worst by time to out-of-stock</p>
          ${table([['#', (w) => `<b>${w.rank}</b>`], ['Warehouse', (w) => `<a href="#sites/${esc(w.warehouse)}">${esc(w.warehouse)} · ${esc(w.name)}</a>`], ['On hand', (w) => num(w.on_hand), 'num'],
            ['Cover', (w) => `${num(w.sales_days_of_cover, 1)} d`, 'num'], ['Out of stock', (w) => (w.stockout_date ? esc(w.stockout_date) : '—'), 'num'], ['', (w) => statusBadge(w.health)]], b.top_warehouses)}
        </div>
      </div>`;
    box.querySelector('[data-oos]').appendChild(window.Charts.bar({ title: 'Time to out-of-stock by warehouse', subtitle: 'days at forecast sales, including inbound and planned production; 60 = not within 60 days', unit: ' d',
      rows: t.by_warehouse.map((w) => ({ label: `${w.warehouse} · ${w.name}`, value: w.days_to_stockout ?? 60, status: w.health, hint: `${num(w.on_hand)} on hand · ${w.stockout_date ? `out of stock ${w.stockout_date}` : 'covered'}${w.below_safety_date ? ` · below safety ${w.below_safety_date}` : ''}` })) }));
    $$('[data-issue]', box).forEach((btn) => btn.addEventListener('click', () => act(b.issues[Number(btn.dataset.issue)].action)));
    $('[data-brief-ask]', box).addEventListener('click', () => openDrawer(`Give me the supply plan for ${b.description} (${b.material}): what are the issues and what should we do first?`));
  }
  async function renderProduct(material, box = $('#product-detail')) {
    box.innerHTML = '<p class="note"><span class="spinner"></span>Building the product view…</p>';
    const p = await api(`/api/v1/products/${material}`);
    const r = p.resupply;
    box.innerHTML = '';
    // 1. Key supply-chain metrics for this product, at a glance
    const kpis = document.createElement('div'); kpis.className = 'kpis'; box.appendChild(kpis);
    kpiTiles(kpis, p.scorecard);

    // 2. Inventory vs time to out-of-stock (forecast sales), warehouses best -> worst
    const H = p.horizon_days;
    const wr = p.warehouse_ranking;
    const oos = document.createElement('div'); oos.className = 'grid g2'; box.appendChild(oos);
    oos.appendChild(renderChart({ type: 'bar', title: 'Time to out-of-stock by warehouse', subtitle: `days until stock runs out at forecast sales (incl. shipments and planned production); ${H} = not within ${H} days`,
      unit: ' d', reference: 7, reference_label: '7 days',
      rows: wr.map((d) => ({ label: `#${d.rank} ${d.warehouse} · ${d.name}`, value: d.days_to_stockout ?? H, status: d.health,
        hint: `${num(d.on_hand)} units on hand · ${num(d.sales_days_of_cover, 1)} days of cover at forecast sales · ${d.stockout_date ? `out of stock ${d.stockout_date}` : `no stock-out within ${H} days`}` })) }));
    oos.appendChild(renderChart({ type: 'bar', title: 'Inventory by warehouse (units)', subtitle: 'on hand today, ranked best → worst by time to out-of-stock', unit: '',
      rows: wr.map((d) => ({ label: `#${d.rank} ${d.warehouse}`, value: d.on_hand, status: d.health, hint: `${num(d.in_transit)} in transit · 14-day surplus/gap ${num(d.surplus_14d)}` })) }));
    const rank = document.createElement('div'); rank.className = 'card'; box.appendChild(rank);
    rank.innerHTML = `<h2>Warehouse ranking — best to worst for ${esc(p.description)}</h2><p class="sub">Ranked by time to out-of-stock at forecast sales, then days of cover (${wr.length} DCs in the network)</p>` +
      table([['Rank', (d) => `<b>#${d.rank}</b>`], ['Warehouse', (d) => `<a href="#sites/${esc(d.warehouse)}">${esc(d.warehouse)} · ${esc(d.name)}</a>`], ['On hand', (d) => num(d.on_hand), 'num'], ['Days of cover (sales)', (d) => num(d.sales_days_of_cover, 1), 'num'],
        ['Time to out-of-stock', (d) => (d.days_to_stockout === null ? `> ${H} d` : `<b>${d.days_to_stockout} d</b>`), 'num'], ['Out-of-stock date', (d) => esc(d.stockout_date || '—'), 'nowrap'],
        ['14-day surplus / gap', (d) => num(d.surplus_14d), 'num'], ['Health', (d) => pill(d.health)]], wr);

    const dcs = document.createElement('div'); dcs.className = 'dc-cards'; box.appendChild(dcs);
    dcs.innerHTML = p.warehouses.map((d) => `<div class="dc"><h3>${esc(d.warehouse)} · ${esc(d.name)} ${statusBadge(d.stockout_date && d.days_of_cover < 14 ? 'critical' : d.below_safety_date ? 'warning' : 'good')}</h3>
      <dl><dt>On hand</dt><dd>${num(d.on_hand)}</dd><dt>In transit</dt><dd>${num(d.in_transit)}</dd><dt>From planned production</dt><dd>${num(d.from_planned_production)}</dd><dt>Demand / day</dt><dd>${num(d.daily_demand)}</dd>
      <dt>Days of cover</dt><dd>${num(d.days_of_cover, 1)}</dd><dt>Open orders</dt><dd>${num(d.open_sales_orders)}</dd>
      <dt>Below safety stock</dt><dd>${esc(d.below_safety_date || '—')}</dd><dt>Projected stock-out</dt><dd><b>${esc(d.stockout_date || '—')}</b></dd></dl>
      ${d.best_donor ? `<div class="donor">Best donor warehouse: <b>${esc(d.best_donor.from)}</b> → ${num(d.best_donor.quantity)} units, arrives ${esc(d.best_donor.arrives)} (${d.best_donor.in_time ? 'before the stock-out' : 'after the stock-out'}) · €${num(d.best_donor.estimated_cost)} · ${num(d.best_donor.carbon_kg)} kg CO₂
        <div style="margin-top:6px"><button class="small" data-balance="${esc(p.material)}">Plan transfer</button></div></div>` : d.stockout_date || d.below_safety_date ? '<div class="donor">No DC has spare stock in the 14-day window — resupply from production.</div>' : ''}</div>`).join('');
    $$('[data-balance]', dcs).forEach((b) => b.addEventListener('click', () => act({ kind: 'stock_balance', params: { material: b.dataset.balance } })));

    const charts = document.createElement('div'); charts.className = 'grid g2'; box.appendChild(charts);
    charts.appendChild(renderChart({ type: 'line', title: 'Projected stock by DC — next 60 days', subtitle: 'on hand + shipments + planned production − XGBoost daily forecast; red dots = stock-out, below 0 = unmet demand', references: [{ value: p.safety_stock, label: 'safety' }],
      series: p.warehouses.map((d) => ({ name: d.warehouse, label: d.warehouse, points: d.projection, markers: d.stockout_date ? [{ date: d.stockout_date, value: 0 }] : [] })) }));
    const f = p.sales.forecast_vs_actuals;
    charts.appendChild(renderChart({ type: 'line', title: `Sales: forecast vs actuals @ ${f.warehouse}`, subtitle: `back-test MAPE ${f.holdout_mape_pct}% · ${f.model_scope}`, today: state.cfg.as_of,
      series: [{ name: 'Actual', label: 'actual', points: f.actual }, { name: 'Back-test', label: 'back-test', points: f.backtest }, { name: 'Forecast', label: 'forecast', points: f.forecast, color: 'var(--s3)' }] }));

    // 3. Suppliers for this product: best time and cost to deliver
    const sr = p.supplier_ranking;
    const supCharts = document.createElement('div'); supCharts.className = 'grid g2'; box.appendChild(supCharts);
    const optHint = (o) => `${o.material} · ${o.type}${o.qualified ? '' : ' (not qualified)'} · landed €${o.landed_cost_per_unit_eur}/unit · €${num(o.cost_per_1000_finished_eur, 2)} per 1,000 finished units · OTIF ${o.otif_pct ?? 'n/a'}% · ${o.time_basis}`;
    supCharts.appendChild(renderChart({ type: 'bar', title: 'Top 5 suppliers — fastest to deliver', subtitle: 'days: contract lead time + actual average delay (alternatives: quoted lead time)', unit: ' d',
      rows: sr.fastest.map((o) => ({ label: `${o.supplier} · ${o.material}`, value: o.time_to_deliver_days, status: o.recommended ? 'good' : o.type === 'alternative' ? 'info' : 'warning', hint: optHint(o) })) }));
    supCharts.appendChild(renderChart({ type: 'bar', title: 'Top 5 suppliers — lowest cost to deliver', subtitle: '€ landed cost (price + freight) per 1,000 finished units — comparable across components', unit: ' €',
      rows: [...sr.lowest_cost].sort((a, b) => a.cost_per_1000_finished_eur - b.cost_per_1000_finished_eur).map((o) => ({ label: `${o.supplier} · ${o.material}`, value: o.cost_per_1000_finished_eur, status: o.recommended ? 'good' : 'info', hint: optHint(o) })) }));
    const opts = document.createElement('div'); opts.className = 'card'; box.appendChild(opts);
    opts.innerHTML = `<h2>Supply options per component</h2><p class="sub">★ = recommended source: fastest qualified option within 10% of the cheapest landed cost. Primary suppliers are measured on actual deliveries; alternatives on quotes.</p>` +
      table([['Component', (o) => `<b>${esc(o.material)}</b>`], ['Supplier', (o) => `${o.recommended ? '★ ' : ''}${esc(o.supplier)}`], ['Type', (o) => chip(o.type + (o.qualified ? '' : ' · not qualified'))],
        ['Time to deliver', (o) => `${num(o.time_to_deliver_days, 1)} d`, 'num'], ['vs fastest', (o) => (o.days_slower_than_best ? `+${num(o.days_slower_than_best, 1)} d` : 'fastest'), 'num'],
        ['Landed €/unit', (o) => num(o.landed_cost_per_unit_eur, 3), 'num'], ['Premium', (o) => (o.cost_premium_pct ? `+${num(o.cost_premium_pct, 1)}%` : 'cheapest'), 'num'],
        ['€ / 1,000 finished', (o) => num(o.cost_per_1000_finished_eur, 2), 'num'], ['OTIF', (o) => (o.otif_pct === null ? '<span class="note">no history</span>' : `${num(o.otif_pct, 1)}%`), 'num'],
        ['Risk', (o) => (o.risk_rating ? badge(o.risk_rating, `${o.risk_rating} risk`) : '—')]], p.supply_options);

    const comp = document.createElement('div'); comp.className = 'card'; box.appendChild(comp);
    comp.innerHTML = `<h2>Resupply needs per component — made at ${esc(p.producing_plant)}</h2><p class="sub">${esc(r.assumptions)}. Product needed at the DCs by <b>${esc(r.need_at_dc_by)}</b>.</p>` +
      table([
        ['Component', (c) => `<b>${esc(c.component)}</b><br><span class="note">${esc(c.description)}</span>`],
        ['Need for builds', (c) => `${num(c.requirement_total, 2)} ${esc(c.uom)}`, 'num'], ['On hand', (c) => num(c.on_hand, 2), 'num'], ['Confirmed POs', (c) => num(c.confirmed_inbound, 2), 'num'],
        ['Shortfall', (c) => (c.shortfall ? `<b>${num(c.shortfall, 2)}</b>` : '0'), 'num'],
        ['First shortage', (c) => esc(c.first_shortage_date || '—'), 'nowrap'], ['Order by', (c) => `<b>${esc(c.order_by || '—')}</b>`, 'nowrap'], ['Status', (c) => badge(c.status)],
        ['Best supplier · time to deliver', (c) => (c.best_suppliers.length ? c.best_suppliers.map((s, i) => `${i ? '' : '★ '}${esc(s.supplier)} · ${num(s.effective_lead_time_days, 1)} d · OTIF ${num(s.otif_pct, 1)}% ${badge(s.risk_rating, s.risk_rating + ' risk')}`).join('<br>') : '—') +
          (c.alternative_sources.length ? `<br><span class="note">Alternative: ${esc(c.alternative_sources.join(', '))}</span>` : '')],
        ['Expedite', (c) => esc(c.expedite_candidates.join(', ') || '—')],
      ], r.components) +
      `<h2 style="margin-top:14px">Builds</h2>${table([['Order', (b) => esc(b.order)], ['Quantity', (b) => num(b.quantity), 'num'], ['Finish', (b) => esc(b.finish_date)], ['Components due', (b) => esc(b.components_needed_by)], ['Status', (b) => chip(b.status)]], r.builds)}`;

    const so = document.createElement('div'); so.className = 'card'; box.appendChild(so);
    so.innerHTML = `<h2>Open sales orders</h2>${table([['Order', (o) => esc(o.order)], ['Customer', (o) => esc(o.customer)], ['DC', (o) => esc(o.warehouse)], ['Qty', (o) => num(o.quantity), 'num'], ['Requested', (o) => esc(o.requested_date)], ['Priority', (o) => chip(o.priority)]], p.sales.open_orders)}
      <div class="row" style="margin-top:10px"><button class="ghost" data-ask-product>Ask the copilot about ${esc(p.description)}</button></div>`;
    $('[data-ask-product]', so).addEventListener('click', () => openDrawer(`Give me the supply situation and resupply plan for ${p.material}.`));
  }

  // ================================================================ WAREHOUSE 360
  async function loadSites() {
    try {
      if (!state.sites) state.sites = await api('/api/v1/sites');
      $('#site-select').innerHTML = ['warehouse', 'factory', 'contract_manufacturer'].map((type) => {
        const group = state.sites.filter((s) => s.type === type);
        return group.length ? `<optgroup label="${{ warehouse: 'Distribution centres', factory: 'Factories', contract_manufacturer: 'Contract manufacturers' }[type]}">${group.map((s) =>
          `<option value="${esc(s.code)}">${esc(s.code)} · ${esc(s.name)}${s.below_target ? ` — ${s.below_target} below target` : ''}</option>`).join('')}</optgroup>` : '';
      }).join('');
      if (!state.sites.some((s) => s.code === state.site)) state.site = (state.sites.find((s) => s.type === 'warehouse') || state.sites[0]).code;
      $('#site-select').value = state.site;
      await renderSite(state.site);
    } catch (e) { toast(e.message); }
  }

  async function renderSite(code) {
    const box = $('#site-detail');
    box.innerHTML = '<p class="note"><span class="spinner"></span>Loading site…</p>';
    const s = await api(`/api/v1/sites/${code}`);
    const site = s.site;
    $('#site-note').textContent = `${site.type.replaceAll('_', ' ')} · ${site.country} · as of ${s.as_of}`;
    box.innerHTML = `<div class="card contact-card">
        <div><h2>${esc(site.code)} · ${esc(site.name)}</h2><span class="chip">${esc(site.type.replaceAll('_', ' '))}</span>
          <dl><dt>Address</dt><dd>${esc(site.address || '—')}</dd><dt>Hours</dt><dd>${esc(site.operating_hours || '—')}</dd><dt>Time zone</dt><dd>${esc(site.timezone || '—')}</dd></dl></div>
        <div><h2 style="font-size:14px">Site management contacts</h2><div class="people">${(site.contacts || []).map((c) => `<div class="person">
          <div class="role">${esc(c.role)}${c.primary ? ' · primary' : ''}</div><b>${esc(c.name)}</b>
          <a href="mailto:${esc(c.email)}">✉ ${esc(c.email)}</a><a href="tel:${esc(c.phone.replaceAll(' ', ''))}">☎ ${esc(c.phone)}</a></div>`).join('')}</div>
          <p class="note" style="margin:8px 0 0">${esc(site.contacts_note || '')}</p></div></div>
      <div class="kpis" id="site-kpis"></div><div class="grid g2" id="site-charts"></div><div id="site-tables"></div>`;
    kpiTiles('#site-kpis', s.kpis);
    const charts = $('#site-charts');
    const tables = [];
    if (s.kind === 'warehouse') {
      const H = 60;
      const byRisk = [...s.products].sort((a, b) => (a.days_to_stockout ?? H + 1) - (b.days_to_stockout ?? H + 1));
      charts.appendChild(renderChart({ type: 'bar', title: 'Time to out-of-stock by product', subtitle: `days at forecast sales (incl. shipments and planned production); ${H} = not within ${H} days`, unit: ' d', reference: 7, reference_label: '7 days',
        rows: byRisk.map((p) => ({ label: p.description, value: p.days_to_stockout ?? H, status: p.health, hint: `${num(p.on_hand)} on hand · ${num(p.sales_days_of_cover, 1)} days of cover · rank #${p.rank_in_network} of ${p.network_dcs} DCs` })) }));
      charts.appendChild(renderChart({ type: 'diverging', title: '14-day surplus (+) / gap (−) by product', subtitle: 'stock + inbound − (forecast + safety stock)', unit: ' units',
        rows: s.products.map((p) => ({ label: p.material, value: p.surplus_14d })) }));
      tables.push(`<div class="card"><h2>Products at this warehouse</h2>${table([['Product', (p) => `<a href="#products/${esc(p.material)}">${esc(p.description)}</a><br><span class="note">${esc(p.material)}</span>`],
        ['On hand', (p) => num(p.on_hand), 'num'], ['In transit', (p) => num(p.in_transit), 'num'], ['Demand / day', (p) => num(p.daily_demand), 'num'], ['Days of cover', (p) => num(p.sales_days_of_cover, 1), 'num'],
        ['Out of stock', (p) => esc(p.stockout_date || `> ${H} d`), 'nowrap'], ['Network rank', (p) => `#${p.rank_in_network} / ${p.network_dcs}`, 'num'], ['Health', (p) => pill(p.health)],
        ['Best donor', (p) => (p.best_donor ? `${esc(p.best_donor.from)} → ${num(p.best_donor.quantity)} units, arrives ${esc(p.best_donor.arrives)}` : '—')]], s.products)}</div>`);
      tables.push(`<div class="card"><h2>Proposed transfers in / out</h2><p class="sub">OR-Tools balancing proposals touching this warehouse</p>${table([['Direction', (t) => chip(t.direction === 'in' ? '↘ in' : '↗ out')], ['Product', (t) => esc(t.material)],
        ['Lane', (t) => esc(`${t.from} → ${t.to}`)], ['Quantity', (t) => num(t.quantity), 'num'], ['Lead', (t) => `${t.lead_days} d`, 'num'], ['Cost', (t) => `€${num(t.estimated_cost, 2)}`, 'num'], ['CO₂', (t) => `${num(t.carbon_kg, 1)} kg`, 'num']], s.transfers)}</div>`);
      tables.push(`<div class="card"><h2>Open sales orders</h2>${table([['Order', (o) => esc(o.order)], ['Customer', (o) => esc(o.customer)], ['Product', (o) => esc(o.material)], ['Qty', (o) => num(o.quantity), 'num'],
        ['Due', (o) => esc(o.requested_date), 'nowrap'], ['Confirmed', (o) => num(o.confirmed), 'num'], ['Status', (o) => badge(o.status)]], s.sales_orders)}</div>`);
    } else {
      const comps = s.positions.filter((r) => r.coverage_pct !== null).sort((a, b) => a.coverage_pct - b.coverage_pct);
      charts.appendChild(renderChart({ type: 'bar', title: 'Component coverage vs 14-day need', subtitle: 'stock + confirmed POs as % of production need + safety stock', unit: '%', reference: 100, reference_label: 'target',
        rows: comps.map((r) => ({ label: r.material, value: r.coverage_pct, status: r.coverage_pct < 60 ? 'critical' : r.coverage_pct < 100 ? 'warning' : 'good', hint: `${num(r.on_hand)} on hand + ${num(r.inbound)} inbound vs ${num(r.target)} ${r.uom}` })) }));
      charts.appendChild(renderChart({ type: 'bar', title: 'Production orders: component readiness', subtitle: '% of BOM components covered by the finish date', unit: '%', reference: 100,
        rows: s.production_orders.map((o) => ({ label: `${o.order} · ${o.material}`, value: o.component_readiness_pct, status: { ready: 'good', at_risk: 'warning' }[o.readiness] || 'critical', hint: `${num(o.quantity)} units due ${o.finish_date}; short: ${o.short_components.join(', ') || 'none'}` })) }));
      tables.push(`<div class="card"><h2>Quality lots</h2>${table([['Lot', (x) => esc(x.lot)], ['Material', (x) => esc(x.material)], ['Qty', (x) => num(x.quantity), 'num'], ['Supplier', (x) => esc(x.supplier || '—')], ['Status', (x) => badge(x.status)], ['Defect / release', (x) => esc(x.defect || x.expected_release || '—')]], s.quality_lots)}</div>`);
      tables.push(`<div class="card"><h2>Open purchase orders</h2>${table([['PO', (x) => esc(x.po)], ['Supplier', (x) => esc(x.supplier)], ['Material', (x) => esc(x.material)], ['Qty', (x) => num(x.quantity), 'num'], ['Delivery', (x) => esc(x.delivery_date), 'nowrap'], ['Status', (x) => chip(x.status)]], s.purchase_orders)}</div>`);
    }
    const shipments = [...s.inbound_shipments.map((x) => ({ ...x, dir: 'inbound' })), ...s.outbound_shipments.map((x) => ({ ...x, dir: 'outbound' }))];
    tables.push(`<div class="card"><h2>Shipments in / out</h2>${table([['Direction', (x) => chip(x.dir)], ['Shipment', (x) => esc(x.shipment)], ['Route', (x) => esc(`${x.from} → ${x.to}`)], ['Material', (x) => esc(x.material)], ['Qty', (x) => num(x.quantity), 'num'],
      ['Carrier', (x) => esc(`${x.carrier} (${x.mode})`)], ['Revised ETA', (x) => esc(x.revised_eta), 'nowrap'], ['Delay', (x) => (x.delay_days ? pill(x.escalate ? 'critical' : 'warning', `${x.delay_days} days late`) : pill('good', 'on time'))]], shipments)}</div>`);
    tables.push(`<div class="grid g2"><div class="card"><h2>Stock counts</h2>${table([['Count', (c) => esc(c.count_id)], ['Material', (c) => esc(c.material)], ['Diff', (c) => num(c.difference), 'num'], ['Status', (c) => badge(c.status)]], s.stocktake)}</div>
      <div class="card"><h2>Batches expiring ≤ 180 days</h2>${table([['Batch', (r) => esc(r.batch)], ['Material', (r) => esc(r.material)], ['Qty', (r) => num(r.quantity), 'num'], ['Days left', (r) => num(r.days_left), 'num'], ['Value', (r) => `€${num(r.value_eur)}`, 'num']], s.expiry)}</div></div>`);
    tables.push(`<div class="card"><h2>Transfer lanes</h2>${table([['Lane', (l) => esc(`${l.from} → ${l.to}`)], ['Lead time', (l) => `${l.lead_days} d`, 'num'], ['Cost / unit', (l) => `€${l.cost_per_unit}`, 'num'], ['CO₂ / unit', (l) => `${l.carbon_kg_per_unit} kg`, 'num']], s.lanes)}</div>`);
    $('#site-tables').innerHTML = tables.join('');
  }

  // ================================================================ submissions
  function submitPanel(analysis) {
    if (!analysis.proposed_actions?.length) return `<div class="panel">${statusBadge('good')} No action required <span class="note">analysis ${esc(analysis.analysis_id)}</span></div>`;
    return `<div class="panel" data-analysis="${esc(analysis.analysis_id)}"><b>${analysis.proposed_actions.length} proposed action(s)</b> <span class="note">analysis ${esc(analysis.analysis_id)} · quantities fixed by the deterministic engine</span>
      <pre>${esc(JSON.stringify(analysis.proposed_actions, null, 2))}</pre>
      <div class="row"><input class="grow" placeholder="Explanation for the manager" value="Proposed by planner from the copilot workspace."><button type="button" class="submit-rec">Submit for manager approval</button></div></div>`;
  }
  document.addEventListener('click', (e) => {
    const btn = e.target.closest('.submit-rec');
    if (!btn) return;
    const panel = btn.closest('.panel');
    busy(btn, async () => {
      const rec = await api('/api/v1/recommendations', { body: { analysis_id: panel.dataset.analysis, explanation: $('input', panel).value || 'Submitted from dashboard', source: 'dashboard' } });
      panel.innerHTML = `${badge('pending_review')} Recommendation #${rec.id} queued for manager review. <a href="#approvals">Open approvals</a>`;
      refreshBadges();
    });
  });

  // ================================================================ INVENTORY
  function balanceView(r, key = 'positions') {
    const host = document.createElement('div');
    host.innerHTML = `<p class="note">Forecast engine ${esc((r.forecast_engine || ['xgboost']).join(', '))} · optimizer ${esc(r.optimization.engine)} · objective €${num(r.optimization.objective_cost, 2)}</p>`;
    const grid = document.createElement('div'); grid.className = 'grid g2'; host.appendChild(grid);
    grid.appendChild(renderChart({ type: 'diverging', title: 'Surplus (+) / gap (−) vs target by DC', subtitle: 'stock + in transit − (forecast + safety stock)', unit: ' units', rows: r[key].map((p) => ({ label: p.warehouse, value: p.surplus_or_gap })) }));
    grid.appendChild(renderChart({ type: 'bar', title: 'Proposed transfers', subtitle: 'quantity per lane · cost and CO₂ in the hint', unit: ' units',
      rows: r.proposed_actions.map((t) => ({ label: `${t.from} → ${t.to}`, value: t.quantity, status: 'info', hint: `€${num(t.estimated_cost, 2)} · ${num(t.carbon_kg, 1)} kg CO₂ · ${t.lead_days} days` })) }));
    const tbl = document.createElement('div'); tbl.className = 'card';
    tbl.innerHTML = table([['Warehouse', (p) => esc(p.warehouse)], ['On hand', (p) => num(p.on_hand), 'num'], ['In transit', (p) => num(p.in_transit_within_horizon), 'num'], ['Forecast demand', (p) => num(p.forecast_demand), 'num'],
      ['Target', (p) => num(p.target_stock), 'num'], ['Surplus / gap', (p) => num(p.surplus_or_gap), 'num'], ['Days of cover', (p) => num(p.days_of_cover, 1), 'num']], r[key]);
    host.appendChild(tbl);
    return host;
  }
  $('#form-balance').addEventListener('submit', (e) => {
    e.preventDefault();
    const f = formData(e.target);
    busy($('button[type=submit]', e.target), async () => {
      const r = await api('/api/v1/analysis/stock-balance', { body: { material: f.material, horizon_days: Number(f.horizon_days), service_level: Number(f.service_level) } });
      const out = $('#balance-out'); out.innerHTML = ''; out.appendChild(balanceView(r)); out.insertAdjacentHTML('beforeend', submitPanel(r));
    });
  });
  $('#btn-whatif').addEventListener('click', (e) => {
    const f = formData($('#form-balance'));
    busy(e.target, async () => {
      const r = await api('/api/v1/analysis/what-if', { body: { material: f.material, demand_change_pct: Number(f.demand_change_pct), horizon_days: Number(f.horizon_days) } });
      const out = $('#balance-out'); out.innerHTML = `<p>${statusBadge('warning')} Hypothetical scenario: demand ${r.scenario.demand_change_pct > 0 ? '+' : ''}${r.scenario.demand_change_pct}% (not submittable)</p>`;
      out.appendChild(balanceView(r, 'scenario_positions'));
    });
  });

  // ================================================================ SALES ORDERS
  async function loadSales() {
    const out = $('#sales-out');
    out.innerHTML = '<p class="note"><span class="spinner"></span>Checking every open order…</p>';
    try {
      const [r, d] = await Promise.all([api('/api/v1/analysis/sales-orders', { body: {} }), api('/api/v1/dashboards/sales')]);
      out.innerHTML = '<div class="kpis" id="so-kpis"></div><div class="grid g2" id="so-charts"></div>';
      kpiTiles('#so-kpis', d.kpis);
      d.charts.forEach((c) => $('#so-charts').appendChild(renderChart(c)));
      out.insertAdjacentHTML('beforeend', `<div class="card"><h2>Orders</h2><p class="sub">Allocated by requested date and priority from DC stock plus inbound arriving in time</p>${table([
        ['Order', (o) => `<b>${esc(o.order)}</b>`], ['Customer', (o) => esc(o.customer)], ['Material', (o) => esc(o.material)], ['DC', (o) => esc(o.warehouse)], ['Qty', (o) => num(o.quantity), 'num'],
        ['Due', (o) => esc(o.requested_date)], ['Priority', (o) => chip(o.priority)], ['Confirmed', (o) => num(o.confirmed), 'num'], ['Status', (o) => badge(o.status)],
        ['Resolution', (o) => (!o.resolution ? '—' : o.resolution.action === 'stock_transfer'
          ? `Transfer <b>${num(o.resolution.quantity)}</b> from ${esc(o.resolution.from)}, arrives ${esc(o.resolution.arrives)} (€${num(o.resolution.estimated_cost)})` : `Partial delivery: ${num(o.resolution.deliverable_now)} now`)],
      ], r.orders)}${submitPanel(r)}</div>`);
    } catch (e) { out.innerHTML = `<div class="empty">${esc(e.message)}</div>`; }
  }

  // ================================================================ STOCKTAKE
  async function loadStocktake() {
    const out = $('#stocktake-out');
    out.innerHTML = '<p class="note"><span class="spinner"></span>Reconciling counts…</p>';
    try {
      const [r, d] = await Promise.all([api('/api/v1/analysis/stocktake', { body: {} }), api('/api/v1/dashboards/stocktake')]);
      out.innerHTML = '<div class="kpis" id="st-kpis"></div><div class="grid g2" id="st-charts"></div>';
      kpiTiles('#st-kpis', d.kpis);
      d.charts.forEach((c) => $('#st-charts').appendChild(renderChart(c)));
      out.insertAdjacentHTML('beforeend', `<div class="card"><h2>Count differences with evidence</h2><p class="sub">Tolerance ${r.tolerance_pct}% · explanations come from unposted goods movements and pending quality decisions</p>${table([
        ['Count', (c) => esc(c.count_id)], ['Location', (c) => esc(c.plant)], ['Material · batch', (c) => `${esc(c.material)}<br><span class="note">${esc(c.batch)}</span>`],
        ['Book', (c) => num(c.book_quantity), 'num'], ['Counted', (c) => num(c.counted_quantity), 'num'], ['Diff', (c) => `<b>${c.difference > 0 ? '+' : ''}${num(c.difference)}</b>`, 'num'],
        ['Status', (c) => badge(c.status)],
        ['Explanation & evidence', (c) => (c.evidence.length ? c.evidence.map((e) => `${esc(e.type.replaceAll('_', ' '))} <b>${esc(e.document)}</b> (${e.quantity > 0 ? '+' : ''}${num(e.quantity)}) — ${esc(e.note || '')}`).join('<br>') : c.difference ? '<span class="note">No movement explains it</span>' : '—')],
        ['Recommendation', (c) => esc((c.recommendation?.action || '—').replaceAll('_', ' '))],
      ], r.counts)}${submitPanel(r)}</div>`);
    } catch (e) { out.innerHTML = `<div class="empty">${esc(e.message)}</div>`; }
  }

  // ================================================================ PRODUCTION
  async function loadProduction() {
    try {
      const d = await api('/api/v1/dashboards/production');
      const box = $('#production-overview');
      box.innerHTML = '<h2>Production orders</h2><p class="sub">Readiness of every planned and released order</p><div class="kpis" id="pr-kpis"></div><div class="grid g2" id="pr-charts"></div>';
      kpiTiles('#pr-kpis', d.kpis);
      d.charts.forEach((c) => { const n = document.createElement('div'); n.appendChild(window.Charts[c.type](c)); $('#pr-charts').appendChild(n); });
    } catch (e) { toast(e.message); }
  }
  $('#form-readiness').addEventListener('submit', (e) => {
    e.preventDefault();
    const body = formData(e.target); body.quantity = Number(body.quantity);
    busy($('button', e.target), async () => {
      const r = await api('/api/v1/analysis/factory-readiness', { body });
      $('#readiness-out').innerHTML = `<p>${badge(r.status, r.status.replace('_', ' ').toUpperCase())} ${num(r.component_readiness_pct, 1)}% of components covered for ${num(r.planned_quantity)} × ${esc(r.material)} at ${esc(r.plant)} by ${esc(r.need_by)}</p>` +
        table([['Component', (c) => esc(c.component)], ['Required', (c) => `${num(c.required, 3)} ${esc(c.uom)}`, 'num'], ['Unrestricted', (c) => num(c.unrestricted_on_hand, 3), 'num'],
          ['Confirmed inbound', (c) => num(c.confirmed_inbound_by_need_date, 3), 'num'], ['Shortage', (c) => num(c.shortage, 3), 'num'], ['Status', (c) => badge(c.status)],
          ['Excluded stock', (c) => esc((c.excluded_stock || []).map((x) => `${x.batch} ${x.status} ${x.quantity}`).join('; ') || '—')]], r.components) + submitPanel(r);
    });
  });

  // ================================================================ SUPPLIERS
  // Every product / site / supplier dropdown is filled from the selected customer's snapshot.
  async function loadSuppliers() {
    try {
      const snap = await api('/api/v1/snapshot');
      state.snapshot = snap;
      const opts = snap.suppliers.map((s) => `<option>${esc(s)}</option>`).join('');
      $('#supplier-select').innerHTML = opts; $('#research-supplier').innerHTML = opts;
      if (snap.suppliers.includes('PackGlass Europe')) $('#supplier-select').value = 'PackGlass Europe';
      if (snap.suppliers.includes('BioActive Labs')) $('#research-supplier').value = 'BioActive Labs';
      const fgs = snap.materials.filter((m) => m.type === 'FG');
      const fgOpts = fgs.map((m) => `<option value="${esc(m.code)}">${esc(m.code)} · ${esc(m.description)}</option>`).join('');
      const factories = snap.plants.filter((p) => p.type !== 'warehouse');
      $('#form-balance [name=material]').innerHTML = fgOpts;
      $('#form-readiness [name=material]').innerHTML = fgOpts;
      $('#form-readiness [name=plant]').innerHTML = factories.map((p) => `<option value="${esc(p.code)}">${esc(p.code)} · ${esc(p.name)}</option>`).join('');
      const h = headlineProduct();
      if (h.material) {
        $('#form-balance [name=material]').value = h.material;
        $('#form-readiness [name=material]').value = h.material;
        const total = Object.values(snap.warehouse_demand_daily[h.material] || {}).reduce((a, b) => a + b, 0);
        $('#form-readiness [name=quantity]').value = Math.max(1, Math.round(total * 10 / 100) * 100);
      }
      state.producedAt = Object.fromEntries((await api('/api/v1/products')).map((p) => [p.material, p.producing_plant]));
      syncReadinessPlant();
      $('#form-readiness [name=need_by]').value = new Date(Date.parse(snap.as_of_date || state.cfg.as_of) + 7 * 864e5).toISOString().slice(0, 10);
      $('#balance-out').innerHTML = ''; $('#readiness-out').innerHTML = ''; $('#supplier-out').innerHTML = '';
    } catch { /* not signed in */ }
  }
  function syncReadinessPlant() {
    const plant = state.producedAt?.[$('#form-readiness [name=material]').value];
    if (plant) $('#form-readiness [name=plant]').value = plant;
  }
  $('#form-readiness [name=material]').addEventListener('change', syncReadinessPlant);
  async function loadSuppliersPage() {
    try {
      const [q, l] = await Promise.all([api('/api/v1/analysis/quality', { body: {} }), api('/api/v1/analysis/logistics', { body: {} })]);
      $('#quality-out').innerHTML = table([['Lot', (x) => esc(x.lot)], ['Plant', (x) => esc(x.plant)], ['Material', (x) => esc(x.material)], ['Qty', (x) => num(x.quantity), 'num'], ['Status', (x) => badge(x.status)], ['Defect / release', (x) => esc(x.defect || x.expected_release || '—')]], q.lots);
      $('#logistics-out').innerHTML = table([['Shipment', (x) => esc(x.shipment)], ['Route', (x) => esc(`${x.from} → ${x.to}`)], ['Qty', (x) => num(x.quantity), 'num'], ['Revised ETA', (x) => esc(x.revised_eta)], ['Delay', (x) => (x.delay_days ? pill(x.escalate ? 'critical' : 'warning', `${x.delay_days} days late`) : pill('good', 'on time'))]], l.shipments);
      if (!$('#supplier-out').innerHTML) $('#form-supplier').requestSubmit();
    } catch (e) { toast(e.message); }
  }
  $('#form-supplier').addEventListener('submit', (e) => {
    e.preventDefault();
    busy($('button', e.target), async () => {
      const r = await api('/api/v1/analysis/supplier-risk', { body: formData(e.target) });
      $('#supplier-out').innerHTML = `<p>${badge(r.risk_rating, `${r.risk_rating} risk · score ${r.risk_score}`)} OTIF ${num(r.otif_pct, 1)}% vs ${r.otif_target_pct}% · rejects ${num(r.quality_reject_pct, 2)}% · lead time ${r.supplier.contract_lead_time_days} d · exposure €${num(r.open_po_exposure_eur)} · ${r.single_source ? 'single source' : 'secondary: ' + esc(r.supplier.secondary_source)}</p>` +
        table([['PO', (x) => esc(x.po)], ['Promised', (x) => esc(x.promised_date)], ['Received', (x) => esc(x.received_date)], ['Delay', (x) => num(x.delay_days), 'num'], ['Rejected', (x) => num(x.quality_rejected), 'num'], ['OTIF', (x) => statusBadge(x.otif ? 'good' : 'critical')]], r.receipts) + submitPanel(r);
    });
  });
  $('#form-rag').addEventListener('submit', (e) => {
    e.preventDefault();
    busy($('button', e.target), async () => {
      const r = await api('/api/v1/rag/search', { body: { query: formData(e.target).query, top_k: 4 } });
      $('#rag-out').innerHTML = r.results.map((h) => `<div class="panel"><b>${esc(h.title)}</b> ${chip(h.category)} <span class="note">score ${h.score}</span><p>${esc(h.text)}</p></div>`).join('');
    });
  });

  // ================================================================ APPROVALS & EXECUTION
  const REASONS = [['', 'Reason (if you change or reject)'], ['supplier_risk', 'Supplier risk'], ['capacity', 'Capacity'], ['cost', 'Cost'], ['timing', 'Timing'],
    ['customer_priority', 'Customer priority'], ['quality', 'Quality'], ['data_quality', 'Data quality'], ['other', 'Other']];
  async function loadApprovals() {
    const filters = [['pending_review', 'Pending review'], ['accepted', 'Accepted · ready to execute'], ['executed', 'Executed'], ['rejected', 'Rejected'], ['', 'All']];
    $('#rec-filters').innerHTML = filters.map(([k, l]) => `<button class="${state.recFilter === k ? 'on' : ''}" data-r="${k}">${esc(l)}</button>`).join('');
    $$('#rec-filters button').forEach((b) => b.addEventListener('click', () => { state.recFilter = b.dataset.r; loadApprovals(); }));
    try {
      const recs = await api(`/api/v1/recommendations${state.recFilter ? `?status=${state.recFilter}` : ''}`);
      const manager = state.role === 'manager';
      $('#recs').innerHTML = recs.length ? recs.map((r) => `<div class="card" data-rec="${r.id}">
        <div class="row" style="justify-content:space-between;margin:0 0 6px"><div><b>#${r.id} · ${esc(r.kind.replaceAll('_', ' '))}</b> ${badge(r.status)}</div><span class="note">${esc(r.analysis_id)} · by ${esc(r.submitted_by)} via ${esc(r.source)} · ${esc(r.submitted_at.slice(0, 16).replace('T', ' '))}</span></div>
        ${table([['Action', (a) => `<b>${esc(a.action.replaceAll('_', ' '))}</b>`], ['Detail', (a) => esc(Object.entries(a).filter(([k]) => k !== 'action').map(([k, v]) => `${k.replaceAll('_', ' ')}: ${Array.isArray(v) ? v.join(', ') : v}`).join(' · '))]], r.actions)}
        <details><summary class="note">Explanation</summary>${md(r.explanation.slice(0, 3000))}</details>
        ${r.status === 'pending_review' ? (manager ? `<div class="decision-row"><select data-reason aria-label="Reason">${REASONS.map(([k, l]) => `<option value="${k}">${esc(l)}</option>`).join('')}</select><input class="grow" placeholder="Why? Your reasoning teaches the AI"><button class="good" data-d="accepted">Approve</button><button class="ghost" data-d="modified">Approve with changes</button><button class="bad" data-d="rejected">Reject</button></div>` : '<p class="note">Awaiting a manager decision.</p>')
          : r.status === 'accepted' ? (manager ? `<div class="row" style="margin-top:10px"><button data-exec>⚡ Execute in SAP (sandbox)</button><span class="note">Creates the documents in the SAP mock sandbox outbox — 1 click, audited.</span></div>` : '<p class="note">Accepted — a manager executes it.</p>')
            : `<p class="note">${esc(r.decided_by ? `Decided by ${r.decided_by}: ${r.decision_comment || ''}` : '')}</p>`}
        <div data-docs></div><div data-outcome></div></div>`).join('') : '<div class="empty">Nothing here.</div>';
      $$('[data-d]').forEach((b) => b.addEventListener('click', () => busy(b, async () => {
        const card = b.closest('[data-rec]');
        const reason = $('[data-reason]', card).value || null;
        if (b.dataset.d !== 'accepted' && !reason) { toast('Pick a reason — it is how SPARC learns from your expertise'); return; }
        await api(`/api/v1/recommendations/${card.dataset.rec}/decision`, { body: { decision: b.dataset.d === 'rejected' ? 'rejected' : 'accepted', modified: b.dataset.d === 'modified',
          reason_code: reason, comment: $('input', card).value } });
        toast(`Recommendation #${card.dataset.rec} ${b.dataset.d === 'modified' ? 'approved with changes' : b.dataset.d}`); loadApprovals(); refreshBadges();
      })));
      $$('[data-exec]').forEach((b) => b.addEventListener('click', () => busy(b, async () => {
        const card = b.closest('[data-rec]');
        const r = await api(`/api/v1/recommendations/${card.dataset.rec}/execute`, { body: {} });
        toast(`Executed: ${r.documents.map((d) => `${d.doc_type} ${d.doc_number}`).join(', ')}`); loadApprovals();
      })));
      const docs = await api('/api/v1/sap/documents');
      // Did it work? Approval is not proof: executed recommendations wait for their real outcome from SAP.
      const learn = await api('/api/v1/learning');
      const byRec = Object.fromEntries(learn.outcomes.map((o) => [o.recommendation_id, o]));
      recs.filter((r) => r.status === 'executed').forEach((r) => {
        const slot = $(`[data-rec="${r.id}"] [data-outcome]`); if (!slot) return;
        const o = byRec[r.id];
        if (o && o.status !== 'awaiting_observation') {
          slot.innerHTML = `<div class="outcome-box done">${pill(o.achieved ? 'good' : 'critical', o.achieved ? 'Outcome verified' : 'Not achieved')} <span>${esc(o.note || '')} · SAP ${esc(o.source_document)}${o.realized_impact_eur ? ` · €${num(o.realized_impact_eur)} realised` : ''} · by ${esc(o.observed_by)}</span></div>`;
          return;
        }
        const doc = docs.find((d) => d.recommendation_id === r.id)?.doc_number || '';
        slot.innerHTML = `<div class="outcome-box"><div><b>Did it work?</b> <span class="note">Record what actually happened in SAP${o?.due_date ? ` (due ${esc(o.due_date)})` : ''} — approval alone is not proof.</span></div>
          ${manager ? `<div class="decision-row"><select data-ach aria-label="Result"><option value="true">Achieved</option><option value="false">Not achieved</option></select>
          <input data-doc placeholder="SAP document" value="${esc(doc)}" aria-label="SAP document"><input data-impact type="number" step="any" placeholder="Realised impact €" aria-label="Realised impact in euros">
          <input data-note class="grow" placeholder="What happened (e.g. DC21 did not stock out)"><button data-out>Record outcome</button></div>` : '<p class="note">A manager records the outcome.</p>'}</div>`;
      });
      $$('[data-out]').forEach((b) => b.addEventListener('click', () => busy(b, async () => {
        const card = b.closest('[data-rec]'); const box = b.closest('.outcome-box');
        const impact = $('[data-impact]', box).value;
        await api(`/api/v1/recommendations/${card.dataset.rec}/outcome`, { body: { achieved: $('[data-ach]', box).value === 'true', source_document: $('[data-doc]', box).value.trim(),
          realized_impact_eur: impact === '' ? null : Number(impact), note: $('[data-note]', box).value, observed: {} } });
        toast(`Outcome recorded for #${card.dataset.rec} — it is now a verified learning label`); loadApprovals();
      })));
      $('#sap-docs').innerHTML = table([['Document', (d) => `<b>${esc(d.doc_number)}</b>`], ['Type', (d) => chip(d.doc_type)], ['Recommendation', (d) => `#${d.recommendation_id}`], ['Payload', (d) => esc(Object.entries(d.payload).map(([k, v]) => `${k}: ${v}`).join(' · '))], ['By', (d) => esc(d.created_by)], ['Status', (d) => esc(d.status.replaceAll('_', ' '))]], docs);
      if (manager) {
        const a = await api('/api/v1/audit?limit=60');
        $('#chain').innerHTML = pill(a.chain_valid ? 'good' : 'critical', a.chain_valid ? 'hash chain valid' : 'hash chain BROKEN');
        $('#audit').innerHTML = table([['Time', (x) => esc(x.ts.slice(0, 19).replace('T', ' '))], ['Actor', (x) => esc(`${x.actor} (${x.role})`)], ['Action', (x) => esc(x.action)], ['Details', (x) => `<code>${esc(JSON.stringify(x.details).slice(0, 140))}</code>`], ['Hash', (x) => `<code>${esc(x.hash.slice(0, 10))}</code>`]], a.events);
      } else { $('#audit').innerHTML = '<p class="note">The audit log is visible to managers.</p>'; }
    } catch (e) { toast(e.message); }
  }

  // ================================================================ INTELLIGENCE MOAT
  const CALC_LINES = [
    ['freight', 'Avoidable emergency freight', 200000, 25, 'Improved supplier predictions'],
    ['expiry', 'Expiry and stock write-offs', 300000, 20, 'Reduced expiry-related waste'],
    ['disruption', 'Production disruption costs', 500000, 15, 'Fewer material shortages'],
    ['labour', 'Manual planning labour', 160000, 25, 'Faster planning'],
    ['balancing', 'Stock-outs, transfers and overstock', 0, 10, 'Better warehouse stock balancing'],
  ];
  function calcState() {
    let saved = {};
    try { saved = JSON.parse(localStorage.getItem(`moatCalc:${state.tenant}`) || '{}'); } catch { /* storage unavailable */ }
    return { currency: saved.currency || '$', lines: CALC_LINES.map(([id, , base, red]) => ({ id, base: saved[id]?.base ?? base, red: saved[id]?.red ?? red })) };
  }
  function renderCalc(m) {
    const s = calcState();
    const cur = s.currency;
    const money = (v) => `${cur}${num(v)}`;
    const rows = CALC_LINES.map(([id, label, , , line], i) => {
      const l = s.lines[i]; const benefit = l.base * l.red / 100; const verified = m.realised_by_line[line] || 0;
      return `<tr><td><b>${esc(label)}</b><br><span class="note">${esc(line)}</span></td>
        <td class="num"><input type="number" min="0" step="1000" data-cb="${id}" value="${l.base}" aria-label="${esc(label)} baseline"></td>
        <td class="num"><input type="number" min="0" max="100" step="1" data-cr="${id}" value="${l.red}" aria-label="${esc(label)} reduction %"> %</td>
        <td class="num"><b>${money(benefit)}</b></td><td class="num">${verified ? `€${num(verified)}` : '—'}</td></tr>`;
    }).join('');
    const total = s.lines.reduce((a, l) => a + l.base * l.red / 100, 0);
    $('#moat-value').innerHTML = `<div class="chart-head"><div><h2>Financial value of the moat</h2><p class="sub">Annual opportunity calculator — replace the illustrative baselines with measured ones; the right column shows only value verified against SAP outcomes</p></div>
      <label class="inline">Currency <select id="calc-cur">${['$', '€', '£'].map((c) => `<option ${c === cur ? 'selected' : ''}>${c}</option>`).join('')}</select></label></div>
      <div class="scroll"><table class="calc"><thead><tr><th>Business benefit</th><th class="num">Annual baseline</th><th class="num">Reduction</th><th class="num">Potential benefit</th><th class="num">Verified so far</th></tr></thead>
      <tbody>${rows}</tbody><tfoot><tr><td><b>Potential annual gross benefit</b></td><td></td><td></td><td class="num"><b class="total">${money(total)}</b></td><td class="num">€${num(Object.values(m.realised_by_line).reduce((a, b) => a + b, 0))}</td></tr></tfoot></table></div>
      <p class="note">Before platform, implementation and attribution adjustments. The calculator does not prove the AI will achieve these reductions; it builds the business case from measured baselines. Example values are illustrative, not customer data.</p>`;
    const save = () => {
      const next = { currency: $('#calc-cur').value };
      CALC_LINES.forEach(([id]) => { next[id] = { base: Number($(`[data-cb="${id}"]`).value) || 0, red: Math.min(100, Number($(`[data-cr="${id}"]`).value) || 0) }; });
      try { localStorage.setItem(`moatCalc:${state.tenant}`, JSON.stringify(next)); } catch { /* storage unavailable */ }
      renderCalc(m);
    };
    $$('#moat-value input').forEach((el) => el.addEventListener('change', save));
    $('#calc-cur').addEventListener('change', save);
  }
  async function loadMoat() {
    try {
      const m = await api('/api/v1/moat');
      const vp = m.value_proposition;
      $('#moat-hero').innerHTML = `<section class="spotlight calm moat-hero"><div><div class="eyebrow">${esc(m.customer)} · ${esc(m.industry_label)}</div><h2>${esc(vp.title)}</h2><p>${esc(vp.text)}</p><p class="moat-line">${esc(vp.moat)}</p></div>
        <div class="cta"><span class="status"><i style="background:var(--${m.consent.industry_learning ? 'good' : 'axis'})"></i>Industry learning ${m.consent.industry_learning ? 'on' : 'off'}</span><span class="note">${esc(m.consent.source)}</span></div></section>`;
      $('#moat-flywheel').innerHTML = m.flywheel.map((s, i) => `<div class="fw-stage"><div class="fw-n">${i + 1}</div><div class="fw-count">${num(s.count)}</div><div class="fw-unit">${esc(s.unit)}</div>
        <h3>${esc(s.stage)}</h3><p>${esc(s.detail)}</p>${s.extra ? `<p class="note">${esc(s.extra)}</p>` : ''}</div>`).join('<div class="fw-arrow" aria-hidden="true">→</div>') +
        '<div class="fw-loop">↺ Better predictions feed back into the AI — valuable only when they measurably improve unseen future decisions</div>';
      $('#moat-metrics').innerHTML = m.metrics.map((x, i) => `<div class="moat-metric"><div class="mm-n">${i + 1}</div><h3>${esc(x.name)}</h3><div class="mm-value">${esc(x.display)}</div><p>${esc(x.question)}</p></div>`).join('');
      $('#moat-sources').innerHTML = table([['Customer data', (x) => `<b>${esc(x.name)}</b><br><span class="note">${esc(x.learns)}</span>`], ['Moat potential', (x) => `<span class="chip pot-${x.potential.replace(/\s+/g, '-').toLowerCase()}">${esc(x.potential)}</span>`],
        ['Evidence in this customer', (x) => esc(x.value)], ['What SPARC has learned', (x) => esc(x.learned)]], m.moats) +
        '<p class="note">The most defensible information is human judgment combined with what actually happened afterwards — for example a supplier that promises 42 days but takes 55, and the planners who switch suppliers when that matters.</p>';
      const mc = m.models;
      $('#moat-models').innerHTML = '<div data-chart></div>' + `<ul class="note">${mc.notes.map((n) => `<li>${esc(n)}</li>`).join('')}</ul>`;
      $('[data-chart]', $('#moat-models')).appendChild(window.Charts.bar({ title: 'Which model predicts this customer best?', subtitle: 'forecast error (WAPE %) on this customer’s 14-day holdout — lower is better', unit: '%',
        rows: [['Customer-only model', mc.customer_only_wape, 'good'], ['Simple baseline (last week)', mc.baseline_wape, 'info'], ['Generic model (all consenting)', mc.generic_wape, 'info'],
          ['Industry model', mc.industry_wape, 'info'], ['Cold start (new customer)', mc.cold_start_wape, 'warning']].filter((r) => r[1] !== null).map(([label, value, status]) => ({ label, value, status })) }));
      const manager = state.role === 'manager';
      $('#moat-consent').innerHTML = `<h2>Consent, privacy and quality gate</h2><p class="sub">Industry learning uses a customer's data only with its recorded consent; only authorised features or protected model contributions pass the gate</p>
        <div class="gate">${m.industry_customers.map((c) => `<div class="gate-row"><span class="status"><i style="background:var(--${c.industry_learning ? 'good' : 'axis'})"></i>${c.industry_learning ? 'contributes' : 'private only'}</span>
          <b>${esc(c.customer)}</b><span class="note">${esc(c.source)}</span></div>`).join('')}
          <div class="gate-arrow">↓ consent · privacy · quality gate ↓</div><div class="gate-model"><b>${esc(m.industry_label)} industry intelligence model</b><span class="note">tested against each customer-only model before improvements return to customer agents</span></div></div>
        ${manager ? `<div class="row" style="margin-top:12px"><button class="${m.consent.industry_learning ? 'bad' : ''}" id="consent-toggle">${m.consent.industry_learning ? 'Stop sharing with industry learning' : `Allow ${esc(m.customer)} to contribute`}</button><span class="note">recorded and audited; the customer keeps control</span></div>` : '<p class="note">A manager of this customer controls consent.</p>'}`;
      $('#consent-toggle')?.addEventListener('click', (e) => busy(e.currentTarget, async () => { await api('/api/v1/moat/consent', { body: { industry_learning: !m.consent.industry_learning } }); toast('Consent updated'); loadMoat(); }));
      renderCalc(m);
      $('#moat-learning').innerHTML = `<h2>Learning evidence</h2><p class="sub">what the data proves today — and what still needs real data</p>${table([['Learning metric', (x) => `<b>${esc(x.metric)}</b><br><span class="note">${esc(x.proves)}</span>`],
        ['Status', (x) => pill(x.status === 'measured' ? 'good' : x.status === 'awaiting data' ? 'warning' : 'info', x.status)], ['Now', (x) => esc(x.value)]], m.data_moat)}`;
      $('#moat-ownership').innerHTML = `<h2>Customer moat vs platform moat</h2><p class="sub">Customers keep their contractual rights and control of their data</p>${table([['', (x) => `<b>${esc(x.aspect)}</b>`], ['Customer’s moat', (x) => esc(x.customer)], ['SPARC’s moat', (x) => esc(x.platform)]], m.ownership)}
        <p class="note">SPARC's moat comes from technology, trusted integration, reusable expertise and explicitly authorised cross-customer learning — never from owning customer data. Industry models are always tested against customer-only models: more customers do not automatically mean better predictions.</p>`;
    } catch (e) { toast(e.message); }
  }

  // ================================================================ WATCHES
  async function loadWatches() {
    try {
      state.kinds = await api('/api/v1/watches/kinds');
      const sel = $('#watch-kind');
      if (!sel.options.length) {
        sel.innerHTML = Object.entries(state.kinds).map(([k, v]) => `<option value="${k}">${esc(v.label)}</option>`).join('');
        sel.addEventListener('change', watchParams); watchParams();
      }
      const r = await api('/api/v1/watches/evaluate', { body: {} });
      $('#watch-list').innerHTML = table([['Watch', (w) => `<b>${esc(w.name)}</b><br><span class="note">${esc(state.kinds[w.kind]?.label || w.kind)}</span>`],
        ['Now', (w) => esc(w.text)], ['State', (w) => (w.kind === 'question' ? chip('saved question') : pill(w.triggered ? 'critical' : 'good', w.triggered ? 'Triggered' : 'OK'))],
        ['Change', (w) => (w.changed ? `from ${esc(String(w.previous_value))}` : '—')], ['', (w) => `${w.kind === 'question' ? `<button class="ghost small" data-q="${esc(w.params.question)}">Ask</button> ` : ''}<button class="ghost small" data-del="${w.id}">Remove</button>`]], r.watches);
      $$('#watch-list [data-del]').forEach((b) => b.addEventListener('click', () => busy(b, async () => { await api(`/api/v1/watches/${b.dataset.del}`, { method: 'DELETE' }); loadWatches(); })));
      $$('#watch-list [data-q]').forEach((b) => b.addEventListener('click', () => openDrawer(b.dataset.q)));
    } catch (e) { toast(e.message); }
  }
  function watchParams() {
    const kind = $('#watch-kind').value;
    const spec = state.kinds[kind];
    const snap = state.snapshot || { materials: [], plants: [], suppliers: [] };
    const field = { material: `<label>Material<select name="p_material">${snap.materials.filter((m) => m.type === 'FG').map((m) => `<option>${esc(m.code)}</option>`).join('')}</select></label>`,
      warehouse: `<label>Warehouse<select name="p_warehouse">${snap.plants.filter((p) => p.type === 'warehouse').map((p) => `<option>${esc(p.code)}</option>`).join('')}</select></label>`,
      supplier: `<label>Supplier<select name="p_supplier">${snap.suppliers.map((s) => `<option>${esc(s)}</option>`).join('')}</select></label>`,
      question: '<label class="grow">Question<input name="p_question" required placeholder="Which orders are at risk this week?"></label>' };
    $('#watch-params').innerHTML = spec.params.map((p) => field[p]).join('');
    $('#watch-threshold').value = spec.default;
    $('#watch-threshold').closest('label').hidden = kind === 'question';
  }
  $('#form-watch').addEventListener('submit', (e) => {
    e.preventDefault();
    const f = formData(e.target);
    const params = Object.fromEntries(Object.entries(f).filter(([k]) => k.startsWith('p_')).map(([k, v]) => [k.slice(2), v]));
    busy($('button[type=submit]', e.target), async () => {
      await api('/api/v1/watches', { body: { name: f.name, kind: f.kind, params, threshold: Number(f.threshold || 0) } });
      e.target.name.value = ''; toast('Watch added'); loadWatches();
    });
  });
  $('#eval-watches').addEventListener('click', loadWatches);

  // ================================================================ AGENTS (Flowise + LangGraph)
  const ENGINES = {
    'fw-chatflow': { label: 'Flowise · Chatflow', backend: 'Flowise' }, 'fw-agentflow': { label: 'Flowise · AgentFlow V2', backend: 'Flowise' },
    'lg-chat': { label: 'LangGraph · Chat Graph', backend: 'LangGraph Server' }, 'lg-agentflow': { label: 'LangGraph · AgentFlow', backend: 'LangGraph Server' },
  };
  async function callEngine(engine, conv, text, resume) {
    if (engine === 'lg-chat') {
      const r = await api('/api/v1/chat', { body: { message: text, thread_id: conv.thread, ...(conv.role ? { role: conv.role } : {}) } });
      conv.thread = r.thread_id;
      return { html: md(r.answer), meta: `${r.runtime} · tools: ${r.tools_used.join(', ') || 'none'} · ${r.elapsed_seconds}s` };
    }
    if (engine === 'lg-agentflow') {
      const r = resume ? await api(`/api/v1/langgraph/agentflow/${encodeURIComponent(conv.thread)}/resume`, { body: resume })
        : await api('/api/v1/langgraph/agentflow', { body: { message: text, thread_id: conv.thread } });
      conv.thread = r.thread_id;
      const out = { html: md(r.answer || '(no text)'), meta: `${r.runtime} · route: ${r.route || '—'} · tools: ${r.tools_used.join(', ') || 'none'}${r.status ? ' · ' + r.status : ''} · ${r.elapsed_seconds}s` };
      if (r.interrupts?.length) { const it = r.interrupts[0]; out.approval = { title: `interrupt() · ${it.question}`, actions: it.proposed_actions, decide: (ok, fb) => ({ decision: ok ? 'submit' : 'discard', comment: fb }) }; }
      return out;
    }
    const flow = engine === 'fw-chatflow' ? 'chatflow' : 'agentflow';
    conv.thread = conv.thread || crypto.randomUUID();
    const r = await api(`/api/v1/flowise/${flow}/predict`, { body: { question: text || '', session_id: conv.thread, ...(resume ? { human_input: resume } : {}) } });
    const path = r.agent_flow_executed?.length ? ` · path: ${r.agent_flow_executed.map((n) => n.node).join(' → ')}` : '';
    const out = { html: md(r.text || '(no text)'), meta: `Flowise ${flow} · tools: ${r.used_tools.join(', ') || 'none'}${path} · ${r.elapsed_seconds}s` };
    if (r.action?.data?.nodeId) { const nodeId = r.action.data.nodeId; out.approval = { title: `Human Input · ${r.action.data.nodeLabel}`, decide: (ok, fb) => ({ type: ok ? 'proceed' : 'reject', startNodeId: nodeId, feedback: fb }) }; }
    return out;
  }
  class Conversation {
    constructor(log, engine) { this.log = log; this.engine = engine; this.thread = null; }
    reset(engine) { this.engine = engine || this.engine; this.thread = null; this.log.innerHTML = ''; }
    add(role, html, meta = '') {
      const div = document.createElement('div');
      div.className = `msg ${role}`; div.innerHTML = html + (meta ? `<div class="meta">${esc(meta)}</div>` : '');
      this.log.appendChild(div); this.log.scrollTop = this.log.scrollHeight;
      return div;
    }
    async send(text, resume) {
      if (!state.key) { toast('Sign in first'); return; }
      if (text) this.add('user', esc(text));
      const pending = this.add('bot', `<span class="spinner"></span>${esc(ENGINES[this.engine].label)} is working…`);
      try {
        const out = await callEngine(this.engine, this, text, resume);
        pending.innerHTML = out.html + `<div class="meta">${esc(ENGINES[this.engine].label)} · ${esc(out.meta)}</div>`;
        if (out.approval) this.approval(out.approval);
      } catch (e) { pending.innerHTML = `${statusBadge('critical')} ${esc(e.message)}`; }
      this.onChange?.();
    }
    approval(a) {
      const box = this.add('bot', `<b>Planner approval required</b> — ${esc(a.title)}${a.actions ? `<pre>${esc(JSON.stringify(a.actions, null, 2))}</pre>` : ''}
        <div class="row" style="margin-top:8px"><input class="grow" placeholder="Comment (optional)"><button class="good">Approve &amp; submit</button><button class="bad">Reject</button></div>`);
      const go2 = (ok) => { const fb = $('input', box).value; box.remove(); this.add('user', ok ? 'Approve &amp; submit' : 'Reject'); this.send('', a.decide(ok, fb)); refreshBadges(); };
      $('button.good', box).onclick = () => go2(true); $('button.bad', box).onclick = () => go2(false);
    }
  }
  // chat page
  const chat = new Conversation($('#messages'), $('#engine').value);
  const threadLabel = () => { $('#thread-label').textContent = chat.thread ? `thread ${chat.thread.slice(0, 8)}… on ${ENGINES[chat.engine].backend}` : `new thread on ${ENGINES[chat.engine].backend}`; };
  chat.onChange = threadLabel; threadLabel();
  $('#engine').addEventListener('change', () => { chat.reset($('#engine').value); threadLabel(); });
  $('#new-thread').addEventListener('click', () => { chat.reset(); threadLabel(); });
  $$('#suggestions button').forEach((b) => b.addEventListener('click', () => chat.send(b.textContent)));
  $('#form-chat').addEventListener('submit', (e) => { e.preventDefault(); const t = $('#chat-input').value.trim(); if (t) { $('#chat-input').value = ''; chat.send(t); } });
  // drawer (copilot on every page)
  const drawer = new Conversation($('#drawer-log'), $('#drawer-engine').value);
  function openDrawer(question, role = null) {
    // A role opens that role's specialised agent (LangGraph chat with the role's mission and tools); otherwise the general copilot.
    if (role !== (drawer.role || null)) {
      drawer.role = role;
      drawer.reset(role ? 'lg-chat' : $('#drawer-engine').value);
      $('#drawer-engine').value = drawer.engine;
    }
    const spec = role && state.roleCat?.find((r) => r.id === role);
    $('#drawer-title').textContent = spec ? spec.agent : 'Copilot';
    $('#drawer').classList.add('open'); if (question) drawer.send(question); $('#drawer-input').focus();
  }
  $('#drawer-close').addEventListener('click', () => $('#drawer').classList.remove('open'));
  $('#drawer-engine').addEventListener('change', () => { drawer.role = null; $('#drawer-title').textContent = 'Copilot'; drawer.reset($('#drawer-engine').value); });
  $('#drawer-form').addEventListener('submit', (e) => { e.preventDefault(); const t = $('#drawer-input').value.trim(); if (t) { $('#drawer-input').value = ''; drawer.send(t); } });
  $('#askbar').addEventListener('submit', (e) => { e.preventDefault(); const t = $('#ask-input').value.trim(); if (t) { $('#ask-input').value = ''; openDrawer(t); } });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') $('#drawer').classList.remove('open'); if ((e.key === '/' && document.activeElement === document.body) || (e.key === 'k' && (e.metaKey || e.ctrlKey))) { e.preventDefault(); $('#ask-input').focus(); } });
  // compare
  const PAIRS = { agent: ['fw-agentflow', 'lg-agentflow'], chat: ['fw-chatflow', 'lg-chat'] };
  const left = new Conversation($('#left-log'), 'fw-agentflow');
  const right = new Conversation($('#right-log'), 'lg-agentflow');
  function setPairing() { const [l, r] = PAIRS[$('#pairing').value]; left.reset(l); right.reset(r); $('#left-title').textContent = ENGINES[l].label; $('#right-title').textContent = ENGINES[r].label; }
  $('#pairing').addEventListener('change', setPairing); $('#compare-reset').addEventListener('click', setPairing); setPairing();
  $$('#compare-suggestions button').forEach((b) => b.addEventListener('click', () => { left.send(b.textContent); right.send(b.textContent); }));
  $('#form-compare').addEventListener('submit', (e) => { e.preventDefault(); const t = $('#compare-input').value.trim(); if (t) { $('#compare-input').value = ''; left.send(t); right.send(t); } });
  // business graph
  function renderWorkflow(r) {
    const v = r.values;
    let html = `<p>${badge(r.interrupts.length ? 'at_risk' : v.status || 'plan', r.interrupts.length ? 'awaiting planner decision' : (v.status || 'running').replaceAll('_', ' '))} <span class="note">thread ${esc(r.thread_id)} · ${esc(r.runtime)} · ${r.elapsed_seconds}s</span></p>`;
    if (v.errors?.length) html += `<div class="panel">${v.errors.map((x) => `<p>${esc(x)}</p>`).join('')}</div>`;
    if (v.request_type) html += `<p class="note">Workflow <b>${esc(v.request_type)}</b> · ${esc(['plant', 'material', 'quantity', 'need_by', 'supplier', 'warehouse'].filter((k) => v[k]).map((k) => `${k}=${v[k]}`).join(' · '))}</p>`;
    if (v.narrative) html += `<div class="panel"><b>Briefing</b> <span class="note">${esc(v.narrative_source)}</span>${md(v.narrative)}</div>`;
    if (v.policy_evidence?.length) html += `<div class="panel"><b>Policy evidence</b>${v.policy_evidence.map((p) => `<p><b>${esc(p.title)}</b> — ${esc(p.text.slice(0, 240))}…</p>`).join('')}</div>`;
    if (r.interrupts.length) { const it = r.interrupts[0]; html += `<div class="panel"><b>interrupt():</b> ${esc(it.question)}<pre>${esc(JSON.stringify(it.proposed_actions, null, 2))}</pre><div class="row"><input class="grow" id="wf-comment" placeholder="Comment"><button class="good" data-wf="submit">Submit to review queue</button><button class="bad" data-wf="discard">Discard</button></div></div>`; }
    if (v.recommendation) html += `<div class="panel">${badge('pending_review')} Recommendation #${v.recommendation.id} created from ${esc(v.recommendation.analysis_id)}.</div>`;
    $('#workflow-out').innerHTML = html;
    $$('[data-wf]').forEach((b) => b.addEventListener('click', () => busy(b, async () => renderWorkflow(await api(`/api/v1/workflows/business/${encodeURIComponent(r.thread_id)}/resume`, { body: { decision: b.dataset.wf, comment: $('#wf-comment')?.value || '' } })))));
  }
  $('#form-workflow').addEventListener('submit', (e) => { e.preventDefault(); busy($('button', e.target), async () => renderWorkflow(await api('/api/v1/workflows/business', { body: { request_text: formData(e.target).request_text } }))); });
  // deep agent
  // Deep Agent harness settings: stored in the governance DB, edited by a manager, applied to every research run.
  const HARNESS_LABELS = { 'contract-analyst': 'Contract analyst', 'quality-analyst': 'Quality analyst', 'logistics-analyst': 'Logistics analyst' };
  // Plain-language help shown under each harness setting: what it means and what changes when you change it.
  const HARNESS_HELP = {
    temperature: 'How much randomness the model uses when writing. 0 = the same, most factual answer every time (recommended). Higher (0.3–0.7) = more varied wording, but more risk of invented details. Range 0–1.',
    max_tokens: 'The longest text the model may write in one step (1 token ≈ ¾ word, so 1,500 ≈ 1,100 words). Lower = shorter, faster replies, but long reports can be cut off. Higher = longer reports, slower. Range 256–4,000.',
    max_steps: 'The limit of the agent loop: every model call and every tool or subagent call is one step. When the budget is used up the run stops with an error instead of looping forever. Lower = faster and cheaper, but deep research may stop early. Higher = more thorough, slower. Range 20–200.',
    report_style: 'Full report = sections: risk rating, evidence, contract levers, recommended actions, approvals required. Executive summary = at most 8 bullet points: risk rating, the 3 key facts, recommended actions.',
    subagents: 'Helper agents the main agent can hand a sub-task to. Untick one and the main agent does that part itself (or skips it). Each subagent always keeps its own tools, listed below.',
    'contract-analyst': 'Reads supplier contracts: lead time, OTIF target, expedite clause, penalties, second source. Tool: search_governed_knowledge.',
    'quality-analyst': 'Checks inspection lots, rejected or blocked batches and quality policy. Tools: quality_status, search_governed_knowledge.',
    'logistics-analyst': 'Checks inbound shipments, delays and carrier SLAs. Tools: logistics_status, search_governed_knowledge.',
    tools: 'The read-only data sources the main agent may call. Untick a tool and the agent can no longer use that data. At least one must stay ticked. No tool can change SAP or anything else.',
    supplier_risk: 'Supplier scorecard: on-time delivery, delays, rejected lots, open-order exposure (calculated, not AI).',
    sap_snapshot: 'Valid SAP codes and master data: plants, materials, suppliers.',
    search_governed_knowledge: 'Searches contracts, SOPs and policies and returns cited excerpts.',
    quality_status: 'Inspection lots, blocked stock and the production orders they affect.',
    logistics_status: 'Shipments, delays and escalations.',
    factory_material_readiness: 'Whether a production order has all its components on time.',
    max_model_calls: 'Thinking turns: how many times the main agent may call the model in one run (each turn it decides the next step). When reached, the run ends gracefully with what it found so far. Lower = faster, shorter research; higher = more thorough. Range 3–50.',
    max_tool_calls: 'Total data look-ups and subagent delegations per run. When reached, further calls are refused and the agent must finish with the evidence it has. Lower = cheaper and faster; higher = broader research. Range 1–60.',
    max_calls_per_tool: 'Repeat guard: the most times any single tool (e.g. supplier_risk) may be called in one run. Stops the agent asking the same question again and again. Range 1–20.',
    max_subagent_calls: 'How many times the agent may hand a sub-task to a subagent. 0 = no delegation at all, including Deep Agents\' built-in general-purpose helper. Each delegation runs a whole helper agent, so it is the most expensive step. Range 0–10.',
    model_timeout_seconds: 'How long to wait for one model answer before giving up. Lower = fails faster when the model server is slow or stuck; too low cuts off long answers on a slow GPU / CPU. Range 15–600 s.',
    model_retries: 'How many times a failed or timed-out model call is retried before the run fails. More retries = more resilient, but a stuck model server makes the run take longer. Range 0–5.',
    tool_retries: 'How many times a failed data tool call (e.g. a gateway timeout) is retried, with a short back-off, before the error is shown to the agent. Range 0–3.',
    require_plan: 'Tells the agent to write a short to-do plan before researching (shown in the result). Off = it starts researching straight away. An instruction to the model, not a hard check.',
    require_citations: 'Tells the agent to quote analysis ids, PO numbers, inspection lots and document titles for every claim. Off = shorter text with fewer references. An instruction to the model, not a hard check.',
  };
  // ---------------------------------------------------------------- harness guide (explains every setting with the live values)
  const SUBAGENT_GUIDE = [
    ['contract-analyst', 'Contract analyst', 'Investigates the supplier contract: lead time, OTIF target, expedite clause, penalties, second-source rights — the contract levers.', 'No dedicated contract investigation; the supervisor reads contracts itself if search_governed_knowledge is allowed.', 'search_governed_knowledge'],
    ['quality-analyst', 'Quality analyst', 'Examines inspection lots, rejected or blocked batches, quality holds and quality policy.', 'No dedicated quality investigation.', 'quality_status, search_governed_knowledge'],
    ['logistics-analyst', 'Logistics analyst', 'Examines inbound shipments, delays, revised ETAs and carrier SLAs (only when they matter for the request).', 'No dedicated logistics investigation.', 'logistics_status, search_governed_knowledge'],
  ];
  const TOOL_GUIDE = [
    ['supplier_risk', 'Supplier scorecard: on-time delivery, average delay, reject rate, open-order exposure, single-source risk (calculated, not AI).', 'Is BioActive Labs a high-risk supplier?'],
    ['sap_snapshot', 'Valid SAP codes and master data from the read-only SAP snapshot: plants, materials, suppliers.', 'Which materials does BioActive Labs supply, to which plant?'],
    ['search_governed_knowledge', 'Searches the approved contracts, SOPs and policies (RAG, PostgreSQL + pgvector) and returns cited excerpts.', 'What does the contract say about late deliveries?'],
    ['quality_status', 'Inspection lots, blocked stock and the production orders they affect.', 'Are any BioActive Labs batches on hold?'],
    ['logistics_status', 'Shipments, delays and escalations.', 'When is the next shipment expected?'],
    ['factory_material_readiness', 'Whether a production order has all its components on time (BOM netting).', 'Can we produce 6,000 serums with the material available?'],
  ];
  function renderHarnessGuide(v) {
    const h = v.harness, on = (b) => (b ? pill('good', 'on') : pill('warning', 'off'));
    const rows = (list) => table(list[0].map((head, i) => [head, (r) => r[i]]), list.slice(1));
    const box = (title, text) => `<div class="guide-box"><b>${title}</b>${text ? `<span>${text}</span>` : ''}</div>`;
    const flow = (...items) => `<div class="guide-flow">${items.join('<span class="guide-arrow">→</span>')}</div>`;
    $('#harness-guide').innerHTML = `<details class="more harness-guide" open><summary><b>Understanding the harness</b> — what each setting does, with the values in force now</summary>
      <p>Think of the Deep Agent as an employee and the <b>harness</b> as its operating procedures: which helpers it may call, which tools it may use,
        how much effort it may spend and what its report must look like. The language model (${esc(state.cfg.llm_model || 'Qwen')}) provides the reasoning;
        the harness controls how that reasoning is used. A manager saves it, every change is audited, and the next research run uses it.</p>

      <h3>1 · Model and execution</h3>
      ${rows([['Setting', 'Now', 'What it does', 'Guidance'],
        ['Temperature', num(h.temperature, 2), 'Randomness of the model\'s wording. 0 = the same, most deterministic answer every time; higher = more variety and more risk of invented detail.', '0–0.3 for evidence-based supplier analysis'],
        ['Max output tokens', num(h.max_tokens), 'Longest text the model may write <b>in one model call</b> (1 token ≈ ¾ word). It limits each answer, not the whole research.', '2,500–4,000 for a detailed report that merges three analysts (the model reads at most 16k tokens in total)'],
        ['Step budget', num(h.max_steps), 'Hard stop for the whole LangGraph run. Every graph step counts (model calls, tool calls, internal steps), so 60 steps is <b>not</b> 60 model calls. When it is exceeded the run fails with an error.', 'Keep it above the loop controls below (60–80) so they end the run first, gracefully'],
        ['Report style', h.report_style === 'full' ? 'Full report' : 'Executive summary', 'Full = risk rating, evidence, contract levers, recommended advisory actions, approvals required. Executive = at most 8 bullets.', 'Full for buyers; executive for leadership']])}

      <h3>2 · Loop controls and reliability — how much effort, and what happens on failure</h3>
      <p class="note">The agent works in a loop: think → call a tool or a subagent → read the result → think again … until it writes the report. These limits are enforced in code around every model and tool call (not just requested in the prompt). Reaching one ends the run <b>gracefully</b>: the agent is told to finish with the evidence it has.</p>
      ${rows([['Setting', 'Now', 'What it does'],
        ['Max model calls', num(h.max_model_calls), 'Thinking turns of the supervisor per run.'],
        ['Max tool calls', num(h.max_tool_calls), 'All data look-ups and delegations together per run; further calls are refused.'],
        ['Max calls of one tool', num(h.max_calls_per_tool), 'Repeat guard: stops the agent asking the same tool again and again.'],
        ['Max subagent delegations', num(h.max_subagent_calls), 'How often it may hand work to a subagent. 0 = none at all, including Deep Agents\' built-in general-purpose helper.'],
        ['Model timeout', `${num(h.model_timeout_seconds)} s`, 'Give up on one model answer after this long (a slow CPU needs more).'],
        ['Model retries · tool retries', `${num(h.model_retries)} · ${num(h.tool_retries)}`, 'Retries of a failed model call / a failed tool call (with a short back-off) before the error counts.']])}

      <h3>3 · Subagents — who does the work</h3>
      <div class="guide-tree">${box('Deep Agent supervisor', 'plans the research, delegates, consolidates the evidence')}
        <div class="guide-children">${SUBAGENT_GUIDE.map(([id, label]) => box(`${label} ${h.subagents.includes(id) ? '✓' : '✗'}`, '')).join('')}${box('General-purpose helper', 'built into Deep Agents')}</div></div>
      ${rows([['Subagent', 'Now', 'When enabled', 'When disabled', 'Its own tools'],
        ...SUBAGENT_GUIDE.map(([id, label, yes, no, tools]) => [label, on(h.subagents.includes(id)), yes, no, `<code>${tools}</code>`])])}
      <p class="note">Enabling a subagent makes it <b>available</b>; the supervisor decides whether to call it (its instructions ask for contract terms → contract analyst, quality evidence → quality analyst, shipments → logistics analyst only when they matter). Subagents keep their own tools listed above even if you untick them under Allowed tools.</p>

      <h3>4 · Allowed tools — what the supervisor may read</h3>
      ${rows([['Tool', 'Now', 'Purpose', 'Example question'], ...TOOL_GUIDE.map(([t, purpose, ex]) => [`<code>${t}</code>`, on(h.tools.includes(t)), purpose, esc(ex)])])}
      ${flow(box('Deep Agent (LangGraph)', 'gets only the allowed tools'), box('SPARC tool functions', 'Python, read-only'), box('FastAPI gateway', 'API key, audit, metrics'),
        box('SAP snapshot', 'read-only OData · writes → 405') + box('RAG knowledge', 'contracts, SOPs, policies') + box('Quality · logistics', 'lots, shipments'))}
      <p class="note"><b>Security:</b> unticking a tool removes it from the supervisor's tool list in code, so it cannot be called. Separately, every tool is read-only and the gateway enforces it (SAP writes return 405) — the UI is not the protection.</p>

      <h3>5 · Rules — how the report must be written</h3>
      ${rows([['Rule', 'Now', 'What it means', 'Why it matters'],
        ['Plan first (todo list)', on(h.require_plan), 'The agent writes a research plan before investigating.', 'Structured, traceable multi-step work'],
        ['Cite evidence for every claim', on(h.require_citations), 'Conclusions must name their source: analysis id, PO number, inspection lot, document title.', 'Fewer unsupported statements; auditable reports']])}
      <p class="note">Not this: <i>"BioActive Labs is a high supply risk."</i> — but this: <i>"BioActive Labs is a high supply risk: average delay 12.7 days against a 95 % OTIF target, single source for RM-ACTIVE (source: supplier_risk scorecard; supply agreement)."</i>
        Both rules are <b>instructions to the model</b>; they are not checked in code yet, so a citation can still be wrong. Programmatic citation checking is the next step for production.</p>

      <h3>6 · Save, reset and audit</h3>
      ${rows([['Control', 'What it does'],
        ['Save harness', 'Stores the settings; the next research run uses them. Only a manager key can save (others get 403); out-of-range values are refused (422).'],
        ['Reset to defaults', 'Restores the built-in defaults (see the line under the form).'],
        ['Last changed by', v.updated_by ? `${esc(v.updated_by)} on ${esc(v.updated_at.slice(0, 16).replace('T', ' '))}` : 'Not changed yet — defaults in force.'],
        ['Audit', 'Every save is written to the tamper-evident audit chain (action agent.deep_research.harness_updated).'],
        ['Read-only', 'This agent can only read and recommend; it never changes SAP or executes anything.'],
        ['LangGraph Studio', 'A run started in Studio uses only the harness typed into it (or the code defaults) — it bypasses the saved settings and the audit.']])}

      <h3>7 · Example — researching BioActive Labs</h3>
      ${flow(box('1 Request', 'Assess supply continuity, quality and contract risk'), box('2 Harness loaded', 'settings · allowed tools · limits · rules'),
        box('3 Plan', 'todo list: scorecard, contract, quality, logistics'), box('4 Evidence', 'supplier_risk + delegate to contract / quality analysts'),
        box('5 Consolidate', 'cross-check, risks, contract levers'), box('6 Cited report', 'risk rating · evidence · levers · actions · approvals'))}
      <p class="note">Measured on this machine (Qwen 2.5 7B): saved settings → about 90 s, 5 tool calls including 3 delegations; tight limits (2 tool calls, no delegation) → about 27 s, still a complete short report.</p>

      <h3>8 · Suggested configuration for supplier research</h3>
      ${rows([['Setting', 'Suggested'], ['Temperature', '0–0.3'], ['Max output tokens', '2,500–4,000'], ['Step budget', '60–80'],
        ['Max model calls · tool calls · per tool · delegations', '15 · 20 · 6 · 3–4'], ['Model timeout', '120–180 s (more on CPU-only machines)'],
        ['Subagents · tools', 'All three · all six for full supplier research'], ['Plan first · cite evidence', 'On · on (add code-level citation checks for production)']])}

      <h3>9 · Agent versus harness</h3>
      ${rows([['The AI agent', 'The harness'], ['Understands the objective', 'Defines the operating constraints'], ['Reasons about the problem', 'Controls the permitted resources and effort'],
        ['Decides which tool to use', 'Restricts which tools exist for it'], ['Delegates to subagents', 'Defines which subagents are available and how often'],
        ['Produces conclusions', 'Defines the report format and evidence rules'], ['Uses the LLM', 'Sets the model parameters, timeouts and retries']])}
      <p class="note">The harness is not a separate LangGraph product: in SPARC it is application code — settings stored in the governance database (<code>DeepAgentHarness</code>), the agent built from them (<code>deep_agent.py</code>: tools, subagents, prompt, loop guard, retries, step budget), the manager-only audited API, and this page.</p>
    </details>`;
  }
  async function loadHarness() {
    const box = $('#harness-card');
    try {
      const v = await api('/api/v1/deep-agents/harness');
      const h = v.harness, o = v.options, manager = state.role === 'manager';
      const dis = manager ? '' : 'disabled';
      const hint = (key) => `<small class="harness-hint">${esc(HARNESS_HELP[key])}</small>`;
      const option = (name, value, label, checked) => `<div class="harness-option"><label class="inline check"><input type="checkbox" name="${name}" value="${esc(value)}" ${checked ? 'checked' : ''} ${dis}>${esc(label)}</label>${hint(value)}</div>`;
      const checks = (name, list, labels = {}) => list.map((x) => option(name, x, labels[x] || x, h[name].includes(x))).join('');
      const numField = (name, label, step) => `<label>${esc(label)}<input name="${name}" type="number" step="${step}" min="${o.ranges[name][0]}" max="${o.ranges[name][1]}" value="${h[name]}" ${dis}>${hint(name)}</label>`;
      const NUMBERS = ['temperature', 'max_tokens', 'max_steps', 'max_model_calls', 'max_tool_calls', 'max_calls_per_tool', 'max_subagent_calls', 'model_timeout_seconds', 'model_retries', 'tool_retries'];
      box.innerHTML = `<div class="chart-head"><div><h2>Harness settings</h2><p class="sub">how the Deep Agent runs — model, step budget, subagents, tools and output rules · ${v.updated_by ? `last changed by ${esc(v.updated_by)} ${esc(v.updated_at.slice(0, 16).replace('T', ' '))}` : 'defaults'}</p></div></div>
        <div class="harness-loop"><b>How the agent works — the loop</b>
          <span>① reads the task${h.require_plan ? ' and writes a plan' : ''}</span><span>→ ② calls a tool or hands a sub-task to a subagent</span><span>→ ③ reads the result and decides the next step</span><span>→ back to ② … until ④ it writes the report.</span>
          <small class="harness-hint">The <b>loop controls</b> below end the loop gracefully (max model calls, tool calls, calls of one tool, delegations); the <b>step budget</b> is the hard stop behind them. Settings apply to the next run.</small></div>
        <form id="form-harness" class="harness">
          <div class="harness-fields">
            <label>Temperature<input name="temperature" type="number" step="0.1" min="${o.ranges.temperature[0]}" max="${o.ranges.temperature[1]}" value="${h.temperature}" ${dis}>${hint('temperature')}</label>
            <label>Max output tokens<input name="max_tokens" type="number" step="50" min="${o.ranges.max_tokens[0]}" max="${o.ranges.max_tokens[1]}" value="${h.max_tokens}" ${dis}>${hint('max_tokens')}</label>
            <label>Step budget (loop limit)<input name="max_steps" type="number" step="5" min="${o.ranges.max_steps[0]}" max="${o.ranges.max_steps[1]}" value="${h.max_steps}" ${dis}>${hint('max_steps')}</label>
            <label>Report style<select name="report_style" ${dis}>${o.report_style.map((s) => `<option value="${s}" ${h.report_style === s ? 'selected' : ''}>${s === 'full' ? 'Full report' : 'Executive summary'}</option>`).join('')}</select>${hint('report_style')}</label></div>
          <div class="harness-section"><b>Loop controls</b><small class="harness-hint">Limits on the agent loop. The step budget above is the hard stop (the run fails); these end the run gracefully with the work done so far.</small>
            <div class="harness-fields" style="margin-top:8px">
              ${numField('max_model_calls', 'Max model calls (thinking turns)', 1)}${numField('max_tool_calls', 'Max tool calls per run', 1)}
              ${numField('max_calls_per_tool', 'Max calls of one tool', 1)}${numField('max_subagent_calls', 'Max subagent delegations', 1)}</div></div>
          <div class="harness-section"><b>Reliability</b><small class="harness-hint">What happens when the model or a data source is slow or fails.</small>
            <div class="harness-fields" style="margin-top:8px">
              ${numField('model_timeout_seconds', 'Model timeout (seconds)', 5)}${numField('model_retries', 'Model retries', 1)}${numField('tool_retries', 'Tool retries', 1)}</div></div>
          <div class="harness-section"><b>Subagents</b>${hint('subagents')}<div class="harness-options">${checks('subagents', o.subagents, HARNESS_LABELS)}</div></div>
          <div class="harness-section"><b>Allowed tools</b>${hint('tools')}<div class="harness-options">${checks('tools', o.tools)}</div></div>
          <div class="harness-section"><b>Rules</b><div class="harness-options">
            ${option('require_plan', 'require_plan', 'Plan first (todo list)', h.require_plan)}${option('require_citations', 'require_citations', 'Cite evidence for every claim', h.require_citations)}</div></div>
          <p class="note" style="margin:10px 0 0">Defaults: temperature 0 · 1,500 tokens · 60 steps · 15 model calls · 20 tool calls · 6 per tool · 4 delegations · 120 s timeout · 1 model / 1 tool retry · full report · all subagents and tools · plan and citations on.</p>
          <div class="row" style="margin:12px 0 0">${manager ? '<button type="submit">Save harness</button><button type="button" class="ghost" id="harness-reset">Reset to defaults</button>' : '<span class="note">Only a manager can change the harness.</span>'}
            <span class="note">All tools stay read-only; changes are audited.</span></div></form>`;
      const read = () => {
        const f = $('#form-harness');
        const list = (n) => $$(`input[name="${n}"]:checked`, f).map((i) => i.value);
        return { ...Object.fromEntries(NUMBERS.map((n) => [n, Number(f[n].value)])), report_style: f.report_style.value,
          subagents: list('subagents'), tools: list('tools'), require_plan: f.require_plan.checked, require_citations: f.require_citations.checked };
      };
      renderHarnessGuide(v);
      $('#form-harness').addEventListener('submit', (e) => { e.preventDefault(); busy(e.submitter, async () => { await api('/api/v1/deep-agents/harness', { method: 'PUT', body: read() }); toast('Harness saved — the next research run uses it'); loadHarness(); }); });
      $('#harness-reset')?.addEventListener('click', (e) => busy(e.currentTarget, async () => { await api('/api/v1/deep-agents/harness', { method: 'PUT', body: v.defaults }); toast('Harness reset to defaults'); loadHarness(); }));
    } catch (e) { box.innerHTML = `<div class="empty">${esc(e.message)}</div>`; }
  }
  $('#form-research').addEventListener('submit', (e) => {
    e.preventDefault();
    $('#research-out').innerHTML = '<p class="note"><span class="spinner"></span>Planning, delegating to subagents and calling tools — 1–2 minutes on a 7B model.</p>';
    busy($('button', e.target), async () => {
      const r = await api('/api/v1/deep-agents/supplier-research', { body: formData(e.target) });
      const todos = (r.todos || []).map((t) => `<li>${chip(t.status)} ${esc(t.content)}</li>`).join('');
      $('#research-out').innerHTML = `<p class="note">${esc(r.runtime)} · ${r.elapsed_seconds}s · ${r.tools_used.length} tool calls · subagents: ${esc(r.subagents_used.join(', ') || 'none')} · harness: ${r.harness ? `${r.harness.report_style}, ${r.harness.max_steps} steps, ${r.harness.subagents.length} subagents, T=${r.harness.temperature}` : 'default'}</p>${todos ? `<div class="panel"><b>Plan</b><ul>${todos}</ul></div>` : ''}<div class="panel">${md(r.report)}</div>`;
    });
  });

  // ================================================================ PLATFORM
  async function loadPlatform() {
    try {
      const st = await api('/api/v1/status');
      $('#runtime').textContent = `cloud: ${st.cloud} · graphs: ${st.graph_runtime}`;
      $('#status').innerHTML = `<div class="status-grid">${Object.entries(st.components).map(([name, c]) => `<div class="status-item"><b>${esc(name.replaceAll('_', ' '))}</b>${badge(c.status)} <div class="note" style="margin:4px 0 0">${esc(c.model || (c.backend ? `${c.backend} · ${c.chunks} chunks` : c.dialect ? `${c.dialect} · audit chain ${c.audit_chain_valid ? 'valid' : 'BROKEN'}` : c.http ? `HTTP ${c.http}` : c.snapshot || c.forecast || ''))}</div></div>`).join('')}</div>`;
    } catch (e) { toast(e.message); }
    const L = state.cfg.links || {};
    const a = (u, t) => (u ? `<a href="${esc(u)}" target="_blank" rel="noopener">${esc(t)}</a>` : `<span class="note">${esc(t)} (not provisioned)</span>`);
    const studio = (g) => `${L.langsmith_studio}&assistantId=${g}`;
    const fw = state.cfg.flowise || {};
    $('#backends').innerHTML = table([['Runtime', (r) => `<b>${esc(r[0])}</b>`], ['Chat flow', (r) => r[1]], ['Agent flow', (r) => r[2]], ['Access', (r) => r[3]]], [
      ['Flowise', a(fw.chatflow_canvas, 'Chatflow canvas'), a(fw.agentflow_canvas, 'AgentFlow V2 canvas'), `${a(L.flowise, 'Flowise UI')}`],
      ['LangGraph', a(L.langsmith_studio && studio('supply_chain_chat'), 'supply_chain_chat'), a(L.langsmith_studio && studio('supply_chain_agentflow'), 'supply_chain_agentflow'), `${a(L.langsmith_studio, 'LangSmith Studio')}`],
    ]);
    const items = [['API docs (Swagger)', state.cfg.api_docs], ['Flowise', L.flowise], ['LangSmith Studio', L.langsmith_studio], ['LangGraph Server', L.langgraph_api], ['MCP server', L.mcp], ['Grafana', L.grafana], ['Langfuse', L.langfuse]];
    $('#links').innerHTML = items.filter((i) => i[1]).map(([t, u]) => `<li><a href="${esc(u)}" target="_blank" rel="noopener">${esc(t)}</a> <span class="note">${esc(u)}</span></li>`).join('');
  }

  // ================================================================ ERP / SAP SETUP
  const ERP_STATUS = { pass: 'good', warn: 'warning', fail: 'critical', 'n/a': 'info', connected: 'good', error: 'critical', disconnected: 'warning', not_configured: 'info',
    validated: 'good', activated: 'good', failed: 'critical', running: 'info', draft: 'info', tested: 'good', active: 'good', inactive: 'info' };
  const erpBadge = (s, label) => pill(ERP_STATUS[s] || 'info', label ?? String(s).replaceAll('_', ' '));
  const erpWhen = (iso) => (iso ? esc(iso.slice(0, 16).replace('T', ' ')) : '—');
  state.erp = { sel: '' };
  async function loadErp() {
    try {
      state.erp.opts = state.erp.opts || await api('/api/v1/erp/providers');
      state.erp.data = await api('/api/v1/erp/connections');
    } catch (e) { $('#erp-config').innerHTML = `<div class="empty">${esc(e.message)}</div>`; return; }
    const d = state.erp.data;
    if (state.erp.sel !== 'new' && !d.connections.some((c) => c.id === state.erp.sel)) state.erp.sel = d.active?.connection_id || d.connections[0]?.id || 'new';
    const conn = d.connections.find((c) => c.id === state.erp.sel) || null;
    const active = d.connections.find((c) => c.id === d.active?.connection_id);
    $('#erp-top').innerHTML = `<div class="row">${chip(`customer: ${state.snapshot?.tenant?.customer || d.tenant}`)}${chip(`active snapshot: ${d.snapshot}`)}
      ${active ? erpBadge('active', `active connection: ${active.name}`) : chip('active: built-in snapshot (no ERP activation yet)')}</div>
      <div class="pills" style="margin-top:10px">${d.connections.map((c) => `<button class="pill ${c.id === state.erp.sel ? 'on' : ''}" data-erp="${c.id}">${esc(c.name)} · ${esc(c.status)}</button>`).join('')}
      ${state.role === 'manager' ? `<button class="pill ${state.erp.sel === 'new' ? 'on' : ''}" data-erp="new">+ New connection</button>` : ''}</div>`;
    $$('[data-erp]').forEach((b) => b.addEventListener('click', () => { state.erp.sel = b.dataset.erp; loadErp(); }));
    erpConfig(conn);
    if (!conn) { ['#erp-health', '#erp-mapping', '#erp-sync'].forEach((s) => { $(s).innerHTML = '<p class="note">Save a connection first.</p>'; }); }
    else { erpHealth(conn); erpMapping(conn); erpSync(conn); }
    erpComponents();
    erpExec();
  }
  const erpPath = (conn, p = '') => `/api/v1/erp/connections/${encodeURIComponent(conn.id)}${p}`;

  function erpConfig(conn) {
    const o = state.erp.opts, c = conn?.config || { environment: 'development', mode: 'mock', protocol: 'snapshot', auth: 'none', timeout_seconds: 15, verify_tls: true, sync_mode: 'manual', sync_interval_minutes: 1440, secret_ref: '' };
    const manager = state.role === 'manager', dis = manager ? '' : 'disabled';
    const provider = conn?.provider || 'mock_sap';
    const sel = (name, map, cur, avail = () => true, label = (k, v) => v.label || k) => `<select name="${name}" ${dis}>${Object.entries(map).map(([k, v]) => `<option value="${k}" ${k === cur ? 'selected' : ''} ${avail(k, v) ? '' : 'disabled'}>${esc(label(k, v))}${avail(k, v) ? '' : ' — not available'}</option>`).join('')}</select>`;
    const list = (arr) => Object.fromEntries(arr.map((x) => [x, { label: x.replaceAll('_', ' ') }]));
    const envRef = (c.secret_ref || '').startsWith('env:') ? c.secret_ref.slice(4) : '';
    $('#erp-config').innerHTML = `<h2>A · ERP connection configuration</h2><p class="sub">${conn ? `${esc(conn.id)} · version ${conn.version} · ${erpBadge(conn.status)}` : 'new connection'}</p>
      <form id="form-erp" class="harness"><div class="harness-fields">
        <label>ERP provider${sel('provider', o.providers, provider, (k, v) => v.available)}</label>
        <label>Connection name<input name="name" value="${esc(conn?.name || '')}" placeholder="Aurelia S/4HANA QA" required ${dis}></label>
        <label>Tenant / customer<input value="${esc(state.erp.data.tenant)}" disabled><small class="harness-hint">The customer chosen at the top; a connection belongs to one customer.</small></label>
        <label>Environment${sel('environment', list(o.environments), c.environment)}</label>
        <label data-live>SAP base URL<input name="base_url" value="${esc(c.base_url || '')}" placeholder="https://my000000-api.s4hana.cloud.sap" ${dis}></label>
        <label data-live>SAP client<input name="sap_client" value="${esc(c.sap_client || '')}" placeholder="100" maxlength="3" ${dis}></label>
        <label data-live>Authentication${sel('auth', list(o.auth), c.auth, (k) => k !== 'none')}</label>
        <label data-auth="basic">User<input name="username" value="${esc(c.username || '')}" autocomplete="off" ${dis}></label>
        <label data-auth="oauth2_client_credentials">Client ID<input name="client_id" value="${esc(c.client_id || '')}" autocomplete="off" ${dis}></label>
        <label data-auth="oauth2_client_credentials">Token URL<input name="token_url" value="${esc(c.token_url || '')}" ${dis}></label>
        <label data-live>Secret reference<select name="secret_kind" ${dis}><option value="env" ${envRef ? 'selected' : ''}>Secrets manager (environment variable)</option><option value="stored" ${c.secret_ref === 'stored' ? 'selected' : ''}>Stored on the server (not for production)</option></select></label>
        <label data-secret="env">Variable name<input name="secret_env" value="${esc(envRef)}" placeholder="SAP_PROD_CLIENT_SECRET" ${dis}><small class="harness-hint">${conn?.secret_source?.startsWith('env:') ? (conn.secret_set ? 'variable present on the server' : 'variable NOT set on the server') : ''}</small></label>
        <label data-secret="stored"><span>Secret</span><input name="secret" type="password" autocomplete="new-password" placeholder="${conn?.secret_set && conn.secret_source === 'stored' ? 'stored — leave empty to keep' : 'not set'}" ${dis}></label>
        <label>API protocol${sel('protocol', list(['snapshot', 'odata_v2', 'odata_v4', 'rest']), c.protocol)}</label>
        <label>Connection mode${sel('mode', o.modes, c.mode, (k, v) => v.available)}<small class="harness-hint">${esc(o.modes.approved_write.description)}</small></label>
        <label data-live>Timeout (seconds)<input name="timeout_seconds" type="number" min="3" max="60" value="${c.timeout_seconds}" ${dis}></label>
        <label data-live class="inline check"><input type="checkbox" name="verify_tls" ${c.verify_tls ? 'checked' : ''} ${dis}>TLS certificate verification</label>
        <label>Synchronization${sel('sync_mode', { manual: { label: 'Manual' }, scheduled: { label: 'Scheduled' }, event: { label: 'Event-driven (needs SAP Event Mesh)' } }, c.sync_mode, (k) => o.sync_modes[k])}</label>
        <label>Sync interval (minutes)<input name="sync_interval_minutes" type="number" min="15" max="10080" value="${c.sync_interval_minutes}" ${dis}></label>
      </div>
      <div class="row" style="margin:12px 0 0">${manager ? `<button type="submit">Save configuration</button>${conn ? `<button type="button" class="ghost" data-act="test">Test connection</button>
        <button type="button" class="ghost" data-act="discover">Discover entities</button><button type="button" class="ghost" data-act="preview">Preview data</button>
        <button type="button" data-act="activate">Activate connection</button>` : ''}` : '<span class="note">Only a manager can change ERP connections.</span>'}
        ${conn ? '<button type="button" class="ghost" data-act="logs">View logs</button>' : ''}
        ${manager && !conn ? `<button type="button" class="ghost" id="erp-emu">Fill SAP emulator (dev)</button>` : ''}</div></form><div id="erp-config-out"></div>`;
    const f = $('#form-erp');
    const sync = () => {
      const live = f.provider.value !== 'mock_sap';
      $$('[data-live]', f).forEach((el) => { el.hidden = !live; });
      $$('[data-auth]', f).forEach((el) => { el.hidden = !live || el.dataset.auth !== f.auth.value; });
      $$('[data-secret]', f).forEach((el) => { el.hidden = !live || el.dataset.secret !== f.secret_kind.value; });
      if (f.environment.value === 'production') { f.verify_tls.checked = true; f.verify_tls.disabled = true; } else if (manager) f.verify_tls.disabled = false;
      if (!live) { f.mode.value = 'mock'; f.protocol.value = 'snapshot'; } else if (f.mode.value === 'mock') { f.mode.value = 'read_only_live'; f.protocol.value = 'odata_v2'; if (f.auth.value === 'none') f.auth.value = 'basic'; }
    };
    ['provider', 'auth', 'secret_kind', 'environment'].forEach((n) => f[n].addEventListener('change', sync)); sync();
    $('#erp-emu')?.addEventListener('click', () => {
      f.provider.value = 'sap_s4hana'; sync();
      f.name.value = 'S/4HANA emulator (dev)'; f.base_url.value = 'http://localhost:8000/erp-emulator';  // called by the API server itself f.sap_client.value = '100'; f.auth.value = 'basic';
      f.username.value = 'SPARC_COMM'; f.secret_kind.value = 'stored'; sync();
      toast('Emulator preset: enter its password (ERP_EMULATOR_PASSWORD), then save');
    });
    f.addEventListener('submit', (e) => {
      e.preventDefault();
      const live = f.provider.value !== 'mock_sap';
      const body = { name: f.name.value.trim(), provider: f.provider.value, environment: f.environment.value, mode: f.mode.value, protocol: f.protocol.value,
        sync_mode: f.sync_mode.value, sync_interval_minutes: Number(f.sync_interval_minutes.value) };
      if (live) Object.assign(body, { base_url: f.base_url.value.trim(), sap_client: f.sap_client.value.trim(), auth: f.auth.value, username: f.username.value.trim(),
        client_id: f.client_id.value.trim(), token_url: f.token_url.value.trim(), timeout_seconds: Number(f.timeout_seconds.value), verify_tls: f.verify_tls.checked,
        secret_ref: f.secret_kind.value === 'env' ? `env:${f.secret_env.value.trim()}` : 'stored' });
      if (live && f.secret_kind.value === 'stored' && f.secret.value) body.secret = f.secret.value;
      if (!live) Object.assign(body, { auth: 'none', base_url: '', secret_ref: '' });
      busy(e.submitter, async () => {
        const saved = conn ? await api(erpPath(conn), { method: 'PATCH', body }) : await api('/api/v1/erp/connections', { body });
        state.erp.sel = saved.id; toast(conn ? `Saved as version ${saved.version} — test it again before activating` : 'Connection created'); loadErp();
      });
    });
    const out = $('#erp-config-out');
    $$('[data-act]', f).forEach((b) => b.addEventListener('click', () => busy(b, async () => {
      const act = b.dataset.act;
      if (act === 'test') { const r = await api(erpPath(conn, '/test'), { method: 'POST' }); out.innerHTML = erpTestHtml(r); toast(r.ok ? 'Connection test passed (not activated)' : 'Connection test failed'); erpHealth({ ...conn }); }
      if (act === 'discover') out.innerHTML = erpDiscoverHtml(await api(erpPath(conn, '/entities')));
      if (act === 'preview') $('#erp-preview-section')?.scrollIntoView({ behavior: 'smooth' });
      if (act === 'activate') {
        if (!confirm(`Activate "${conn.name}" for ${state.erp.data.tenant}? Every business service, Flowise and LangGraph tool will use its snapshot from the next call.`)) return;
        const r = await api(erpPath(conn, '/activate'), { method: 'POST', body: {} }); toast(`Active snapshot: ${r.snapshot_id}`); loadErp();
      }
      if (act === 'logs') {
        const r = await api(erpPath(conn, '/logs'));
        modal(`Logs · ${conn.name}`, table([['When', (x) => erpWhen(x.ts)], ['Action', (x) => esc(x.action.replace('erp.', ''))], ['By', (x) => esc(x.actor)],
          ['Details', (x) => `<code>${esc(JSON.stringify(Object.fromEntries(Object.entries(x.details).filter(([k]) => !['tenant', 'connection_id'].includes(k)))).slice(0, 220))}</code>`]], r.events));
      }
    })));
  }
  const erpTestHtml = (r) => `<div class="panel"><p>${r.ok ? erpBadge('connected', 'connection test passed') : erpBadge('error', 'connection test failed')} ${chip(`auth: ${r.auth}`)} ${r.latency_ms != null ? chip(`${r.latency_ms} ms`) : ''} <span class="note">${esc(r.note || '')}</span></p>
    ${r.error ? `<p class="note">${esc(r.error)}</p>` : ''}${r.checks?.length ? table([['Service / entity', (x) => esc(x.entity)], ['Status', (x) => erpBadge(x.status === 'up' ? 'pass' : 'fail', x.status)], ['Detail', (x) => esc(x.detail)], ['ms', (x) => num(x.ms), 'num']], r.checks) : ''}</div>`;
  const erpDiscoverHtml = (r) => `<div class="panel"><b>Discovered entities</b>${r.provider === 'mock_sap'
    ? table([['SAP business data', (x) => esc(x.label)], ['Entity set', (x) => `<code>${esc(x.entity_set)}</code>`], ['Available', (x) => erpBadge(x.available ? 'pass' : 'n/a', x.available ? 'yes' : 'no')], ['Rows', (x) => num(x.rows), 'num']], r.entities)
    : table([['Service', (x) => `<code>${esc(x.service)}</code>`], ['Entity sets', (x) => (x.error ? `<span class="note">${esc(x.error)}</span>` : esc(x.entity_sets.join(', ')))]], r.entities)}</div>`;

  async function erpHealth(conn) {
    const box = $('#erp-health');
    try {
      const h = await api(erpPath(conn, '/health'));
      const kv = [['Status', erpBadge(h.status)], ['Provider · environment', `${esc(state.erp.opts.providers[h.provider]?.label || h.provider)} · ${esc(h.environment)} · ${esc(h.mode.replaceAll('_', ' '))}`],
        ['Active for this customer', h.active ? erpBadge('active', 'yes') : 'no'], ['SAP system', esc(h.system ? `${h.system.id}${h.system.client ? ` · client ${h.system.client}` : ''}${h.system.snapshot ? ` · ${h.system.snapshot}` : ''}` : '—')],
        ['Last connection test', `${erpWhen(h.last_test_at)} ${h.last_test_ok == null ? '' : h.last_test_ok ? '✓' : '✗'}`], ['Last successful sync', erpWhen(h.last_sync_at)], ['Authentication', esc(h.auth || '—')],
        ['API latency', h.latency_ms != null ? `${num(h.latency_ms)} ms` : '—'], ['Last error', esc(h.last_error || '—')], ['Mapped entities', num(h.mapped_entities)], ['Records synchronized', num(h.records_synced)],
        ['Snapshot in use', `${esc(h.tenant_snapshot.id)} · ${esc(h.tenant_snapshot.source_system || '')} · ${num(h.tenant_snapshot.age_hours, 0)} h old`]];
      box.innerHTML = `<h2>B · SAP connection health</h2><p class="sub">${esc(conn.name)}</p><dl class="kv">${kv.map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join('')}</dl>
        ${state.role === 'manager' ? '<button type="button" id="erp-health-test">Test connection</button>' : ''}<div id="erp-health-out"></div>`;
      $('#erp-health-test')?.addEventListener('click', (e) => busy(e.currentTarget, async () => { const r = await api(erpPath(conn, '/test'), { method: 'POST' }); erpHealth(conn); setTimeout(() => { $('#erp-health-out').innerHTML = erpTestHtml(r); }, 300); }));
    } catch (e) { box.innerHTML = `<div class="empty">${esc(e.message)}</div>`; }
  }

  async function erpMapping(conn) {
    const box = $('#erp-mapping'), o = state.erp.opts, manager = state.role === 'manager', dis = manager ? '' : 'disabled';
    if (conn.provider === 'mock_sap') {
      box.innerHTML = `<h2>C · SAP entity mapping</h2><p class="note">The Mock SAP snapshot is already in SPARC's data model: no mapping needed. Use <b>Discover entities</b> to list what it contains, then <b>Validate</b>.</p>
        ${manager ? '<div class="row"><button type="button" id="erp-mock-validate">Validate</button></div><div id="erp-map-out"></div>' : ''}`;
      $('#erp-mock-validate')?.addEventListener('click', (e) => busy(e.currentTarget, async () => { const r = await api(erpPath(conn, '/validate'), { method: 'POST' }); $('#erp-map-out').innerHTML = erpProblems(r); loadErp(); }));
      return;
    }
    const { mapping } = await api(erpPath(conn, '/mappings'));
    const rows = Object.entries(o.sections).map(([key, spec]) => ({ key, spec, m: mapping[key] || { enabled: false, service: '', entity_set: '', expand: '', filter: '', fields: {} } }));
    const fieldsText = (r) => [...r.spec.required, ...r.spec.optional].map((fld) => `${fld} = ${r.m.fields[fld] || ''}`).join('\n');
    box.innerHTML = `<h2>C · SAP entity mapping</h2><p class="note">Per SPARC data set: the OData entity to read and how each SPARC field is built — <code>Property</code>, <code>nav/Property</code> (with <code>$expand</code>), <code>const:value</code> or <code>map:Property|A=x,B=y,*=z</code>. Required fields first. Data sets not used are carried over from the current snapshot. ${conn.mapping_valid == null ? chip('not validated') : conn.mapping_valid ? erpBadge('pass', 'mapping valid') : erpBadge('fail', 'mapping has errors')}</p>
      <div class="scroll"><table class="erp-map"><thead><tr><th>SAP business data → SPARC usage</th><th>Use</th><th>Service · entity set · $expand · $filter</th><th>Fields (SPARC = SAP)</th></tr></thead><tbody>
      ${rows.map((r) => `<tr data-sec="${r.key}"><td><b>${esc(r.spec.label)}</b><div class="note">${esc(r.spec.usage)}</div><div class="note">required: ${esc(r.spec.required.join(', '))}</div></td>
        <td><input type="checkbox" data-f="enabled" ${r.m.enabled ? 'checked' : ''} ${dis}></td>
        <td><input data-f="service" value="${esc(r.m.service)}" placeholder="/sap/opu/odata/sap/…" ${dis}><input data-f="entity_set" value="${esc(r.m.entity_set)}" placeholder="entity set" ${dis}>
          <input data-f="expand" value="${esc(r.m.expand)}" placeholder="$expand" ${dis}><input data-f="filter" value="${esc(r.m.filter)}" placeholder="$filter" ${dis}></td>
        <td><textarea data-f="fields" rows="${r.spec.required.length + r.spec.optional.length}" ${dis}>${esc(fieldsText(r))}</textarea></td></tr>`).join('')}
      <tr><td><b>Business outcomes</b><div class="note">Verified decision results</div></td><td>—</td><td colspan="2" class="note">Not read from SAP: SPARC's outcome ledger, reconciled against SAP goods receipts.</td></tr>
      </tbody></table></div>
      ${manager ? '<div class="row" style="margin-top:10px"><button type="button" id="erp-map-save">Save mapping</button><button type="button" class="ghost" id="erp-map-validate">Validate mapping</button><button type="button" class="ghost" id="erp-map-discover">Discover entities</button></div>' : ''}
      <div id="erp-map-out"></div>`;
    const read = () => Object.fromEntries($$('tr[data-sec]', box).map((tr) => {
      const v = (n) => $(`[data-f="${n}"]`, tr);
      const fields = Object.fromEntries(v('fields').value.split('\n').map((line) => line.split('=').map((s) => s.trim())).filter(([k]) => k)
        .map(([k, ...rest]) => [k, rest.join('=').trim()]).filter(([, val]) => val));
      return [tr.dataset.sec, { enabled: v('enabled').checked, service: v('service').value.trim(), entity_set: v('entity_set').value.trim(), expand: v('expand').value.trim(), filter: v('filter').value.trim(), fields }];
    }));
    $('#erp-map-save')?.addEventListener('click', (e) => busy(e.currentTarget, async () => { const r = await api(erpPath(conn, '/mappings'), { method: 'PUT', body: { mapping: read() } }); $('#erp-map-out').innerHTML = erpProblems({ valid: !r.problems.length, problems: r.problems }, 'Saved. Offline checks: '); toast('Mapping saved — validate it against SAP'); }));
    $('#erp-map-validate')?.addEventListener('click', (e) => busy(e.currentTarget, async () => { const r = await api(erpPath(conn, '/validate'), { method: 'POST' }); $('#erp-map-out').innerHTML = erpProblems(r); state.erp.data.connections.find((x) => x.id === conn.id).mapping_valid = r.valid; }));
    $('#erp-map-discover')?.addEventListener('click', (e) => busy(e.currentTarget, async () => { $('#erp-map-out').innerHTML = erpDiscoverHtml(await api(erpPath(conn, '/entities'))); }));
  }
  const erpProblems = (r, prefix = '') => `<div class="panel">${prefix}${r.valid ? erpBadge('pass', 'mapping valid against the ERP metadata') : erpBadge('fail', `${r.problems.length} problem(s) — activation is blocked`)}${r.problems.length ? `<ul>${r.problems.map((p) => `<li>${esc(p)}</li>`).join('')}</ul>` : ''}</div>`;

  async function erpSync(conn) {
    const box = $('#erp-sync'), manager = state.role === 'manager';
    const [{ jobs }, { history }] = await Promise.all([api(erpPath(conn, '/sync-history')), api('/api/v1/erp/activation-history')]);
    const total = (j) => Object.values(j.counts || {}).reduce((a, b) => a + b, 0);
    box.innerHTML = `<h2>D · Synchronization &amp; data preview</h2><p class="note">A sync reads the ERP into a <b>staged</b> snapshot, then validates it (master-data references, required data, and the business engine computing on it). It never replaces the active snapshot: a manager activates a validated sync. Full sync only (incremental sync is not supported yet).</p>
      ${manager ? `<div class="row"><button type="button" id="erp-run-sync">Run sync now</button><button type="button" class="ghost" id="erp-rollback">Roll back to previous snapshot</button></div>` : ''}
      ${table([['Sync job', (j) => `<code>${esc(j.id)}</code>${j.retry_of ? `<div class="note">retry of ${esc(j.retry_of)}</div>` : ''}`], ['Status', (j) => erpBadge(j.status)], ['Started', (j) => erpWhen(j.started_at)], ['Records', (j) => num(total(j)), 'num'],
        ['Errors / warnings', (j) => (j.errors.length || j.warnings.length ? `<details><summary>${j.errors.length} errors · ${j.warnings.length} warnings</summary><ul class="note">${[...j.errors, ...j.warnings].slice(0, 30).map((x) => `<li>${esc(x)}</li>`).join('')}</ul></details>` : '—')],
        ['Snapshot', (j) => esc(j.snapshot_id || '—')], ['', (j) => (!manager ? '' : j.status === 'validated' ? `<button class="small" data-activate="${j.id}">Activate</button>` : j.status === 'failed' ? `<button class="small ghost" data-retry="${j.id}">Retry</button>` : '')]], jobs.slice(0, 10))}
      <h3 id="erp-preview-section" style="margin-top:16px">Preview mapped ERP records</h3>
      <form id="form-erp-preview" class="row"><select name="section">${Object.entries(state.erp.opts.sections).map(([k, s]) => `<option value="${k}">${esc(s.label)}</option>`).join('')}</select>
        <input name="top" type="number" min="1" max="50" value="5" style="width:80px">${manager ? '<button type="submit">Preview</button>' : '<span class="note">Only a manager can read live ERP data.</span>'}</form><div id="erp-preview-out"></div>
      <details class="more"><summary>Activation history (this customer)</summary>${table([['When', (h) => erpWhen(h.at)], ['Action', (h) => esc(h.action)], ['Snapshot', (h) => esc(h.snapshot_id)], ['Previous', (h) => esc(h.previous_snapshot_id || 'built-in')], ['By', (h) => esc(h.actor)]], history)}</details>`;
    $('#erp-run-sync')?.addEventListener('click', (e) => busy(e.currentTarget, async () => { const j = await api(erpPath(conn, '/sync'), { method: 'POST', body: {} }); toast(j.status === 'validated' ? `Sync validated: ${total(j)} records staged (not active)` : `Sync failed: ${j.errors[0] || ''}`); loadErp(); }));
    $('#erp-rollback')?.addEventListener('click', (e) => busy(e.currentTarget, async () => { if (!confirm('Roll back to the snapshot that was active before?')) return; const r = await api(erpPath(conn, '/rollback'), { method: 'POST' }); toast(`Rolled back: ${r.snapshot_id}`); loadErp(); }));
    $$('[data-activate]', box).forEach((b) => b.addEventListener('click', () => busy(b, async () => { if (!confirm('Activate this validated snapshot for the customer?')) return; const r = await api(erpPath(conn, '/activate'), { method: 'POST', body: { sync_job_id: b.dataset.activate } }); toast(`Active snapshot: ${r.snapshot_id}`); loadErp(); })));
    $$('[data-retry]', box).forEach((b) => b.addEventListener('click', () => busy(b, async () => { await api(erpPath(conn, '/sync'), { method: 'POST', body: { retry_of: b.dataset.retry } }); loadErp(); })));
    $('#form-erp-preview').addEventListener('submit', (e) => {
      e.preventDefault();
      busy(e.submitter, async () => {
        const r = await api(erpPath(conn, '/preview'), { body: { section: e.target.section.value, top: Number(e.target.top.value) } });
        const cols = [...new Set(r.rows.flatMap((row) => Object.keys(row)))].slice(0, 12);
        $('#erp-preview-out').innerHTML = `<p class="note">${esc(r.source)} · ${r.rows.length} mapped rows${r.errors.length ? ` · ${r.errors.length} rows rejected` : ''}</p>${table(cols.map((k) => [k, (row) => esc(row[k] ?? '')]), r.rows)}
          ${r.errors.length ? `<ul class="note">${r.errors.map((x) => `<li>${esc(x)}</li>`).join('')}</ul>` : ''}
          <details class="more"><summary>Raw ERP rows</summary><pre class="code-view">${esc(JSON.stringify(r.raw, null, 1).slice(0, 6000))}</pre></details>`;
      });
    });
  }

  async function erpComponents() {
    const box = $('#erp-components'), manager = state.role === 'manager';
    const s = await api('/api/v1/erp/integration-status').catch(() => ({}));
    const render = (chk) => (chk ? `<p class="sub">checked ${erpWhen(chk.checked_at)} on snapshot ${esc(chk.snapshot)}${chk.deep ? ' · with live Flowise and LangGraph runs' : ''} · ${chk.ok ? erpBadge('pass', 'all validated') : erpBadge('warn', 'needs attention')}</p>
      ${table([['Component', (r) => `<b>${esc(r.component)}</b>`], ['Status', (r) => erpBadge(r.status)], ['Result of the check', (r) => esc(r.detail)]], chk.results)}`
      : '<div class="empty">Never validated for this customer. Statuses are only shown after a real check.</div>');
    box.innerHTML = `<h2>E · Component integration status</h2><p class="note">Each check calls the component (or the exact endpoint its tools call) and compares the snapshot it answered from with the active one. Not configured = n/a, never green.</p>
      ${manager ? `<div class="row"><button type="button" id="erp-validate-all">Validate all integrations</button><label class="inline check"><input type="checkbox" id="erp-deep">also run a Flowise Agentflow and a LangGraph question (1–3 min)</label></div>` : ''}
      <div id="erp-components-out">${render(s.last_check)}</div>`;
    $('#erp-validate-all')?.addEventListener('click', (e) => busy(e.currentTarget, async () => { const r = await api('/api/v1/erp/validate-integrations', { body: { deep: $('#erp-deep').checked } }); $('#erp-components-out').innerHTML = render(r); }));
  }

  function erpExec() {
    const m = state.erp.opts.modes;
    $('#erp-exec').innerHTML = `<h2>F · SAP execution &amp; human approval</h2><p class="note">SAP writes are disabled by default. Current execution of accepted recommendations: <b>${esc(state.cfg.sap_execution_mode || 'sandbox')}</b> (SAP mock sandbox outbox, never a production SAP system).</p>
      <div class="grid g3">${Object.entries(m).map(([k, v]) => `<div class="panel"><b>${esc(v.label)}</b> ${v.available ? erpBadge('pass', 'available') : erpBadge('n/a', 'not available')}<p class="note">${esc(v.description)}</p></div>`).join('')}</div>
      <p class="note"><b>Governance sequence (unchanged):</b> AI recommendation → human review → manager approval → authorized ERP execution (sandbox) → audit → outcome reconciliation. Flowise and LangGraph agents hold assistant keys: they can read and propose, never approve or execute; the gateway answers 405 to every SAP write.</p>`;
  }

  // ================================================================ NETWORK MAP
  const TIER_COLOR = { local: 'var(--s3)', regional: 'var(--s1)', international: 'var(--s2)' };
  const cssVar = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  let leafletMap = null;
  async function loadMap() {
    try {
      const m = await api('/api/v1/network/map');
      const ft = m.factory_sourcing;
      const spend = ft.reduce((a, f) => a + f.spend_eur, 0) || 1;
      const within = ft.reduce((a, f) => a + f.spend_eur * f.within_zone_pct, 0) / spend;
      const intl = m.tier_summary.find((t) => t.tier === 'international');
      const local = m.tier_summary.find((t) => t.tier === 'local');
      kpiTiles('#map-kpis', [
        { label: 'Sites', value: m.sites.length, status: 'info', hint: `${m.sites.filter((s) => s.type === 'warehouse').length} DCs · ${m.sites.filter((s) => s.type !== 'warehouse').length} plants` },
        { label: 'Tier-1 suppliers', value: m.suppliers.length, status: 'info', hint: `${m.alternatives.length} qualified/quoted alternatives` },
        { label: 'Spend within production zone', value: Math.round(within * 10) / 10, unit: '%', status: within >= 75 ? 'good' : 'warning', hint: 'local + regional, spend-weighted' },
        { label: 'International: actual time to deliver', value: intl?.avg_learned_time_to_deliver_days, unit: ' d', status: 'warning', hint: `${intl?.suppliers || 0} suppliers` },
        { label: 'Local: actual time to deliver', value: local?.avg_learned_time_to_deliver_days, unit: ' d', status: 'good', hint: `${local?.suppliers || 0} suppliers` },
        { label: 'Tier-2 origins', value: m.origins.length, status: m.origins.some((o) => o.criticality === 'high') ? 'warning' : 'info', hint: 'raw-material origins' },
      ]);
      $('#map-sourcing').innerHTML = table([['Factory', (f) => `<b>${esc(f.plant)}</b> ${esc(f.name)}`], ['Local', (f) => `${num(f.local_pct, 1)}%`, 'num'], ['Regional', (f) => `${num(f.regional_pct, 1)}%`, 'num'],
        ['International', (f) => `${num(f.international_pct, 1)}%`, 'num'], ['Within zone', (f) => `<b>${num(f.within_zone_pct, 1)}%</b>`, 'num']], ft);
      $('#map-learned').innerHTML = table([['Supplier', (s) => esc(s.name)], ['SAP', (s) => `${s.sap_lead_time_days} d`, 'num'], ['Actual', (s) => `<b>${num(s.learned_time_to_deliver_days, 1)} d</b>`, 'num'],
        ['Gap', (s) => (s.learned_vs_sap_days ? pill(s.learned_vs_sap_days > 5 ? 'critical' : 'warning', `+${num(s.learned_vs_sap_days, 1)} d`) : pill('good', 'on promise'))]],
        [...m.suppliers].sort((a, b) => b.learned_vs_sap_days - a.learned_vs_sap_days));
      const ref = m.reference;
      $('#map-reference').innerHTML = ref ? `<h2>Real-world reference</h2><p class="sub">${esc(ref.source)}</p>${ref.figures.map((f) => `<div class="row" style="margin:0 0 6px;align-items:baseline"><b style="font-size:20px">${f.value_pct}%</b><span class="note" style="margin:0">${esc(f.label)}</span></div>`).join('')}
        <p class="note">${esc(ref.caveat)}</p><ul class="note">${ref.patterns.map((p) => `<li>${esc(p)}</li>`).join('')}</ul>` : '<h2>Real-world reference</h2><p class="note">No external reference attached to this customer.</p>';
      $('#map-tiers').innerHTML = table([['Tier', (t) => `<span class="tier-dot" style="background:${TIER_COLOR[t.tier]}"></span><b>${esc(t.tier)}</b>`], ['Suppliers', (t) => num(t.suppliers), 'num'],
        ['Actual time to deliver', (t) => (t.avg_learned_time_to_deliver_days === null ? '—' : `${num(t.avg_learned_time_to_deliver_days, 1)} d`), 'num'], ['Delay vs SAP', (t) => (t.avg_delay_vs_sap_days === null ? '—' : `+${num(t.avg_delay_vs_sap_days, 1)} d`), 'num'],
        ['Average OTIF', (t) => (t.avg_otif_pct === null ? '—' : `${num(t.avg_otif_pct, 1)}%`), 'num'], ['AI focus', (t) => esc({ local: 'reliability, capacity, just-in-time', regional: 'cost vs speed, alternative sourcing', international: 'delay prediction, safety stock, early replenishment' }[t.tier])],
        ['Who', (t) => esc(t.names.join(', ') || '—')]], m.tier_summary);
      drawMap(m);
    } catch (e) { toast(e.message); }
  }
  function drawMap(m) {
    const box = $('#network-map');
    if (!window.L) { box.innerHTML = '<div class="empty">The map library could not load (offline?). All map data is in the tables.</div>'; return; }
    if (leafletMap) { leafletMap.remove(); leafletMap = null; }
    leafletMap = L.map(box, { worldCopyJump: true, scrollWheelZoom: false });
    // OpenStreetMap standard tiles (dark mode inverts them in CSS); light demo usage within the OSM tile policy.
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 12, attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' }).addTo(leafletMap);
    const color = (v) => cssVar(v.replace(/var\((--[^)]+)\)/, '$1')) || v;
    const status = { critical: color('var(--critical)'), warning: color('var(--warning)'), good: color('var(--good)'), info: color('var(--info)'), high: color('var(--critical)'), medium: color('var(--warning)'), low: color('var(--good)') };
    const layers = { sites: L.layerGroup(), suppliers: L.layerGroup(), alternatives: L.layerGroup(), origins: L.layerGroup(), supply: L.layerGroup(), tier2: L.layerGroup(), distribution: L.layerGroup(), lane: L.layerGroup(), shipment: L.layerGroup() };
    const bounds = [];
    const link = (code) => `<a href="#sites/${esc(code)}">Open Warehouse 360 →</a>`;
    m.sites.forEach((s) => {
      const isDc = s.type === 'warehouse';
      const mk = L.circleMarker([s.lat, s.lon], { radius: isDc ? 9 : 11, color: color('var(--surface)'), weight: 2, fillColor: isDc ? color('var(--accent)') : color('var(--ink)'), fillOpacity: 1 });
      mk.bindPopup(`<b>${esc(s.code)} · ${esc(s.name)}</b><br>${esc(s.type.replaceAll('_', ' '))} · ${esc(s.city)}, ${esc(s.country)}<br>Stock €${num(s.stock_value_eur)} · ${s.below_target} position(s) below target${s.manager ? `<br>Manager: ${esc(s.manager.name)} · <a href="mailto:${esc(s.manager.email)}">${esc(s.manager.email)}</a>` : ''}<br>${link(s.code)}`);
      mk.bindTooltip(s.code, { permanent: true, direction: 'top', offset: [0, -8] }).addTo(layers.sites); bounds.push([s.lat, s.lon]);
    });
    m.suppliers.forEach((s) => {
      const c = color(TIER_COLOR[s.worst_tier]);
      L.circleMarker([s.lat, s.lon], { radius: 7, color: status[s.risk_rating] || c, weight: 3, fillColor: c, fillOpacity: 0.95 })
        .bindPopup(`<b>${esc(s.name)}</b><br>${esc(s.manufacturing_site || '')} · ${esc(s.city)}, ${esc(s.country)}<br>Supplies ${esc(s.materials.join(', '))}<br>Tier: ${s.serves.map((x) => `${esc(x.plant)} ${esc(x.tier)}`).join(', ')}<br>
          SAP lead time <b>${s.sap_lead_time_days} d</b> · actual <b>${num(s.learned_time_to_deliver_days, 1)} d</b><br>OTIF ${num(s.otif_pct, 1)}% · risk ${esc(s.risk_rating)}${s.single_source ? ' · single source' : ''}`)
        .addTo(layers.suppliers);
      bounds.push([s.lat, s.lon]);
    });
    m.alternatives.forEach((q) => L.circleMarker([q.lat, q.lon], { radius: 5, color: color(TIER_COLOR.regional), weight: 2, fillOpacity: 0, dashArray: '3' })
      .bindPopup(`<b>${esc(q.supplier)}</b> (alternative)<br>${esc(q.material)} · quoted ${q.quoted_lead_time_days} d · €${q.unit_price_eur}/unit<br>${q.qualified ? 'qualified' : 'not yet qualified'} · ${esc(q.reference || '')}`).addTo(layers.alternatives));
    m.origins.forEach((o) => {
      L.circleMarker([o.lat, o.lon], { radius: 6, color: status[o.criticality], weight: 2, fillColor: color('var(--s2)'), fillOpacity: 0.5 })
        .bindPopup(`<b>${esc(o.ingredient)}</b> · ${esc(o.origin)}<br>feeds ${esc(o.feeds_supplier)} (${esc(o.feeds_material)}, ${o.share_of_material_pct}%)<br>transit ${o.transit_days} ± ${o.transit_variability_days} d · criticality ${esc(o.criticality)}<br>${esc(o.note)}`).addTo(layers.origins);
      bounds.push([o.lat, o.lon]);
    });
    m.flows.forEach((f) => {
      if (!f.from[0] || !f.to[0]) return;
      const style = {
        supply: { color: color(TIER_COLOR[f.tier] || 'var(--s1)'), weight: 2, opacity: 0.75 }, tier2: { color: color('var(--s2)'), weight: 1.5, opacity: 0.6, dashArray: '2 6' },
        distribution: { color: color('var(--muted)'), weight: 1, opacity: 0.45 }, lane: { color: color('var(--accent)'), weight: 1.5, opacity: 0.5, dashArray: '6 6' },
        shipment: { color: status[f.status], weight: 3, opacity: 0.9 } }[f.kind];
      L.polyline([f.from, f.to], style).bindTooltip(esc(f.label), { sticky: true }).addTo(layers[f.kind]);
    });
    const shown = { sites: true, suppliers: true, alternatives: false, origins: true, supply: true, tier2: true, distribution: false, lane: true, shipment: true };
    const labels = { sites: 'Sites', suppliers: 'Suppliers', alternatives: 'Alternatives', origins: 'Ingredient origins', supply: 'Supply flows', tier2: 'Tier-2 flows', distribution: 'Distribution', lane: 'DC lanes', shipment: 'Shipments' };
    Object.entries(layers).forEach(([k, layer]) => { if (shown[k]) layer.addTo(leafletMap); });
    $('#map-layers').innerHTML = Object.keys(layers).map((k) => `<label><input type="checkbox" data-layer="${k}" ${shown[k] ? 'checked' : ''}>${labels[k]}</label>`).join('');
    $$('#map-layers input').forEach((cb) => cb.addEventListener('change', () => (cb.checked ? layers[cb.dataset.layer].addTo(leafletMap) : leafletMap.removeLayer(layers[cb.dataset.layer]))));
    $('#map-legend').innerHTML = [['local supplier', TIER_COLOR.local], ['regional supplier', TIER_COLOR.regional], ['international supplier', TIER_COLOR.international], ['plant', 'var(--ink)'], ['distribution centre', 'var(--accent)']]
      .map(([l, c]) => `<span><i class="dot" style="--c:${c}"></i>${l}</span>`).join('') + '<span class="note" style="margin:0">ring colour = supplier risk · red/amber lines = delayed shipments</span>';
    leafletMap.fitBounds(bounds, { padding: [24, 24] });
  }

  // ================================================================ industry / customer
  function agentNotes() {
    const off = state.tenant && state.tenant !== state.catalogue?.default;
    $$('#page-chat, #page-compare, #page-workflow, #page-research').forEach((page) => {
      let note = page.querySelector('.agent-note');
      if (!note) { note = document.createElement('div'); note.className = 'empty agent-note'; page.prepend(note); }
      note.hidden = !off;
      note.innerHTML = 'AI agents, MCP tools and the RAG knowledge base are connected to the <b>Aurelia Cosmetics</b> demo tenant. Dashboards, maps and analytics follow the customer selected in the top bar.';
    });
  }
  function fillTenantBar() {
    const cat = state.catalogue;
    const tid = state.tenant || cat.default;
    const industry = tid.split('/')[0];
    $('#industry-select').innerHTML = cat.industries.map((i) => `<option value="${esc(i.id)}">${esc(i.label)} (${i.customers.length})</option>`).join('');
    $('#industry-select').value = industry;
    const customers = cat.industries.find((i) => i.id === industry)?.customers || [];
    $('#customer-select').innerHTML = customers.map((c) => `<option value="${esc(c.id)}">${esc(c.name)}${c.synthetic ? ' · demo' : ''}</option>`).join('');
    $('#customer-select').value = tid;
  }
  async function setTenant(id) {
    state.tenant = id; local.set('tenant', id);
    Object.assign(state, { products: null, sites: null, product: '', focus: '', site: '', insights: [], filter: 'all' });
    local.set('focus', ''); local.set('site', '');
    fillTenantBar(); agentNotes();
    try { state.cfg = await api('/api/v1/config/public'); } catch { /* keep */ }
    if (state.key) { await loadSuppliers(); refreshBadges(); }
    envLine();
    route();
  }
  function envLine() {
    const t = state.snapshot?.tenant;
    $('#env-line').textContent = `${t ? `${t.customer} · ${t.industry_label} · ` : ''}${(state.cfg.cloud || 'local').toUpperCase()} · graphs on ${state.cfg.graph_runtime || '—'}${state.cfg.llm_model ? ' · ' + state.cfg.llm_model : ''}`;
  }
  $('#industry-select').addEventListener('change', () => {
    const industry = state.catalogue.industries.find((i) => i.id === $('#industry-select').value);
    setTenant(industry.customers[0].id);
  });
  $('#customer-select').addEventListener('change', () => setTenant($('#customer-select').value));
  $('#product-focus').addEventListener('change', () => { state.focus = $('#product-focus').value; local.set('focus', state.focus); loadDashboard(); });
  $('#site-select').addEventListener('change', () => { state.site = $('#site-select').value; local.set('site', state.site); loadSites(); });

  // ================================================================ boot
  async function boot() {
    try { state.cfg = await api('/api/v1/config/public'); } catch { /* optional */ }
    try {
      const fromUrl = new URLSearchParams(location.search).get('tenant');  // shareable link: /?tenant=pharmaceutical/medivia#dashboard
      if (fromUrl) { state.tenant = fromUrl; local.set('tenant', fromUrl); }
      state.catalogue = await api('/api/v1/tenants');
      const known = state.catalogue.industries.some((i) => i.customers.some((c) => c.id === state.tenant));
      if (!known) state.tenant = state.catalogue.default;
      fillTenantBar(); agentNotes();
    } catch { $('#tenant-bar').hidden = true; }
    envLine();
    if (state.cfg.demo_auto_login) {
      let keys = null;
      for (let i = 0; i < 5 && !keys; i++) {  // the API may still be starting right after a deploy
        try { keys = await api('/api/v1/demo/session'); } catch (e) { if (i === 4) { toast(`Automatic sign-in failed: ${e.message}`); route(); return; } await new Promise((r) => setTimeout(r, 2000)); }
      }
      $('#login').hidden = true; $('#demo-role').hidden = false;
      // The dropdown lists every business role; each maps to an API permission (director = manager, others = planner).
      state.demoKeys = keys;
      const persona = { executive: 'director', inventory: 'warehouse', sales: 'demand', stocktake: 'warehouse' }[local.get('persona')] || local.get('persona');
      const start = [...$('#role-select').options].some((o) => o.value === persona) ? persona : 'director';
      state.persona = start; $('#role-select').value = start;
      $('#role-select').addEventListener('change', () => { const id = $('#role-select').value; choosePersona(id); if (!location.hash.startsWith('#dashboard')) location.hash = `dashboard/${id}/${state.focus || ''}`; });
      await signIn(keys[ROLE_ACCESS[start] || 'planner'], false);  // not quiet: a failing API is shown, not hidden behind the key box
    } else if (state.key) {
      $('#demo-role').hidden = true;
      await signIn(state.key, true);
    } else { route(); }
  }
  boot();
})();
