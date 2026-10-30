// Print line ranges from files: args like  path:12-30 path2:5-9 ...
const fs = require('fs');
const path = require('path');
const root = process.argv[2];
const specs = process.argv.slice(3);
for (const s of specs) {
  const m = s.match(/^(.*):(\d+)-(\d+)$/);
  if (!m) { console.log('bad spec ' + s); continue; }
  const p = path.isAbsolute(m[1]) ? m[1] : path.join(root, m[1]);
  const a = +m[2], b = +m[3];
  console.log(`\n===== ${m[1]} [${a}-${b}] =====`);
  let L;
  try { L = fs.readFileSync(p, 'utf8').split(/\r?\n/); } catch (e) { console.log('  !! ' + e.message); continue; }
  for (let i = a; i <= Math.min(b, L.length); i++) console.log(String(i).padStart(4) + '| ' + L[i - 1]);
}
