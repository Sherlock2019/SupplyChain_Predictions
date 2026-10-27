#!/usr/bin/env node
/*
 * SCInsight Functions & Code Explorer — Flowise Agentflow V2 exports built from code_explorer/registry (via codemap_spec.json).
 * Runs inside the Flowise container (node classes of the installed Flowise, same as flowise/scinsight/build-scinsight.cjs):
 *
 *   docker compose exec -T -w /usr/local/lib/node_modules/flowise flowise node /opt/flows/code_explorer/build-code-map.cjs
 *
 * One flow per code-explorer category + a master flow. Every real function is a Custom Function node whose JavaScript is only a
 * documentation comment + `return` of its id (it never runs Python or calls the backend), and a Sticky Note beside it shows the
 * complete annotated source. Edges are the verified call / HTTP / dependency relations of code_explorer/registry/dependencies.json.
 */
const fs = require('fs')
const { AgentflowBuilder } = require('../build-flows.cjs')

const spec = JSON.parse(fs.readFileSync(__dirname + '/codemap_spec.json', 'utf8'))
const PREFIX = 'SCInsight Code Explorer · '
const MASTER = 'SCInsight — Functions & Code Explorer'
const byId = Object.fromEntries(spec.items.map((i) => [i.id, i]))
const label = (id) => spec.labels[id] || id
const out = {}, inn = {}
for (const e of spec.edges) { (out[e.from] = out[e.from] || []).push(e); (inn[e.to] = inn[e.to] || []).push(e) }
const EDGE_LABEL = { calls: 'calls function', http_request: 'HTTP request', depends_on: 'validates / authorizes (Depends)', validates_input: 'validates input (Pydantic)', references: 'passes reference' }

function docJs(item) {
    const lines = [
        `// ${item.id} · ${item.name}   [${item.kind} · ${item.status}]`,
        '// DOCUMENTATION NODE of the SCInsight code map: this JavaScript never runs Python and never calls the backend.',
        `// Source: ${item.file}${item.lines ? ':' + item.lines : ''}`,
        `// Annotated copy: ${item.annotated}`,
    ]
    if (item.summary) lines.push(`// Summary: ${item.summary}`)
    if (item.routes && item.routes.length) lines.push(`// FastAPI route: ${item.routes.join(', ')}`)
    lines.push('// Called by:', ...((inn[item.id] || []).slice(0, 15).map((e) => `//   <- ${label(e.from)} (${EDGE_LABEL[e.kind] || e.kind})`)), ...(inn[item.id] ? [] : ['//   (none found)']))
    lines.push('// Calls:', ...((out[item.id] || []).slice(0, 20).map((e) => `//   -> ${label(e.to)} (${EDGE_LABEL[e.kind] || e.kind})`)), ...(out[item.id] ? [] : ['//   (none found)']))
    lines.push('// The complete annotated source is in the Sticky Note to the right of this node.')
    lines.push(`return ${JSON.stringify(item.id + ' ' + item.name)};`)
    return lines.join('\n') + '\n'
}

function noteText(item) {
    const head = `${item.id} · ${item.name}\n${item.file}${item.lines ? ':' + item.lines : ''}${item.routes && item.routes.length ? '\nRoute: ' + item.routes.join(', ') : ''}\n` +
        `Annotated copy: ${item.annotated}\n${'-'.repeat(60)}\n`
    return head + item.code
}

