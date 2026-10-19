// Minimal WebSocket JSON-RPC client for the ported minecraft-mcp Fabric mod.
// Usage: node tools/mcp_fabric_client.mjs <method> ['<params-json>'] [--port 25576] [--timeout 15000] [--out <dir>]
import fs from 'node:fs';
import path from 'node:path';

const argv = process.argv.slice(2);
let port = 25576, timeout = 15000, outDir = null;
const rest = [];
for (let i = 0; i < argv.length; i++) {
  const a = argv[i];
  if (a === '--port') port = Number(argv[++i]);
  else if (a === '--timeout') timeout = Number(argv[++i]);
  else if (a === '--out') outDir = argv[++i];
  else rest.push(a);
}
const method = rest[0];
let params = {};
if (rest[1]) params = JSON.parse(rest[1]);
if (!method) { console.error('usage: node mcp_fabric_client.mjs <method> [params-json] [--port N] [--out dir]'); process.exit(2); }

function saveIfImage(res) {
  const candidates = [];
  if (typeof res === 'string') candidates.push(res);
  if (res && typeof res === 'object') {
    for (const k of ['data', 'base64', 'image', 'png']) if (typeof res[k] === 'string') candidates.push(res[k]);
  }
  for (const raw of candidates) {
    const s = raw.startsWith('data:') ? raw.slice(raw.indexOf(',') + 1) : raw;
    if (s.length > 5000 && /^[A-Za-z0-9+/=\s]+$/.test(s)) {
      const dir = outDir || path.join(process.cwd(), 'screenshots');
      fs.mkdirSync(dir, { recursive: true });
      const file = path.join(dir, 'mcp-' + Date.now() + '.png');
      fs.writeFileSync(file, Buffer.from(s.replace(/\s/g, ''), 'base64'));
      console.log('WROTE ' + file + ' (' + fs.statSync(file).size + ' bytes)');
      return true;
    }
  }
  return false;
}

const id = 'req-' + Date.now();
const ws = new WebSocket('ws://127.0.0.1:' + port);
const timer = setTimeout(() => { console.error('TIMEOUT'); try { ws.close(); } catch {} process.exit(3); }, timeout);
ws.addEventListener('open', () => ws.send(JSON.stringify({ id, method, params })));
ws.addEventListener('message', (ev) => {
  let msg;
  try { msg = JSON.parse(String(ev.data)); } catch { console.error('BAD JSON'); return; }
  if (msg.id !== id) return;
  clearTimeout(timer);
  if (msg.error) { console.error('ERROR ' + JSON.stringify(msg.error)); ws.close(); process.exit(1); }
  const res = msg.result;
  if (!saveIfImage(res)) console.log(typeof res === 'string' ? res : JSON.stringify(res, null, 2));
  ws.close(); process.exit(0);
});
ws.addEventListener('error', (e) => { clearTimeout(timer); console.error('WS ERROR ' + (e.message || 'connect failed')); process.exit(4); });
