// Reconstruct the PRE-round snapshot of every file touched by table-batch1/2 by
// reverse-applying the replacement tables to the current content, and write it as
// "<file>.bak-r352". Rationale: all 39 files already carried a stale ".bak-final"
// from earlier rounds, so the batch fixer (which never overwrites) left no true
// pre-round backup. This script recreates one deterministically.
const fs = require('fs');
const path = require('path');
const root = process.argv[2];
const tables = [
  require('C:/Users/95959/OneDrive/Desktop/Work/skylands-262/tools/table-batch1.cjs'),
  require('C:/Users/95959/OneDrive/Desktop/Work/skylands-262/tools/table-batch2.cjs'),
  // manual follow-up edit on GirderBlockMixin (see docs/fix-aero-final.md §3 #7)
  [{ file: 'src/main/java/dev/simulated_team/simulated/mixin/auger_shaft/GirderBlockMixin.java',
     ops: [
       ['// PORT(26.3): 1.21.11 的 GirderBlock.isConnected 首参是 BlockAndTintGetter；26.3 改成\r\n'
        + '//   BlockAndLightGetter（javap 实测）。@Inject 处理器参数必须与目标描述符完全一致，\r\n'
        + '//   所以这里用 BlockAndLightGetter 而不是「搬到 client.renderer.block 的 BlockAndTintGetter」。\r\n'
        + 'import net.minecraft.world.level.BlockAndLightGetter;',
        'import net.minecraft.world.level.BlockAndTintGetter;', 1],
       ['final BlockAndLightGetter world,', 'final BlockAndTintGetter world,', 1],
     ] }],
];

// merge per file, preserving op order (table1 then table2 then manual)
const byFile = new Map();
for (const t of tables) {
  for (const e of t) {
    if (!byFile.has(e.file)) byFile.set(e.file, []);
    byFile.get(e.file).push(...e.ops);
  }
}

const importLine = (cls) => `import ${cls};`;
let written = 0;
for (const [file, ops] of byFile) {
  const p = path.join(root, file);
  let work;
  try { work = fs.readFileSync(p, 'utf8'); } catch { console.log(`MISSING ${file}`); continue; }
  const problems = [];
  // reverse order
  for (let i = ops.length - 1; i >= 0; i--) {
    const [find, repl] = ops[i];
    if (typeof find === 'string' && find.startsWith('@import ')) {
      const line = importLine(find.slice(8).trim());
      // only remove if the batch actually added it (heuristic: our own insert point is right
      // after the last import line; removing by exact line is enough here)
      const idx = work.split('\n').findIndex(l => l.trim() === line.trim());
      if (idx >= 0) {
        const lines = work.split('\n');
        lines.splice(idx, 1);
        work = lines.join('\n');
      }
      continue;
    }
    const crlf = work.includes('\r\n');
    const r = crlf ? repl.replace(/\n/g, '\r\n') : repl;
    const f = crlf ? find.replace(/\n/g, '\r\n') : find;
    const n = work.split(r).length - 1;
    if (n === 0) { problems.push(`inverse not found: ${r.slice(0, 70)}`); continue; }
    work = work.split(r).join(f);
  }
  if (problems.length) {
    console.log(`SKIP ${file}`);
    for (const pr of problems) console.log('   ' + pr);
    continue;
  }
  fs.writeFileSync(p + '.bak-r352', work);
  written++;
  console.log(`OK   ${file}`);
}
console.log(`\nbak-r352 written: ${written}`);
