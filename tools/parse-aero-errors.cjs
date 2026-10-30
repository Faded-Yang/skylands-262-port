#!/usr/bin/env node
// Parse javac (zh-CN) error log into structured JSON/text.
// usage: node parse-aero-errors.cjs <log> [--by=symbol|file|msg] [--top=N] [--file=Substr] [--sym=Substr]
const fs = require('fs');

const logPath = process.argv[2];
if (!logPath) { console.error('need log'); process.exit(2); }
const argv = process.argv.slice(3);
const opt = { by: 'symbol', top: 40, file: null, sym: null, full: false };
for (const a of argv) {
  let m;
  if ((m = a.match(/^--by=(.*)$/))) opt.by = m[1];
  else if ((m = a.match(/^--top=(\d+)$/))) opt.top = +m[1];
  else if ((m = a.match(/^--file=(.*)$/))) opt.file = m[1];
  else if ((m = a.match(/^--sym=(.*)$/))) opt.sym = m[1];
  else if (a === '--full') opt.full = true;
}

const raw = fs.readFileSync(logPath, 'utf8').replace(/\r\n/g, '\n');
const lines = raw.split('\n').map(l => l.replace(/^\s{2,}(?=[A-Za-z]:\\)/, ''));

const HEAD = /^(.*?):(\d+): (错误|error): (.*)$/;
const errs = [];
let cur = null;
for (const line of lines) {
  const m = line.match(HEAD);
  if (m && /\.java$/.test(m[1].trim())) {
    if (cur) errs.push(cur);
    cur = { file: m[1].trim(), line: +m[2], msg: m[4].trim(), detail: [] };
    continue;
  }
  if (cur) {
    if (/^(注:|Note:|\d+ 个错误|BUILD |\* Try)/.test(line.trim())) { errs.push(cur); cur = null; continue; }
    if (line.trim() !== '') cur.detail.push(line.replace(/\s+$/, ''));
  }
}
if (cur) errs.push(cur);

// dedupe repeated (gradle prints a simplified second pass)
{
  const seen = new Set();
  const uniq = [];
  for (const e of errs) {
    const k = `${e.file}:${e.line}:${e.msg}`;
    if (seen.has(k)) continue;
    seen.add(k);
    uniq.push(e);
  }
  errs.length = 0;
  errs.push(...uniq);
}

// derive symbol
for (const e of errs) {
  e.symbol = '';
  e.pkg = '';
  for (const d of e.detail) {
    let m;
    if ((m = d.match(/^\s*符号:\s*(?:类|方法|变量|内部类|接口)?\s*(\S.*)$/))) { e.symbol = e.symbol || m[1].trim(); continue; }
    if ((m = d.match(/^\s*symbol:\s*(?:class|method|variable)?\s*(\S.*)$/))) { e.symbol = e.symbol || m[1].trim(); continue; }
    if ((m = d.match(/^\s*位置:\s*(?:类|接口|程序包|package)?\s*(.*)$/))) { e.pkg = e.pkg || m[1].trim(); continue; }
    if ((m = d.match(/^\s*location:\s*(?:class|package)?\s*(.*)$/))) { e.pkg = e.pkg || m[1].trim(); continue; }
  }
  // package-not-exist errors: symbol is embedded in msg
  let m;
  if (!e.symbol && (m = e.msg.match(/^程序包(\S+)不存在/))) e.symbol = 'PKG:' + m[1];
  if (!e.symbol && (m = e.msg.match(/^package (\S+) does not exist/))) e.symbol = 'PKG:' + m[1];
  if (!e.symbol) e.symbol = e.msg;
  // normalize symbol for grouping: strip leading "类 "
  e.key = e.symbol.replace(/^(类|方法|变量|内部类)\s*/, '').trim();
}

let sel = errs;
if (opt.file) sel = sel.filter(e => e.file.toLowerCase().includes(opt.file.toLowerCase()));
if (opt.sym) sel = sel.filter(e => e.key.toLowerCase().includes(opt.sym.toLowerCase()) || e.msg.includes(opt.sym));

const groups = new Map();
for (const e of sel) {
  const k = opt.by === 'file' ? e.file : opt.by === 'msg' ? e.msg : e.key;
  if (!groups.has(k)) groups.set(k, []);
  groups.get(k).push(e);
}
const sorted = [...groups.entries()].sort((a, b) => b[1].length - a[1].length);

console.log(`TOTAL errors in log: ${errs.length}; selected: ${sel.length}; groups: ${sorted.length}`);
for (const [k, list] of sorted.slice(0, opt.top)) {
  if (opt.by === 'msg') {
    console.log(`[${String(list.length).padStart(3)}] ${k}`);
  } else if (opt.by === 'file') {
    const short = k.replace(/^.*\\aeronautics-26\\/, '');
    console.log(`[${String(list.length).padStart(3)}] ${short}`);
  } else {
    const files = new Set(list.map(e => e.file));
    const pkgs = new Set(list.map(e => e.pkg).filter(Boolean));
    console.log(`[${String(list.length).padStart(3)}] ${k}   (${files.size} file(s))`);
    if (opt.full && pkgs.size) console.log(`        loc: ${[...pkgs].slice(0, 6).join(' | ')}`);
    if (opt.full) for (const e of list.slice(0, 30)) console.log(`        ${e.file.replace(/^.*\\aeronautics-26\\/, '')}:${e.line}  ${e.msg}`);
  }
}
if (opt.full && sel.length && opt.top === 0) {
  for (const e of sel) console.log(`${e.file.replace(/^.*\\aeronautics-26\\/, '')}:${e.line} | ${e.msg} | ${e.key} | ${e.pkg}`);
}
