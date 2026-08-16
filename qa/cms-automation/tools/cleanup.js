#!/usr/bin/env node
'use strict';

/**
 * تنظيف بيانات التست — الأبناء قبل الآباء.
 *
 *   node tools/cleanup.js --dry-run
 *   node tools/cleanup.js
 *   node tools/cleanup.js --run-id RUN-...
 */

const env = require('../config/env');
const { getAll, deleteByErc } = require('../lib/rest-client');
const { loadCatalog, deletionOrder, isSelfReferencing, entriesPath } = require('../lib/objects');

const args = process.argv.slice(2);
if (args.includes('--help') || args.includes('-h')) {
  console.log(`استخدام:
  node tools/cleanup.js --dry-run           اعرض بدون حذف
  node tools/cleanup.js                     امسح كل ${env.testPrefix}*
  node tools/cleanup.js --run-id RUN-...    امسح run معيّن فقط`);
  process.exit(0);
}
const DRY = args.includes('--dry-run');
const i = args.indexOf('--run-id');
const RUN_ID = i >= 0 ? args[i + 1] : null;
const MATCH = RUN_ID ? `${env.testPrefix}${RUN_ID}-` : env.testPrefix;

/** ترتيب الشجرة الذاتية: الأعمق أولاً (NavItem). */
function deepestFirst(items) {
  const byId = new Map(items.map((i) => [String(i.id), i]));
  const depth = (it, seen = new Set()) => {
    const pf = Object.keys(it).find((k) => /^r_.*_c_.*Id$/.test(k) && it[k] && byId.has(String(it[k])));
    if (!pf) return 0;
    const pid = String(it[pf]);
    if (seen.has(pid)) return 0;
    seen.add(pid);
    return 1 + depth(byId.get(pid), seen);
  };
  return [...items].sort((a, b) => depth(b) - depth(a));
}

(async () => {
  console.log(`[i] البادئة: "${MATCH}"${DRY ? '  (تجربة)' : ''}`);
  const cat = await loadCatalog();
  const ordered = deletionOrder(cat.objects);
  console.log(`[i] ${cat.objects.length} Object — ترتيب الحذف محسوب من العلاقات الحية.\n`);

  let found = 0, deleted = 0;
  const failures = [], plan = [];

  for (const o of ordered) {
    let items;
    try { items = await getAll(entriesPath(o), 100); }
    catch (e) { console.warn(`[!] ${o.name}: ${String(e.message).slice(0, 100)}`); continue; }

    let targets = items.filter((it) => String(it.externalReferenceCode || '').startsWith(MATCH));
    if (!targets.length) continue;
    if (isSelfReferencing(o)) { targets = deepestFirst(targets); console.log(`[i] ${o.name} شجرة ذاتية — الأعمق أولاً.`); }

    found += targets.length;
    plan.push({ object: o.name, count: targets.length });
    console.log(`▸ ${o.name} — ${targets.length}`);

    for (const t of targets) {
      const erc = t.externalReferenceCode;
      if (DRY) { console.log(`    [تجربة] ${erc}`); continue; }
      try { await deleteByErc(o.restPath, erc); deleted++; console.log(`    ✓ ${erc}`); }
      catch (e) { console.error(`    ✗ ${erc} — ${String(e.message).slice(0, 140)}`); failures.push({ erc, object: o.name }); }
    }
  }

  console.log('\n══════════ الملخص ══════════');
  if (!found) { console.log(`[✓] مفيش صفوف بادئة بـ "${MATCH}".`); process.exit(0); }
  if (DRY) {
    console.log(`سيُحذف ${found} صف عبر ${plan.length} Object:`);
    plan.forEach((p) => console.log(`  ${String(p.count).padStart(4)}  ${p.object}`));
    process.exit(0);
  }
  console.log(`اتمسح ${deleted}/${found}.`);
  if (failures.length) {
    console.log(`\n⛔ فشل ${failures.length}. السبب الأشهر: أبناء لم تُحذف. شغّل تاني.`);
    process.exit(1);
  }
  console.log('[✓] تم. شغّل fingerprint diff للتأكيد.');
  process.exit(0);
})().catch((e) => { console.error('[✗]', e.message); process.exit(3); });
