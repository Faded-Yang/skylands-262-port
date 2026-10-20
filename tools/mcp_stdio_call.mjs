#!/usr/bin/env node
// Minimal stdio MCP client for teammates: spawn an MCP server, initialize, call one tool, print JSON.
// Usage:
//   node tools/mcp_stdio_call.mjs --server mcmodding --tool search_fabric_docs --args '{"query":"register item"}'
//   node tools/mcp_stdio_call.mjs --server modrinth --tool search_mods --args '{"query":"create","loaders":["fabric"]}'
//   node tools/mcp_stdio_call.mjs --server mcmodding --list-tools
import { spawn } from "node:child_process";
import path from "node:path";
import os from "node:os";

const ROOT = path.resolve(process.cwd());
const NM = "work/run26/mcptools/node_modules";
const SERVERS = {
  mcmodding: path.join(ROOT, NM, "mcmodding-mcp/dist/index.js"),
  modrinth: path.join(ROOT, NM, "@mrfentmen/modrinth-mcp/dist/index.js"),
};
const argv = process.argv.slice(2);
function arg(n, d) { const i = argv.indexOf("--" + n); return i >= 0 ? argv[i + 1] : d; }
const server = arg("server");
const tool = arg("tool");
const listTools = argv.includes("--list-tools");
const argsJson = arg("args", "{}");

if (!server || !SERVERS[server]) {
  console.error("usage: --server mcmodding|modrinth --tool <name> [--args json] | --list-tools");
  process.exit(2);
}
const entry = SERVERS[server];
const child = spawn(process.execPath, [entry], { stdio: ["pipe", "pipe", "pipe"] });
let buf = "";
let nextId = 1;
const pending = new Map();
child.stdout.on("data", (d) => {
  buf += d.toString();
  let idx;
  while ((idx = buf.indexOf("\n")) >= 0) {
    const line = buf.slice(0, idx).trim();
    buf = buf.slice(idx + 1);
    if (!line) continue;
    let msg; try { msg = JSON.parse(line); } catch { continue; }
    if (msg.id && pending.has(msg.id)) { pending.get(msg.id)(msg); pending.delete(msg.id); }
  }
});
child.stderr.on("data", () => {});
function rpc(method, params) {
  const id = nextId++;
  return new Promise((resolve, reject) => {
    pending.set(id, resolve);
    child.stdin.write(JSON.stringify({ jsonrpc: "2.0", id, method, params }) + "\n");
    setTimeout(() => { if (pending.has(id)) { pending.delete(id); reject(new Error("timeout " + method)); } }, 30000);
  });
}
function notify(method, params) { child.stdin.write(JSON.stringify({ jsonrpc: "2.0", method, params }) + "\n"); }

try {
  const init = await rpc("initialize", { protocolVersion: "2024-11-05", capabilities: {}, clientInfo: { name: "dsh-teammate-cli", version: "1.0" } });
  notify("notifications/initialized", {});
  if (listTools) {
    const res = await rpc("tools/list", {});
    console.log(JSON.stringify(res.result?.tools?.map(t => ({ name: t.name, description: (t.description || "").slice(0, 120) })), null, 2));
  } else {
    if (!tool) { console.error("need --tool"); process.exit(2); }
    const res = await rpc("tools/call", { name: tool, arguments: JSON.parse(argsJson) });
    const content = res.result?.content ?? res.result ?? res;
    const texts = Array.isArray(content) ? content.filter(c => c.type === "text").map(c => c.text) : [JSON.stringify(content)];
    console.log(texts.join("\n"));
  }
} catch (e) {
  console.error("ERROR: " + e.message);
  process.exitCode = 1;
} finally {
  child.kill();
}