#!/usr/bin/env node
// Automated quest-book UI test via mcpfabric: open, list widgets, click chapter/next/quest/submit, screenshot.
// Usage: node tools/quest_ui_test.mjs --game <dir>
import fs from "node:fs";
import path from "node:path";
const argv = process.argv.slice(2);
const arg = (n, d) => { const i = argv.indexOf("--" + n); return i >= 0 ? argv[i + 1] : d; };
const game = arg("game");
const cfg = JSON.parse(fs.readFileSync(path.join(game, "config", "mcpfabric.config.json"), "utf8"));
const base = "http://" + cfg.host + ":" + cfg.port;
const headers = { "content-type": "application/json", authorization: "Bearer " + cfg.token };
async function call(m, p = {}) {
  const res = await fetch(base + "/rpc", { method: "POST", headers, body: JSON.stringify({ method: m, params: p }) });
  return await res.json().catch(() => ({ ok: false }));
}
const out = { step: [] };
await call("chat.send", { message: "/questbook open" });
await new Promise(r => setTimeout(r, 2500));
const scr = await call("screen.get");
out.screen = scr.result;
const w1 = await call("ui.widgets");
out.widgets_before = w1.result ?? w1.error;
const widgets = (w1.result?.widgets ?? w1.result ?? []);
const byType = (t) => widgets.filter(w => (w.type || "").toLowerCase().includes(t));
const chapters = widgets.filter(w => /chapter|章节/i.test(JSON.stringify(w)));
const next = widgets.find(w => /next|->|更多/i.test(JSON.stringify(w)));
const cells = widgets.filter(w => w.type && String(w.type).toLowerCase() === "other");
function click(w) { return call("ui.click", { widget: w.text || w.id }); }
const log = (k, v) => { out.step.push({ [k]: v }); console.log(k, JSON.stringify(v).slice(0, 300)); };
const submitState = () => (widgets.find(w => /submit|提交/i.test(w.text || "")) || {}).active;
out.submit_before = submitState();
if (cells.length) { const r = await click(cells[0]); log("click_cell", r.result ?? r.error); await new Promise(r => setTimeout(r, 800)); const w3 = await call("ui.widgets"); const ws3 = w3.result?.widgets ?? []; out.submit_after = (ws3.find(w => /submit|提交/i.test(w.text || "")) || {}).active; log("submit_after", out.submit_after); await new Promise(r => setTimeout(r, 600)); const shot2 = await call("vision.screenshot", {}); out.shot_after_cell = shot2.result ? "ok" : shot2.error; }
const shot = await call("vision.screenshot", {});
log("screenshot", shot.result ? { format: shot.result.format, w: shot.result.width, h: shot.result.height } : shot.error);
fs.writeFileSync("work/run26/port/g29/quest_ui_test.json", JSON.stringify(out, null, 2));
console.log("written work/run26/port/g29/quest_ui_test.json");