// Batch fixer: exact-string / regex replacements with per-file backup (.bak-final).
// Usage: node fix-batch.cjs <table.cjs> ; table exports [{file, ops:[[find, repl, expectedCount]]}]
const fs = require('fs');
const path = require('path');
const root = process.argv[2];
const tableFile = process.argv[3];
const table = require(path.resolve(tableFile));

let ok = 0, bad = 0, touched = 0;
for (const entry of table) {
  const p = path.join(root, entry.file);
  let src;
  try { src = fs.readFileSync(p, 'utf8'); } catch (e) { console.log(`MISSING ${entry.file}`); bad++; continue; }
  let work = src;
  const problems = [];
  const log = [];
  for (const [find, repl, expect] of entry.ops) {
    if (typeof find === 'string' && find.startsWith('@import ')) {
      const cls = find.slice(8).trim();
      const line = `import ${cls};`;
      if (work.includes(line)) { log.push(`= ${cls}`); continue; }
      const lines = work.split('\n');
      let last = -1;
      for (let i = 0; i < lines.length; i++) {
        if (/^import /.test(lines[i])) last = i;
        if (last >= 0 && /^\s*$/.test(lines[i]) && i > last) break;
      }
      if (last < 0) { problems.push('no import block for ' + cls); continue; }
      lines.splice(last + 1, 0, line);
      work = lines.join(work.includes('\r\n') ? '\r\n' : '\n');
      log.push(`+ ${cls}`);
      continue;
    }
    if (find instanceof RegExp) {
      const m = work.match(find);
      const n = m ? m.length : 0;
      if (expect != null && n !== expect) problems.push(`regex ${find}: found ${n}, expected ${expect}`);
      work = work.replace(find, repl);
      log.push(`${n}x ${find}`);
    } else {
      // pick the variant (LF vs CRLF) that actually matches; files may be mixed
      let f = find, r = repl;
      if (work.includes('\r\n') && !work.includes(find) && work.includes(find.replace(/\n/g, '\r\n'))) {
        f = find.replace(/\n/g, '\r\n');
        r = repl.replace(/\n/g, '\r\n');
      }
      const parts = work.split(f);
      const n = parts.length - 1;
      if (expect != null && n !== expect) problems.push(`text "${find.slice(0, 60)}": found ${n}, expected ${expect}`);
      if (n === 0) problems.push(`NOT FOUND: ${find.slice(0, 80)}`);
      work = parts.join(r);
      log.push(`${n}x ${find.slice(0, 50)}`);
    }
  }
  if (problems.length) {
    console.log(`SKIP ${entry.file}`);
    for (const pr of problems) console.log(`   ${pr}`);
    bad++;
    continue;
  }
  const bak = p + '.bak-final';
  if (!fs.existsSync(bak)) fs.copyFileSync(p, bak);
  fs.writeFileSync(p, work);
  console.log(`OK   ${entry.file}  (${log.join(' | ')})`);
  touched++; ok++;
}
console.log(`\nfiles changed: ${touched}, skipped: ${bad}`);
