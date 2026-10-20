/* Dependency-free SVG charts: bar, diverging, stacked, line. Hover tooltips, legends, table view for every chart.
   Colors come from CSS tokens (validated categorical slots + reserved status palette). */
(() => {
  const NS = 'http://www.w3.org/2000/svg';
  const esc = (v) => String(v ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const STATUS = {
    critical: { color: 'var(--critical)', icon: '▲', label: 'Critical' },
    warning: { color: 'var(--warning)', icon: '◆', label: 'Warning' },
    serious: { color: 'var(--serious)', icon: '◆', label: 'Serious' },
    good: { color: 'var(--good)', icon: '✓', label: 'Good' },
    info: { color: 'var(--info)', icon: 'ℹ', label: 'Info' },
  };
  const SERIES = ['var(--s1)', 'var(--s2)', 'var(--s3)'];
  const fmt = (v, unit = '') => {
    if (v === null || v === undefined || Number.isNaN(v)) return '—';
    const n = Number(v);
    const abs = Math.abs(n);
    const s = abs >= 1e6 ? `${(n / 1e6).toFixed(1)}M` : abs >= 1e4 ? `${(n / 1e3).toFixed(1)}K` : n.toLocaleString(undefined, { maximumFractionDigits: abs < 10 ? 1 : 0 });
    return unit.trim() === '€' ? `€${s}` : `${s}${unit}`;
  };

  // ---- tooltip
  const tip = document.createElement('div');
  tip.className = 'tooltip';
  document.addEventListener('DOMContentLoaded', () => document.body.appendChild(tip));
  function showTip(evt, html) {
    tip.innerHTML = html; tip.classList.add('show');
    const x = Math.min(evt.clientX + 14, window.innerWidth - tip.offsetWidth - 8);
    const y = Math.min(evt.clientY + 14, window.innerHeight - tip.offsetHeight - 8);
    tip.style.left = `${x}px`; tip.style.top = `${y}px`;
  }
  const hideTip = () => tip.classList.remove('show');

  function el(tag, attrs = {}, parent) {
    const node = document.createElementNS(NS, tag);
    for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
    if (parent) parent.appendChild(node);
    return node;
  }
  // Bar with a 4px rounded data-end and a square baseline end.
  function barPath(x0, x1, y, h) {
    const r = Math.min(4, Math.abs(x1 - x0) / 2, h / 2);
    if (x1 >= x0) return `M${x0},${y} H${x1 - r} Q${x1},${y} ${x1},${y + r} V${y + h - r} Q${x1},${y + h} ${x1 - r},${y + h} H${x0} Z`;
    return `M${x0},${y} H${x1 + r} Q${x1},${y} ${x1},${y + r} V${y + h - r} Q${x1},${y + h} ${x1 + r},${y + h} H${x0} Z`;
  }
  const statusBadge = (s) => (STATUS[s] ? `<span class="status" style="--dot:${STATUS[s].color}"><i></i>${STATUS[s].icon} ${STATUS[s].label}</span>` : '');

  function frame(spec, legendItems) {
    const wrap = document.createElement('div');
    wrap.className = 'chart';
    wrap.innerHTML = `<div class="chart-head"><div><h2>${esc(spec.title)}</h2>${spec.subtitle ? `<p class="sub">${esc(spec.subtitle)}</p>` : ''}</div>
      <button class="ghost small" type="button" data-toggle>Table</button></div>` +
      (legendItems?.length ? `<div class="legend">${legendItems.map((l) => `<span><i class="${l.dot ? 'dot' : ''}" style="--c:${l.color}"></i>${esc(l.label)}</span>`).join('')}</div>` : '');
    const plot = document.createElement('div');
    const table = document.createElement('div');
    table.className = 'scroll'; table.hidden = true;
    wrap.append(plot, table);
    wrap.querySelector('[data-toggle]').addEventListener('click', (e) => {
      table.hidden = !table.hidden; plot.hidden = !table.hidden;
      e.target.textContent = table.hidden ? 'Table' : 'Chart';
    });
    return { wrap, plot, table };
  }
  const tableHtml = (cols, rows) => `<table><thead><tr>${cols.map((c) => `<th class="${c[2] || ''}">${esc(c[0])}</th>`).join('')}</tr></thead><tbody>${rows.map((r) => `<tr>${cols.map((c) => `<td class="${c[2] || ''}">${c[1](r)}</td>`).join('')}</tr>`).join('')}</tbody></table>`;

  // ---- horizontal ranked bars (status-colored, optional reference line)
  function bar(spec) {
    const rows = spec.rows || [];
    const statuses = [...new Set(rows.map((r) => r.status).filter((s) => STATUS[s]))];
    const { wrap, plot, table } = frame(spec, statuses.length > 1 ? statuses.map((s) => ({ label: `${STATUS[s].icon} ${STATUS[s].label}`, color: STATUS[s].color, dot: true })) : null);
    if (!rows.length) { plot.innerHTML = '<div class="empty">Nothing to show — all clear.</div>'; return wrap; }
    const W = 640, labelW = 210, valueW = 62, rowH = 30, barH = 16, top = 6;
    const H = top + rows.length * rowH + 22;
    const max = Math.max(spec.reference || 0, ...rows.map((r) => Math.abs(r.value || 0))) || 1;
    const x = (v) => labelW + (Math.max(0, v || 0) / max) * (W - labelW - valueW);
    const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, role: 'img', 'aria-label': spec.title }, plot);
    const grid = el('g', { class: 'grid axis' }, svg);
    [0, 0.25, 0.5, 0.75, 1].forEach((t) => {
      const gx = labelW + t * (W - labelW - valueW);
      el('line', { x1: gx, x2: gx, y1: top, y2: H - 18 }, grid);
      el('text', { x: gx, y: H - 4, 'text-anchor': 'middle' }, grid).textContent = fmt(max * t, spec.unit || '');
    });
    rows.forEach((r, i) => {
      const y = top + i * rowH + (rowH - barH) / 2;
      const color = STATUS[r.status]?.color || SERIES[0];
      el('text', { x: labelW - 8, y: y + barH / 2 + 4, 'text-anchor': 'end', class: 'lbl-ink' }, svg).textContent = r.label.length > 30 ? `${r.label.slice(0, 29)}…` : r.label;
      el('path', { d: barPath(labelW, Math.max(labelW + 1, x(r.value)), y, barH), fill: color, class: 'mark' }, svg);
      el('text', { x: x(r.value) + 6, y: y + barH / 2 + 4, class: 'val' }, svg).textContent = fmt(r.value, spec.unit || '');
      const hit = el('rect', { x: 0, y: y - 6, width: W, height: rowH, class: 'hit' }, svg);
      const html = `<b>${esc(r.label)}</b>${fmt(r.value, spec.unit || '')}${r.status ? ` · ${STATUS[r.status]?.icon || ''} ${STATUS[r.status]?.label || r.status}` : ''}${r.hint ? `<br>${esc(r.hint)}` : ''}`;
      hit.addEventListener('mousemove', (e) => showTip(e, html)); hit.addEventListener('mouseleave', hideTip);
    });
    el('line', { x1: labelW, x2: labelW, y1: top, y2: H - 18, class: 'base' }, svg);
    if (spec.reference) {
      const rx = x(spec.reference);
      el('line', { x1: rx, x2: rx, y1: top - 4, y2: H - 18, class: 'ref' }, svg);
      if (spec.reference_label) el('text', { x: rx + 4, y: top + 6, class: 'lbl' }, svg).textContent = spec.reference_label;
    }
    table.innerHTML = tableHtml([['Item', (r) => esc(r.label)], ['Value', (r) => fmt(r.value, spec.unit || ''), 'num'], ['Status', (r) => statusBadge(r.status)], ['Detail', (r) => esc(r.hint || '')]], rows);
    return wrap;
  }

  // ---- diverging bars around zero (blue = surplus / positive, red = gap / negative)
  function diverging(spec) {
    const rows = spec.rows || [];
    const { wrap, plot, table } = frame(spec, [{ label: 'positive / surplus', color: 'var(--pos)' }, { label: 'negative / gap', color: 'var(--neg)' }]);
    const W = 640, labelW = 130, rowH = 30, barH = 16, top = 6, pad = 104; // pad keeps outside value labels clear of the category labels
    const H = top + rows.length * rowH + 22;
    const max = Math.max(...rows.map((r) => Math.abs(r.value || 0)), 1);
    const mid = labelW + (W - labelW) / 2;
    const half = (W - labelW) / 2 - pad;
    const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, role: 'img', 'aria-label': spec.title }, plot);
    const grid = el('g', { class: 'grid axis' }, svg);
    [-1, -0.5, 0, 0.5, 1].forEach((t) => {
      const gx = mid + t * half;
      el('line', { x1: gx, x2: gx, y1: top, y2: H - 18 }, grid);
      el('text', { x: gx, y: H - 4, 'text-anchor': 'middle' }, grid).textContent = fmt(max * t, spec.unit || '');
    });
    rows.forEach((r, i) => {
      const y = top + i * rowH + (rowH - barH) / 2;
      const end = mid + (r.value / max) * half;
      el('text', { x: labelW - 8, y: y + barH / 2 + 4, 'text-anchor': 'end', class: 'lbl-ink' }, svg).textContent = r.label;
      el('path', { d: barPath(mid, end === mid ? mid + 1 : end, y, barH), fill: r.value >= 0 ? 'var(--pos)' : 'var(--neg)', class: 'mark' }, svg);
      el('text', { x: r.value >= 0 ? end + 6 : end - 6, y: y + barH / 2 + 4, 'text-anchor': r.value >= 0 ? 'start' : 'end', class: 'val' }, svg).textContent = fmt(r.value, spec.unit || '');
      const hit = el('rect', { x: 0, y: y - 6, width: W, height: rowH, class: 'hit' }, svg);
      hit.addEventListener('mousemove', (e) => showTip(e, `<b>${esc(r.label)}</b>${fmt(r.value, spec.unit || '')}`)); hit.addEventListener('mouseleave', hideTip);
    });
    el('line', { x1: mid, x2: mid, y1: top - 2, y2: H - 18, class: 'base' }, svg);
    table.innerHTML = tableHtml([['Item', (r) => esc(r.label)], ['Value', (r) => fmt(r.value, spec.unit || ''), 'num']], rows);
    return wrap;
  }

  // ---- horizontal stacked bars (2px surface gap between segments)
  function stacked(spec) {
    const rows = spec.rows || [];
    const colors = spec.series.map((s, i) => (spec.status_series ? STATUS[s]?.color : SERIES[i]) || SERIES[i % 3]);
    const { wrap, plot, table } = frame(spec, spec.series.map((s, i) => ({ label: spec.status_series ? `${STATUS[s]?.icon || ''} ${s}` : s, color: colors[i] })));
    if (!rows.length) { plot.innerHTML = '<div class="empty">Nothing to show.</div>'; return wrap; }
    const W = 640, labelW = 190, valueW = 56, rowH = 30, barH = 16, top = 6;
    const H = top + rows.length * rowH + 22;
    const totals = rows.map((r) => r.segments.reduce((a, s) => a + (s.value || 0), 0));
    const max = Math.max(...totals, 1);
    const scale = (v) => (v / max) * (W - labelW - valueW);
    const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, role: 'img', 'aria-label': spec.title }, plot);
    const grid = el('g', { class: 'grid axis' }, svg);
    [0, 0.5, 1].forEach((t) => {
      const gx = labelW + t * (W - labelW - valueW);
      el('line', { x1: gx, x2: gx, y1: top, y2: H - 18 }, grid);
      el('text', { x: gx, y: H - 4, 'text-anchor': 'middle' }, grid).textContent = fmt(max * t, spec.unit || '');
    });
    rows.forEach((r, i) => {
      const y = top + i * rowH + (rowH - barH) / 2;
      el('text', { x: labelW - 8, y: y + barH / 2 + 4, 'text-anchor': 'end', class: 'lbl-ink' }, svg).textContent = r.label.length > 28 ? `${r.label.slice(0, 27)}…` : r.label;
      let cursor = labelW;
      const visible = r.segments.filter((s) => s.value > 0);
      visible.forEach((s, j) => {
        const w = scale(s.value);
        const gap = j < visible.length - 1 ? 2 : 0;
        const isLast = j === visible.length - 1;
        const color = colors[spec.series.indexOf(s.name)];
        if (isLast) el('path', { d: barPath(cursor, cursor + Math.max(w, 1), y, barH), fill: color, class: 'mark' }, svg);
        else el('rect', { x: cursor, y, width: Math.max(w - gap, 1), height: barH, fill: color, class: 'mark' }, svg);
        cursor += w;
      });
      el('text', { x: cursor + 6, y: y + barH / 2 + 4, class: 'val' }, svg).textContent = fmt(totals[i], spec.unit || '');
      const hit = el('rect', { x: 0, y: y - 6, width: W, height: rowH, class: 'hit' }, svg);
      const html = `<b>${esc(r.label)}</b>${r.segments.map((s) => `${esc(s.name)}: ${fmt(s.value, spec.unit || '')}`).join('<br>')}`;
      hit.addEventListener('mousemove', (e) => showTip(e, html)); hit.addEventListener('mouseleave', hideTip);
    });
    el('line', { x1: labelW, x2: labelW, y1: top, y2: H - 18, class: 'base' }, svg);
    table.innerHTML = tableHtml([['Item', (r) => esc(r.label)], ...spec.series.map((s) => [s, (r) => fmt(r.segments.find((x) => x.name === s)?.value, spec.unit || ''), 'num'])], rows);
    return wrap;
  }

  // ---- line chart over dates with crosshair tooltip
  function line(spec) {
    const series = spec.series.filter((s) => s.points?.length);
    const colors = series.map((s, i) => s.color || SERIES[i % 3]);
    const { wrap, plot, table } = frame(spec, series.length > 1 ? series.map((s, i) => ({ label: s.name, color: colors[i] })) : null);
    const W = 680, H = 260, L = 48, R = 70, T = 12, B = 26;
    const dates = [...new Set(series.flatMap((s) => s.points.map((p) => p.date)))].sort();
    const idx = Object.fromEntries(dates.map((d, i) => [d, i]));
    const values = series.flatMap((s) => s.points.map((p) => p.value)).concat(spec.references?.map((r) => r.value) || []);
    let lo = Math.min(0, ...values), hi = Math.max(...values, 1);
    hi += (hi - lo) * 0.08;
    const x = (d) => L + (idx[d] / Math.max(dates.length - 1, 1)) * (W - L - R);
    const y = (v) => T + (1 - (v - lo) / (hi - lo)) * (H - T - B);
    const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, role: 'img', 'aria-label': spec.title }, plot);
    const grid = el('g', { class: 'grid axis' }, svg);
    for (let t = 0; t <= 4; t += 1) {
      const v = lo + ((hi - lo) * t) / 4;
      el('line', { x1: L, x2: W - R, y1: y(v), y2: y(v) }, grid);
      el('text', { x: L - 6, y: y(v) + 4, 'text-anchor': 'end' }, grid).textContent = fmt(v);
    }
    const step = Math.ceil(dates.length / 6);
    dates.forEach((d, i) => { if (i % step === 0) el('text', { x: x(d), y: H - 6, 'text-anchor': 'middle', class: 'lbl' }, svg).textContent = d.slice(5); });
    if (lo < 0) el('line', { x1: L, x2: W - R, y1: y(0), y2: y(0), class: 'base' }, svg);
    (spec.references || []).forEach((r) => {
      el('line', { x1: L, x2: W - R, y1: y(r.value), y2: y(r.value), class: 'ref' }, svg);
      el('text', { x: W - R + 4, y: y(r.value) + 4, class: 'lbl' }, svg).textContent = r.label;
    });
    if (spec.today && idx[spec.today] !== undefined) {
      el('line', { x1: x(spec.today), x2: x(spec.today), y1: T, y2: H - B, class: 'ref' }, svg);
      el('text', { x: x(spec.today) + 4, y: T + 10, class: 'lbl' }, svg).textContent = 'today';
    }
    series.forEach((s, i) => {
      const d = s.points.map((p, j) => `${j ? 'L' : 'M'}${x(p.date)},${y(p.value)}`).join(' ');
      el('path', { d, fill: 'none', stroke: colors[i], 'stroke-width': 2, 'stroke-linejoin': 'round', 'stroke-linecap': 'round' }, svg);
      const last = s.points[s.points.length - 1];
      el('circle', { cx: x(last.date), cy: y(last.value), r: 4, fill: colors[i], stroke: 'var(--surface)', 'stroke-width': 2 }, svg);
      // End labels only while they cannot collide; with 3+ series the legend carries identity.
      if (series.length <= 2) el('text', { x: x(last.date) + 7, y: y(last.value) + 4, class: 'lbl' }, svg).textContent = s.label || s.name;
      (s.markers || []).forEach((m) => {
        if (idx[m.date] === undefined) return;
        el('circle', { cx: x(m.date), cy: y(m.value), r: 5, fill: 'var(--critical)', stroke: 'var(--surface)', 'stroke-width': 2 }, svg);
      });
    });
    const cross = el('line', { x1: 0, x2: 0, y1: T, y2: H - B, class: 'base', opacity: 0 }, svg);
    const hit = el('rect', { x: L, y: T, width: W - L - R, height: H - T - B, class: 'hit' }, svg);
    hit.addEventListener('mousemove', (e) => {
      const box = svg.getBoundingClientRect();
      const px = ((e.clientX - box.left) / box.width) * W;
      const i = Math.round(((px - L) / (W - L - R)) * (dates.length - 1));
      const d = dates[Math.max(0, Math.min(dates.length - 1, i))];
      cross.setAttribute('x1', x(d)); cross.setAttribute('x2', x(d)); cross.setAttribute('opacity', 1);
      const lines = series.map((s, k) => { const p = s.points.find((q) => q.date === d); return p ? `<span style="color:${colors[k]}">●</span> ${esc(s.name)}: ${fmt(p.value, spec.unit || '')}` : ''; }).filter(Boolean);
      showTip(e, `<b>${d}</b>${lines.join('<br>')}`);
    });
    hit.addEventListener('mouseleave', () => { hideTip(); cross.setAttribute('opacity', 0); });
    table.innerHTML = tableHtml([['Date', (d) => d], ...series.map((s) => [s.name, (d) => fmt(s.points.find((p) => p.date === d)?.value), 'num'])], dates);
    return wrap;
  }

  window.Charts = { bar, diverging, stacked, line, STATUS, statusBadge, fmt, esc };
})();
