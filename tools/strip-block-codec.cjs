#!/usr/bin/env node
// 26.3: Block/BlockBehaviour no longer expose simpleCodec()/propertiesCodec() and blocks are
// no longer MapCodec-serialized (vanilla block classes have no CODEC field at all).
// Remove `MapCodec<X> CODEC = ...;` declarations and their `codec()` overrides.
const fs = require('fs');

function parenBalanced(s) {
  let p = 0, b = 0;
  for (const ch of s) {
    if (ch === '(') p++;
    else if (ch === ')') p--;
    else if (ch === '{') b++;
    else if (ch === '}') b--;
  }
  return p === 0 && b === 0;
}

for (const f of process.argv.slice(2)) {
  const lines = fs.readFileSync(f, 'utf8').split('\n');
  const removed = [];

  // 1) CODEC declaration
  for (let i = 0; i < lines.length; i++) {
    if (/\bCODEC\s*=/.test(lines[i]) && /MapCodec\b/.test(lines[i])) {
      let j = i, acc = '';
      for (; j < lines.length; j++) {
        acc += lines[j];
        if (/;\s*$/.test(lines[j]) && parenBalanced(acc)) break;
      }
      removed.push(`CODEC decl L${i + 1}-${j + 1}: ${lines[i].trim().slice(0, 70)}`);
      lines.splice(i, j - i + 1);
      i--;
    }
  }

  // 2) codec() override returning CODEC
  for (let i = 0; i < lines.length; i++) {
    if (!/codec\s*\(\s*\)\s*\{/.test(lines[i])) continue;
    if (!/MapCodec</.test(lines[i])) continue;
    // single-line form?
    let end = -1;
    if (/codec\s*\(\s*\)\s*\{.*\}/.test(lines[i])) {
      end = i;
    } else {
      for (let j = i + 1; j < lines.length; j++) {
        if (/^\s*\}\s*$/.test(lines[j])) { end = j; break; }
      }
    }
    if (end < 0) continue;
    let start = i;
    if (start > 0 && /^\s*@Override\s*$/.test(lines[start - 1])) start--;
    removed.push(`codec() override L${start + 1}-${end + 1}`);
    lines.splice(start, end - start + 1);
    // drop one blank line left behind
    if (lines[start] !== undefined && lines[start].trim() === '' && lines[start - 1] !== undefined && lines[start - 1].trim() === '') lines.splice(start, 1);
    i = start - 1;
  }

  // 3) unused import of MapCodec if no longer referenced
  const body = lines.join('\n');
  const rest = body.replace(/^import .*MapCodec.*$/m, '');
  if (/^import\s+[\w.]*MapCodec;$/m.test(body) && !/\bMapCodec\b/.test(rest)) {
    for (let i = 0; i < lines.length; i++) {
      if (/^import\s+[\w.]*MapCodec;/.test(lines[i])) { removed.push(`import MapCodec L${i + 1}`); lines.splice(i, 1); break; }
    }
  }

  fs.writeFileSync(f, lines.join('\n'));
  console.log(`${f}\n  ${removed.join('\n  ') || 'NOTHING REMOVED'}`);
}
