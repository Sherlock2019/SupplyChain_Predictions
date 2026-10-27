// Flowise Custom Function '5 · Policy search (RAG)' in SCInsight-Cosmetics-Warehouse-Agentflow-v1 (customFunctionAgentflow_2)
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

    // ---- governed RAG through the API (tenant-, role- and validity-filtered); flagged chunks never reach the model
    const q = (String($topic || '') + ' ' + String($question || '')).slice(0, 900)
    const r = await api('POST', '/api/v1/rag/search', { query: q, top_k: 3 })
    if (!r.ok) return result({ policy: `Policy search unavailable (HTTP ${r.status}): ${detail(r)}`, citations: '' })
    const all = r.data.results || []
    const hits = all.filter((h) => !(h.flags || []).length)
    return result({
        policy: (hits.map((h) => `[${h.citation.doc_id} v${h.citation.version} section "${h.citation.section}"] ${h.text}`).join('\n') || 'No matching policy excerpt.') +
            (all.length > hits.length ? `\n(${all.length - hits.length} retrieved excerpt(s) withheld: instruction-like text)` : ''),
        citations: hits.map((h) => `${h.citation.doc_id} v${h.citation.version} "${h.citation.section}"`).join('; '),
    })