function buildCategory(cat) {
    const b = new AgentflowBuilder()
    const items = spec.items.filter((i) => i.category === cat)
    const start = b.add('startAgentflow', 'Start · code map (documentation only)', { startInputType: 'chatInput', startEphemeralMemory: true, startState: '', startPersistState: false }, { x: -400, y: 0 })
    b.add('stickyNoteAgentflow', 'Sticky Note', {
        note: `READ ME · ${cat} — ${spec.categories[cat]}\n${items.length} functions / classes. Each node = one real function (open it: role, file, callers, callees).\n` +
            'The Sticky Note to its right holds the complete annotated source (real code + comments). Edges = verified calls / HTTP requests / dependencies inside this category; ' +
            'calls into other categories are listed in each node. Source of truth: code_explorer/registry/*.json (regenerate with code_explorer/tools/build_code_explorer.py).'
    }, { x: -400, y: -500 })
    const nodeOf = {}
    const columns = {}
    for (const it of items) (columns[it.file] = columns[it.file] || []).push(it)
    let x = 0
    for (const [file, list] of Object.entries(columns)) {
        let y = 0
        const width = Math.min(2600, Math.max(320, ...list.map((i) => Math.max(...noteText(i).split('\n').map((l) => l.length)) * 6.8)))
        const head = b.add('stickyNoteAgentflow', 'Sticky Note', { note: `FILE ${file}\n${list.length} definitions · ${list[0].sub}` }, { x, y: -200 })
        for (const it of list) {
            const id = b.add('customFunctionAgentflow', `${it.id} · ${it.name}${it.kind === 'class' || it.kind === 'pydantic_model' ? '' : '()'}`, {
                customFunctionInputVariables: [], customFunctionJavascriptFunction: docJs(it), customFunctionUpdateState: ''
            }, { x, y })
            nodeOf[it.id] = id
            const lines = noteText(it).split('\n').length
            b.add('stickyNoteAgentflow', 'Sticky Note', { note: noteText(it) }, { x: x + 250, y })
            y += Math.max(140, lines * 18 + 80)
        }
        b.connect(start, nodeOf[list[0].id], { label: file.split('/').pop() })
        x += width + 340
        void head
    }
    for (const e of spec.edges) {
        if (!nodeOf[e.from] || !nodeOf[e.to] || e.from === e.to) continue
        if (e.kind === 'references' && byId[e.to] && (byId[e.to].kind === 'class' || byId[e.to].kind === 'pydantic_model')) continue
        b.connect(nodeOf[e.from], nodeOf[e.to], { label: EDGE_LABEL[e.kind] || e.kind })
    }
    // the builder may create a duplicate edge id when two relations link the same pair: keep the first
    const seen = new Set()
    b.edges = b.edges.filter((e) => (seen.has(e.id) ? false : seen.add(e.id)))
    return { nodes: b.nodes, edges: b.edges }
}

