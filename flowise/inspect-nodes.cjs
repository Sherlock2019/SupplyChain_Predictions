// Print input definitions of the Flowise nodes used by the generated flows (run inside the Flowise container).
const path = require('path')
const C = '/usr/local/lib/node_modules/flowise/node_modules/flowise-components/dist/nodes'
const files = process.argv.slice(2)
for (const f of files) {
    try {
        const m = require(path.join(C, f))
        const n = new m.nodeClass()
        console.log('==', f, n.name, 'v' + n.version, n.type, JSON.stringify(n.baseClasses), n.category)
        for (const i of n.inputs || []) {
            console.log('  ', i.name, '|', i.type, i.optional ? '(opt)' : '', i.list ? '[list]' : '', i.default !== undefined ? 'default=' + JSON.stringify(i.default).slice(0, 80) : '',
                i.show ? 'show=' + JSON.stringify(i.show) : '', i.loadMethod ? 'load=' + i.loadMethod : '', i.array ? 'array=' + JSON.stringify(i.array.map((a) => a.name)) : '')
        }
        if (n.credential) console.log('   credential', JSON.stringify(n.credential))
        if (n.outputs) console.log('   outputs', JSON.stringify(n.outputs))
    } catch (e) {
        console.log('ERR', f, e.message)
    }
}
