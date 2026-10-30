#!/usr/bin/env node
// Registrate shim shape fixes for block registration files.
// 1. `.simpleItem().transform(customItemModel(...))` : the shim's simpleItem() returns BlockBuilder
//    (upstream returns ItemBuilder) and AbstractBuilder.transform() only takes NonNullUnaryOperator<S>,
//    so the ItemBuilder operator no longer applies. Route through .item() (returns ItemBuilder) and
//    .build() (returns the parent BlockBuilder) to preserve the chain type.
// 2. Drop no-arg `.onRegister()` calls (only legal against the shim's `onRegister(Object...)` varargs).
const fs = require('fs');
let totalA = 0, totalB = 0;
for (const f of process.argv.slice(2)) {
  let src = fs.readFileSync(f, 'utf8');
  let a = 0;
  src = src.replace(/\.simpleItem\(\)(\s*)\.transform\((customItemModel\([^()]*\))\)/g, (m, ws, cm) => {
    a++;
    return `.item()${ws}.transform(${cm}).build()`;
  });
  let b = 0;
  src = src.replace(/^[ \t]*\.onRegister\(\)[ \t]*\r?\n/gm, () => { b++; return ''; });
  fs.writeFileSync(f, src);
  console.log(`${f}: simpleItem+transform -> ${a}; no-arg onRegister removed -> ${b}`);
  totalA += a; totalB += b;
}
console.log(`TOTAL: ${totalA} chains, ${totalB} onRegister`);
