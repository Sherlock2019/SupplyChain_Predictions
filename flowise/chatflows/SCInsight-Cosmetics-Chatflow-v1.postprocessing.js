// Flowise > Chatflow configuration > Post Processing (evidence gate). Imported automatically by deploy.py.
    // ---- Chatflow post-processing evidence gate: numbers in the answer must exist in this turn's tool outputs (or the question)
    const raw = String($flow.rawOutput || '')
    const used = Array.isArray($flow.usedTools) ? $flow.usedTools : []
    const evidence = used.map((u) => `${typeof u.toolOutput === 'string' ? u.toolOutput : JSON.stringify(u.toolOutput)} ${JSON.stringify(u.toolInput || {})}`).join(' ') + ' ' + String($flow.input || '')
    const nums = (t) => (String(t).match(/\d[\d,]*(?:\.\d+)?/g) || []).map((x) => Number(x.replace(/,/g, ''))).filter(Number.isFinite)
    const known = new Set(nums(evidence))
    const unsupported = [...new Set(nums(raw).filter((n) => !known.has(n) && !(Number.isInteger(n) && n <= 10)))]
    const calcs = [...new Set((evidence.match(/CALC-[A-Z0-9]{6,}/g) || []))]
    const tools = [...new Set(used.map((u) => u.tool))]
    const docs = [...new Set((evidence.match(/"doc_id":"[A-Z0-9-]+"/g) || []).map((m) => m.split('"')[3]))]
    const footer = `\n\n---\nTools: ${tools.join(', ') || 'none'}${calcs.length ? ' · calculations: ' + calcs.join(', ') : ''}` +
        `${docs.length ? ' · policy documents: ' + docs.join(', ') : ''} · SAP read-only; approvals only by authorised managers in the SCInsight API.`
    if (!unsupported.length) return raw + footer
    const outputs = used.map((u) => String(u.toolOutput || ''))
    const summaries = outputs.filter((o) => o.startsWith('SUMMARY')).map((o) => o.split('\n\nDATA:')[0])
    // specialist answers are already evidence-gated inside their Agentflow: return them verbatim instead of the rephrased text
    const specialists = used.filter((u) => /_specialist$|^ask_sc_agent_manager$/.test(String(u.tool))).map((u) => String(u.toolOutput || '')).filter(Boolean)
    const safe = specialists.length ? specialists : summaries
    return (safe.length ? safe.join('\n\n') : 'The figures could not be verified against the tool results; please ask again or open the calculation in the SCInsight API.') +
        `\n\n(Evidence gate: the narrative answer was withheld because it contained numbers that are not in the tool results: ${unsupported.slice(0, 8).join(', ')}.)` + footer
