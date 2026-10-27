// Flowise Custom Function '4 · Calculate with SAP data' in SCInsight-Cosmetics-Logistics-Agentflow-v1 (customFunctionAgentflow_1)
// Generated from flowise/scinsight/build-scinsight.cjs (PRELUDE + step function)
    // ---- SCInsight API client (fixed base URL + agent key from Flowise Variables; the model never sees either)
    const fetch = require('node-fetch')
    const BASE = String($vars.sci_api_url || '').replace(/\/+$/, '')
    const KEY = String($vars.sci_agent_key || '')
    const api = async (method, path, payload) => {
        if (!BASE || !KEY) return { ok: false, status: 0, data: { detail: 'Flowise variables sci_api_url and sci_agent_key are not set' } }
        try {
            const res = await fetch(BASE + path, { method, headers: { 'X-API-Key': KEY, 'Content-Type': 'application/json', Accept: 'application/json' },
                body: payload === undefined ? undefined : JSON.stringify(payload) })
            const text = await res.text()
            let data
            try { data = JSON.parse(text) } catch (e) { data = { detail: text.slice(0, 400) } }
            return { ok: res.ok, status: res.status, data }
        } catch (e) {
            return { ok: false, status: 0, data: { detail: 'SCInsight API unreachable: ' + String((e && e.message) || e).slice(0, 200) } }
        }
    }
    // ---- deterministic identifier detection (codes first, then catalog names); same rules as detect_codes() in backend/scinsight/lg/common.py
    function detectCodes(question, catalog) {
        const q = String(question || '').toUpperCase()
        const sec = {}
        for (const line of String(catalog || '').split('\n')) {
            const i = line.indexOf(': ')
            if (i < 0) continue
            sec[line.slice(0, i)] = line.slice(i + 2).split('; ').filter((p) => p.includes(' = ')).map((p) => [p.slice(0, p.indexOf(' = ')), p.slice(p.indexOf(' = ') + 3)])
        }
        const TOKEN = /[A-Z0-9]+(?:-[A-Z0-9]+)+/g
        const inQ = new Set(q.match(TOKEN) || [])
        const words = q.match(/[A-Z0-9][A-Z0-9\/]*/g) || []
        const STOP = new Set(['THE', 'AND', 'FOR', 'WITH', 'SYNTHETIC', 'BASE'])
        const hits = (label) => {
            const tokens = (label.toUpperCase().replace(/\(.*?\)/g, '').match(/[A-Z][A-Z0-9]{2,}/g) || []).filter((t) => !STOP.has(t) && t !== 'ML')
            const n = tokens.filter((t) => words.some((w) => w.startsWith(t))).length
            return tokens.length && n >= Math.min(2, tokens.length) ? n : 0
        }
        const byCode = (s) => ((sec[s] || []).find(([c]) => inQ.has(c)) || [''])[0]
        const best = (s, score) => { let b = [0, '']; for (const [c, l] of sec[s] || []) { const v = Number(score(c, l)); if (v > b[0]) b = [v, c] } return b[1] }
        const esc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
        const product = byCode('PRODUCTS') || best('PRODUCTS', (c, l) => hits(l))
        const material = byCode('MATERIALS') || best('MATERIALS', (c, l) => hits(l))
        const supplier = byCode('SUPPLIERS') || best('SUPPLIERS', (c, l) => new RegExp(`\\bSUPPLIER ${esc(c.split('-').pop())}\\b`).test(q) || words.includes(l.split(' ')[0].toUpperCase()))
        const places = []
        for (const [code, label] of sec['LOCATIONS'] || []) {
            const head = label.split(' (')[0].toUpperCase()
            const names = [code, ...(head.includes(' — ') ? [head.split(' — ')[0]] : head.split(' ').slice(0, 1))]
            const pos = names.filter((n) => new RegExp(`\\b${esc(n)}\\b`).test(q)).map((n) => q.indexOf(n))
            if (pos.length) places.push([Math.min(...pos), code])
        }
        const ordered = places.sort((a, b) => a[0] - b[0]).map((p) => p[1])
        const target = ordered.find((c) => new RegExp(`\\b(TO|INTO|REACH|RESUPPLY|COVER)\\s+(WAREHOUSE ${esc(c.slice(-1))}|${esc(c)})\\b`).test(q)) || ordered.find((c) => c.startsWith('WH-')) || ''
        const clean = q.replace(TOKEN, ' ').replace(/\d{4}-\d{2}-\d{2}/g, ' ')
        const qty = clean.match(/(?<![\w.])(\d{1,3}(?:[ ,]\d{3})+|\d{3,})(?![\w.])/)
        const date = q.match(/\d{4}-\d{2}-\d{2}/)
        const found = { production_order_id: byCode('PRODUCTION ORDERS'), sku: product, material_id: material, supplier_id: supplier,
            item_id: material && byCode('MATERIALS') ? material : (product || material), location: ordered[0] || '', target_warehouse: target,
            quantity: qty ? qty[1].replace(/[ ,]/g, '') : '', need_date: date ? date[0] : '' }
        return Object.fromEntries(Object.entries(found).filter(([, v]) => v))
    }
    const STATE = ($flow && $flow.state) || {}
    const DETECTED = typeof $question === 'undefined' ? {} : detectCodes(String($question), String(STATE.catalog || ''))
    // identifiers extracted by the LLM arrive as JSON text; parsed leniently (a missing or malformed key is simply empty)
    const EXTRACTED = (() => {
        const m = String(typeof $extracted === 'undefined' ? '' : $extracted).match(/\{[\s\S]*?\}/)  // first (flat) object
        if (!m) return {}
        try { const o = JSON.parse(m[0].replace(/:\s*(none|null|n\/a|undefined)\s*(?=[,}\n])/gi, ': ""')); if (o && typeof o === 'object') return o } catch (e) { /* fall through */ }
        const o = {}
        for (const kv of m[0].matchAll(/"([a-z_]+)"\s*:\s*"?([^",}\n]*)"?/gi)) o[kv[1]] = kv[2].trim()
        return o
    })()
    const val = (k) => {
        let v = STATE[k]
        // identifiers: code-detected first, the model's extraction only fills what code could not find
        if ((v === undefined || v === null || v === '') && k.startsWith('p_')) v = DETECTED[k.slice(2)] || EXTRACTED[k.slice(2)]
        if (v === undefined || v === null) return ''
        const s = String(v).trim()
        return /^(none|null|unknown|n\/a|undefined|\{\{.*\}\})$/i.test(s) ? '' : s
    }
    const code = (k) => { const s = val(k).toUpperCase().replace(/\s+/g, ''); return /^[A-Z0-9][A-Z0-9_-]{1,40}$/.test(s) ? s : '' }
    const num = (k) => { const n = Number(val(k).replace(/[, ]/g, '')); return Number.isFinite(n) && n > 0 ? n : null }
    const day = (k) => { const s = val(k); return /^\d{4}-\d{2}-\d{2}$/.test(s) ? s : '' }
    const detail = (r) => { const d = r.data && r.data.detail; return (typeof d === 'string' ? d : JSON.stringify(d || r.data)).slice(0, 400) }
    const strip = (o) => Array.isArray(o) ? o.map(strip) : (o && typeof o === 'object')
        ? Object.fromEntries(Object.entries(o).filter(([k]) => k !== 'source_records').map(([k, v]) => [k, strip(v)])) : o
    // every returned value is a string: Flowise keeps the literal "{{ output.x }}" for missing/null values
    const result = (o) => JSON.stringify(Object.fromEntries(Object.entries(o).map(([k, v]) => [k, v === undefined || v === null ? '' : typeof v === 'string' ? v : JSON.stringify(v)])))

    // ---- deterministic, number-preserving summaries of the calculation results (the explanation model only rephrases these)
    const list = (xs, f) => (xs || []).map(f).join('; ') || 'none'
    const kv = (o) => Object.entries(o || {}).map(([x, y]) => `${x}=${typeof y === 'object' ? JSON.stringify(y) : y}`).join(' ')
    const opt = (o) => `  option ${o.rank}: ${o.option} - quantity ${o.quantity}, lead ${o.lead_days ?? '-'} days${o.lead_time_basis ? ' (' + o.lead_time_basis + (o.contract_lead_days ? ', contract ' + o.contract_lead_days + ' days' : '') + ')' : ''}${o.mode ? ', ' + o.mode : ''}, arrival ${o.arrival_date}, in time: ${o.in_time}, covers need: ${o.covers_need}, cost EUR ${o.cost_eur ?? 'not estimated'}, feasible: ${o.feasible}, recommended: ${!!o.recommended}${(o.reasons || []).length ? ' - ' + o.reasons.join(', ') : ''}${(o.not_transferable || []).length ? '; not transferable: ' + list(o.not_transferable, (e) => `${e.batch_id} ${e.quantity} (${e.reason})`) : ''}`
    const summarize = (d) => {
        const L = []
        const k = d.kind
        if (k === 'material_readiness') {
            L.push(`Production order ${d.production_order_id || '-'}: ${d.sku} x ${d.quantity} at ${d.plant}, materials needed by ${d.need_date} (BOM ${d.bom_version}). Status: ${d.status}.`)
            L.push('Shortages: ' + list(d.shortages, (s) => `${s.material_id} missing ${s.missing} ${s.uom} (needed ${s.required_date})`))
            for (const l of d.lines || []) {
                if (l.status === 'covered' && !(l.excluded_stock || []).length) { L.push(`${l.material_id}: required ${l.required_quantity} ${l.uom}, usable ${l.usable} - covered`); continue }
                L.push(`${l.material_id}: required ${l.required_quantity} ${l.uom}, usable ${l.usable}, missing ${l.missing}; excluded: ${list(l.excluded_stock, (e) => `${e.batch_id} ${e.quantity} (${e.reason})`)}; late POs: ${list(l.late_purchase_orders, (p) => `${p.po_id} ${p.quantity} promised ${p.promised_date}`)}; unconfirmed POs: ${list(l.unconfirmed_purchase_orders, (p) => `${p.po_id} ${p.quantity} promised ${p.promised_date} (${p.status})`)}`)
                for (const o of l.supply_options || []) L.push(opt(o))
            }
            if (d.partial_production_possible !== undefined) L.push(`Partial production possible now: ${d.partial_production_possible}.`)
            L.push('Alternatives: ' + list(d.alternatives, kv))
        } else if (k === 'warehouse_balancing') {
            L.push(`${d.sku} balancing towards ${d.target_warehouse || 'the lowest-cover warehouse'}. Status: ${d.status}.`)
            for (const p of d.positions || []) L.push(`${p.warehouse} (${p.name}): usable ${p.usable}, demand ${p.daily_demand}/day, cover ${p.days_of_cover} days (target ${p.target_cover_days}), projected stock-out ${p.projected_stockout || 'none'}; excluded: ${list(p.excluded_stock, (e) => `${e.batch_id} ${e.quantity} (${e.reason})`)}; near expiry: ${list(p.near_expiry, (e) => `${e.batch_id} ${e.quantity} expires ${e.expiry_date}`)}`)
            for (const o of d.options || []) L.push(opt(o))
        } else if (k === 'replenishment') {
            L.push(`${d.item_id} at ${d.location}: usable ${d.usable}, quantity to replenish ${d.quantity}, need date ${d.need_date}.`)
            for (const o of d.options || []) L.push(opt(o))
        } else if (k === 'quality_check') {
            L.push(`${d.item_id} at ${d.location || 'all locations'}: on hand ${d.on_hand}, usable ${d.usable}.`)
            L.push('Excluded: ' + list(d.excluded, (e) => `${e.batch_id} ${e.quantity} (${e.reason})`))
            L.push('Near expiry: ' + list(d.near_expiry, (e) => `${e.batch_id} ${e.quantity} expires ${e.expiry_date}`))
            L.push('Expiry risks: ' + list(d.expiry_risks, kv))
            L.push('FEFO order of usable batches: ' + list(d.fefo_order, (b) => typeof b === 'object' ? `${b.batch_id} ${b.quantity ?? ''}` : String(b)))
            if (d.note) L.push(d.note)
        } else if (k === 'lead_time_estimate') {
            const e = d.estimate || {}
            L.push(`${d.supplier_id} (${d.supplier}) ${d.material_id || ''}: predicted lead time ${d.predicted_lead_time_days} days (${d.basis}, model ${d.model_version}); receipts ${e.receipts}, mean ${e.estimate_days}, p90 ${e.p90_days}, min ${e.min_days}, max ${e.max_days}, contract ${e.contract_days} days, on-time rate ${e.on_time_rate}.`)
        } else if (k === 'demand_forecast') {
            const b = d.backtest || {}
            L.push(`${d.sku} at ${d.warehouse}: forecast ${d.total} units over ${(d.forecast || []).length} days (${d.method}, ${d.model_version}); back-test over ${b.holdout_days} days: WAPE ${b.wape_pct}% vs naive ${b.naive_same_weekday_wape_pct}%.`)
        }
        L.push('Proposed actions: ' + list(d.proposed_actions, kv))
        const pv = d.provenance || {}
        L.push(`Calculation ${d.calculation_id} (${k}) on SAP snapshot ${pv.snapshot_id} as of ${pv.as_of_date}${pv.synthetic ? ', synthetic data' : ''}.`)
        return L.join('\n')
    }

    const done = (main, extra, message) => result({
        calc_ok: 'yes', calc_id: main.calculation_id, calc_kind: main.kind, snapshot_id: (main.provenance || {}).snapshot_id,
        calc_has_actions: (main.proposed_actions || []).length ? 'yes' : 'no',
        calc_summary: [summarize(main), ...extra.map(summarize), message || ''].filter(Boolean).join('\n\n'),
        calc_evidence: JSON.stringify([main, ...extra].map(strip)), calc_message: '' })
    const fail = (message) => result({ calc_ok: 'no', calc_id: '', calc_kind: '', snapshot_id: val('snapshot_id'), calc_has_actions: 'no', calc_summary: '', calc_evidence: '', calc_message: message })

    const sku = code('p_sku'), target = code('p_target_warehouse')
    if (!sku) return fail('Which product (SKU) should be moved, and to which warehouse?')
    const r = await api('POST', '/api/v1/optimizer/warehouse-balancing', target ? { sku, target_warehouse: target } : { sku })
    if (!r.ok) return fail(`Transport options could not be calculated (HTTP ${r.status}): ${detail(r)}`)
    return done(r.data, [])
