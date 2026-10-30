// Dump javac error blocks with symbol/needed/found detail. Usage: node err-detail.cjs <log> [--file=Substr]
const fs = require('fs');
const log = process.argv[2];
const fileFilter = (process.argv.find(a => a.startsWith('--file=')) || '').slice(7);
const lines = fs.readFileSync(log, 'utf8').split(/\r?\n/);
const blocks = [];
let cur = null;
for (const ln of lines) {
  const m = ln.match(/^(.*?\.java):(\d+):\s*(错误|error):\s*(.*)$/);
  if (m) {
    if (cur) blocks.push(cur);
    cur = { file: m[1], line: +m[2], msg: m[4], detail: [] };
    continue;
  }
  if (cur) {
    if (/^\s*$/.test(ln)) { if (cur.detail.length) { blocks.push(cur); cur = null; } continue; }
    if (/^\s*(符号|位置|需要|找到|原因|symbol|location|required|found|reason)\s*:/.test(ln.trim())
        || /^\s{4,}\S/.test(ln)) {
      cur.detail.push(ln.trim());
    } else {
      // new section header (task line, gradle, etc)
      blocks.push(cur); cur = null;
    }
  }
}
if (cur) blocks.push(cur);
let shown = 0;
for (const b of blocks) {
  if (fileFilter && !b.file.includes(fileFilter)) continue;
  shown++;
  const rel = b.file.replace(/^.*aeronautics-26\\/, '');
  console.log(`${rel}:${b.line}`);
  console.log(`   ${b.msg}`);
  for (const d of b.detail) console.log(`     | ${d}`);
}
console.log(`\n--- blocks: ${blocks.length}, shown: ${shown} ---`);
