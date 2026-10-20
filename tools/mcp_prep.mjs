#!/usr/bin/env node
// Prep a harness instance: write mcpfabric config (enableUiControl), wait for bridge, join world.
// Usage: node tools/mcp_prep.mjs --game <dir> [--world sp:lm-final] [--timeout 300]
import fs from "node:fs";
import path from "node:path";
const argv = process.argv.slice(2);
const arg = (n, d) => { const i = argv.indexOf("--" + n); return i >= 0 ? argv[i + 1] : d; };
const game = arg("game");
const world = arg("world", "sp:lm-final");
const timeoutS = parseInt(arg("timeout", "300"), 10);
if (!game) { console.error("need --game"); process.exit(2); }
const cfgPath = path.join(game, "config", "mcpfabric.config.json");
fs.mkdirSync(path.dirname(cfgPath), { recursive: true });
let cfg = { host: "127.0.0.1", port: 25599, token: "", requireAuth: true, enableWorldWrite: true, enableCommands: true, enablePlayerControl: true, enableVision: true, enableUiControl: true };
if (fs.existsSync(cfgPath)) { try { cfg = { ...cfg, ...JSON.parse(fs.readFileSync(cfgPath, "utf8")) }; } catch {} }
cfg.enableUiControl = true;
cfg.enablePlayerControl = true;
if (!cfg.token) cfg.token = Math.random().toString(16).slice(2) + Math.random().toString(16).slice(2);
fs.writeFileSync(cfgPath, JSON.stringify(cfg, null, 2));
console.log("config ready (enableUiControl=true)");
const base = "http://" + cfg.host + ":" + cfg.port;
const headers = { "content-type": "application/json", authorization: "Bearer " + cfg.token };
async function call(m, p = {}) {
  const res = await fetch(base + "/rpc", { method: "POST", headers, body: JSON.stringify({ method: m, params: p }) });
  return await res.json().catch(() => ({ ok: false }));
}
// force zh_cn so language-dependent tests are stable
const optsPath = path.join(game, "options.txt");
try {
  let opts = fs.existsSync(optsPath) ? fs.readFileSync(optsPath, "utf8") : "";
  if (/^lang:/m.test(opts)) opts = opts.replace(/^lang:.*$/m, "lang:zh_cn");
  else opts += (opts.endsWith("\n") || opts === "" ? "" : "\n") + "lang:zh_cn\n";
  // auto-pause on lost focus makes the player not tick -> breaks interaction tests
  if (/^pauseOnLostFocus:/m.test(opts)) opts = opts.replace(/^pauseOnLostFocus:.*$/m, "pauseOnLostFocus:false");
  else opts += (opts.endsWith("\n") || opts === "" ? "" : "\n") + "pauseOnLostFocus:false\n";
  fs.writeFileSync(optsPath, opts);
  console.log("options.txt lang=zh_cn pauseOnLostFocus=false");
} catch (e) { console.log("warn: options.txt write failed", e.message); }

const hardDeadline = Date.now() + Math.min(timeoutS, 120) * 1000;
let ready = false;
let ticks = 0;
while (Date.now() < hardDeadline) {
  try { const r = await call("screen.get"); if (r?.ok) { ready = true; break; } } catch {}
  if (++ticks % 10 === 0) {
    console.log("waiting bridge... " + Math.round((Date.now() - (hardDeadline - Math.min(timeoutS,120)*1000)) / 1000) + "s");
    const logPath = path.join(game, "logs", "latest.log");
    if (fs.existsSync(logPath)) {
      const tail = fs.readFileSync(logPath, "utf8").slice(-4000);
      if (/Address already in use|failed to start HTTP bridge/i.test(tail)) {
        console.error("FATAL: mcpfabric bridge failed to bind (port 25599 in use). Kill stale java and relaunch.");
        process.exit(3);
      }
    }
  }
  await new Promise(r => setTimeout(r, 1000));
}
console.log("bridge:", ready ? "up" : "TIMEOUT(120s)");
if (!ready) { const logPath = path.join(game, "logs", "latest.log"); if (fs.existsSync(logPath)) console.error(fs.readFileSync(logPath,"utf8").slice(-800)); process.exit(1); }
let st = await call("screen.get");
const worldDeadline = Date.now() + timeoutS * 1000;
for (;;) {
  if (st?.result?.inWorld && st?.result?.screen !== "loading") break;
  if (st?.result?.screen === "title") { const j = await call("session.join", { worldId: world }); console.log("join:", JSON.stringify(j?.result ?? j?.error)); }
  if (Date.now() > worldDeadline) { console.log("world join TIMEOUT", JSON.stringify(st)); process.exit(1); }
  await new Promise(r => setTimeout(r, 1500));
  st = await call("screen.get");
}
console.log("in world:", JSON.stringify(st.result));