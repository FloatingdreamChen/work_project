import { spawn } from 'node:child_process'
import os from 'node:os'

function findLanAddress() {
  const interfaces = os.networkInterfaces()
  const candidates = []

  for (const [name, items] of Object.entries(interfaces)) {
    if (/^(lo|utun|ppp|bridge|awdl|llw)/.test(name)) continue
    for (const item of items || []) {
      if (item.family !== 'IPv4' || item.internal) continue
      if (/^(169\.254|127\.)/.test(item.address)) continue
      candidates.push({ name, address: item.address })
    }
  }

  return candidates.find((item) => item.address.startsWith('192.168.')) || candidates[0]
}

const selected = findLanAddress()
if (!selected) {
  console.error('No LAN IPv4 address found. Use npm run dev for localhost only.')
  process.exit(1)
}

console.log(`LAN interface: ${selected.name} ${selected.address}`)
console.log('Local: http://localhost:3000')
console.log(`Open: http://${selected.address}:3000`)
console.log(`mDNS: http://${os.hostname()}:3000`)

if (process.argv.includes('--print-only')) {
  process.exit(0)
}

const child = spawn(
  'vite',
  ['--host', '0.0.0.0', '--port', '3000', '--strictPort'],
  {
    stdio: 'inherit',
    shell: false,
  },
)

child.on('exit', (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal)
    return
  }
  process.exit(code ?? 0)
})