function buildMaster(names) {
    const b = new AgentflowBuilder()
    const start = b.add('startAgentflow', 'Start · SCInsight Functions & Code Explorer', { startInputType: 'chatInput', startEphemeralMemory: true, startState: '', startPersistState: false }, { x: 0, y: 0 })
    const counts = {}
    for (const i of spec.items) counts[i.category] = (counts[i.category] || 0) + 1
    Object.entries(spec.categories).forEach(([cat, text], k) => {
        if (!counts[cat]) return
        const id = b.add('customFunctionAgentflow', `${cat.slice(0, 2)} · ${text.split(' — ')[0]} (${counts[cat]})`, {
            customFunctionInputVariables: [], customFunctionUpdateState: '',
            customFunctionJavascriptFunction: `// ${cat}: ${text}\n// ${counts[cat]} functions / classes.\n// Open the Agentflow "${names[cat]}" to inspect every function and its annotated source.\n` +
                `// Annotated modules: code_explorer/${cat}/  ·  index: code_explorer/${cat}/<subfolder>/FUNCTIONS.md\nreturn ${JSON.stringify(names[cat])};\n`
        }, { x: 340, y: k * 160 - 400 })
        b.connect(start, id, { label: 'category' })
    })
    // real execution paths, taken from the verified registry edges
    const find = (pred) => spec.items.find(pred)
    const paths = [
        ['FACTORY READINESS (Flowise specialist -> FastAPI -> Python -> SAP data)', [
            find((i) => i.kind === 'flowise_custom_function' && /Factory-Planning.*Calculate with SAP data/.test(i.name)),
            find((i) => i.file === 'backend/scinsight/app.py' && i.name === 'create_app.material_readiness'),
            find((i) => i.name === 'MaterialReadinessRequest'),
            find((i) => i.name === 'Service.material_readiness'),
            find((i) => i.name === 'calculate_bom_requirements'),
            find((i) => i.name === 'calculate_usable_stock'),
            find((i) => i.name === 'calculate_material_shortage'),
            find((i) => i.name === 'compare_supply_options'),
            find((i) => i.name === 'Database.query' && i.file === 'backend/scinsight/db.py'),
            find((i) => i.name === 'Service._save_run')]],
        ['POLICY RAG (Flowise tool -> FastAPI -> governed retrieval)', [
            find((i) => i.kind === 'flowise_tool' && /search_supply_chain_policy/.test(i.name)),
            find((i) => i.file === 'backend/scinsight/app.py' && i.name === 'create_app.rag_search'),
            find((i) => i.name === 'KnowledgeBase.search')]],
        ['HUMAN APPROVAL (supervisor Save -> recommendation -> authorised review)', [
            find((i) => i.kind === 'flowise_custom_function' && /Supervisor.*Save recommendation/.test(i.name)),
            find((i) => i.file === 'backend/scinsight/app.py' && i.name === 'create_app.create_decision'),
            find((i) => i.name === 'Service.create_decision'),
            find((i) => i.file === 'backend/scinsight/app.py' && i.name === 'create_app.review'),
            find((i) => i.name === 'Service.review'),
            find((i) => i.name === 'Security.require_reviewer'),
            find((i) => i.name === 'Security.audit')]],
    ]
    paths.forEach(([title, chain], row) => {
        const y0 = 900 + row * 420
        b.add('stickyNoteAgentflow', 'Sticky Note', { note: `EXECUTION PATH · ${title}\nEach node is the real function (open it for file, callers, callees); full code in its category flow.` }, { x: 0, y: y0 - 150 })
        let prev = null
        chain.filter(Boolean).forEach((it, k) => {
            const id = b.add('customFunctionAgentflow', `${it.id.startsWith('flowise:') ? 'Flowise' : it.id} · ${it.name}`, {
                customFunctionInputVariables: [], customFunctionJavascriptFunction: docJs(it), customFunctionUpdateState: ''
            }, { x: k * 300, y: y0 })
            if (prev) {
                const e = spec.edges.find((x) => x.from === prev.item.id && x.to === it.id)
                b.connect(prev.node, id, { label: e ? (EDGE_LABEL[e.kind] || e.kind) : 'then (same request)' })
            } else b.connect(start, id, { label: 'path' })
            prev = { node: id, item: it }
        })
    })
    b.add('stickyNoteAgentflow', 'Sticky Note', {
        note: 'READ ME · SCInsight — Functions & Code Explorer (documentation flow: running it only returns text)\n' +
            Object.entries(spec.categories).filter(([c]) => counts[c]).map(([c, t]) => `${c}  ->  Agentflow "${names[c]}"  (${counts[c]})  ${t}`).join('\n') +
            '\nEvery function node -> its annotated source in a Sticky Note; repository: code_explorer/ (FUNCTION_INDEX.md, viewer/index.html, registry/*.json).'
    }, { x: 0, y: -900 })
    return { nodes: b.nodes, edges: b.edges }
}

const names = Object.fromEntries(Object.entries(spec.categories).map(([c, t]) => [c, `${PREFIX}${c.slice(0, 2)} ${t.split(' — ')[0]}`]))
const flows = []
for (const cat of Object.keys(spec.categories)) if (spec.items.some((i) => i.category === cat)) flows.push({ name: names[cat], category: cat, flow: buildCategory(cat) })
flows.unshift({ name: MASTER, category: 'master', flow: buildMaster(names) })
process.stdout.write(JSON.stringify(flows))
