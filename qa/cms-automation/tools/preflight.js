#!/usr/bin/env node
'use strict';

/**
 * preflight — §14 كفحص حي، مش كورقة.
 * شغّله قبل أي run. لو فشل، متكملش.
 *
 * رموز الخروج: 0=جاهز  1=تحذيرات  2=فشل حاسم
 */

const env = require('../config/env');
const { get, getAll, byErcPath } = require('../lib/rest-client');
const { loadCatalog, entriesPath } = require('../lib/objects');

const checks = [];
const add = (name, status, detail) => {
  checks.push({ name, status, detail });
  console.log(`${status === 'PASS' ? '✓' : status === 'WARN' ? '⚠️ ' : '✗'} ${name}${detail ? ` — ${detail}` : ''}`);
};

(async () => {
  console.log(`فحص البيئة: ${env.baseUrl}  (groupId ${env.groupId})\n`);

  /* 1) المصادقة + الموقع */
  try {
    const site = await get(byErcPath('/o/headless-admin-site/v1.0/sites', env.siteErc));
    if (site.__notFound) add('الموقع', 'FAIL', `${env.siteErc} غير موجود`);
    else if (String(site.id) !== String(env.groupId))
      add('الموقع', 'FAIL', `groupId الحقيقي ${site.id} ≠ QC_GROUP_ID=${env.groupId}`);
    else add('الموقع', 'PASS', `groupId ${site.id}`);
  } catch (e) {
    add('المصادقة/الموقع', 'FAIL', `${e.kind}: ${String(e.message).slice(0, 120)}`);
  }

  /* 2) سقف pageSize (§5.3) */
  try {
    const r = await get('/o/object-admin/v1.0/object-definitions?page=1&pageSize=99');
    add('حد pageSize', r.__notFound ? 'PASS' : 'WARN',
      r.__notFound ? 'السلوك الموثّق قائم — السقف 50 مطبّق' : 'الباج اتصلح؛ الكود لسه آمن');
  } catch { add('حد pageSize', 'PASS', 'السقف 50 مطبّق'); }

  /* 3) الكتالوج */
  let cat;
  try {
    cat = await loadCatalog();
    add('كتالوج الـ Objects', cat.objects.length >= 100 ? 'PASS' : 'WARN', `${cat.objects.length} Object`);
    if (cat.meta.unrecoverable.length)
      add('اكتمال الكتالوج', 'WARN', `${cat.meta.unrecoverable.length} ERC معروف لم يُسترجع`);
    else add('اكتمال الكتالوج', 'PASS');
  } catch (e) {
    add('كتالوج الـ Objects', 'FAIL', String(e.message).slice(0, 140));
  }

  /* 4) القراءة بالـ scope (§8) */
  if (cat) {
    const s = cat.byName.get('NewsArticle') || cat.objects[0];
    try {
      const items = await getAll(entriesPath(s), 10);
      add('القراءة بالـ scope', 'PASS', `${s.name}: ${items.length} صف`);
    } catch (e) {
      add('القراءة بالـ scope', 'FAIL', `${e.kind}: ${String(e.message).slice(0, 140)}`);
    }
  }

  /* 5) العلاقات — 3 موثّقة. أي تغيير يعني ترتيب الحذف اتغيّر. */
  if (cat) {
    const uniq = new Set(
      cat.objects.flatMap((o) => o.relationships
        .filter((r) => ['oneToMany', 'oneToOne'].includes(r.type))
        .map((r) => `${r.parentId}->${r.childId}`))
    );
    add('العلاقات', uniq.size === 3 ? 'PASS' : 'WARN',
      uniq.size === 3 ? '3 كما هو موثّق' : `${uniq.size} (المتوقع 3) — راجع ترتيب الحذف`);
  }

  /* 6) بقايا بيانات تست */
  if (cat) {
    let n = 0; const dirty = [];
    for (const o of cat.objects) {
      try {
        const items = await getAll(entriesPath(o), 100);
        const t = items.filter((i) => String(i.externalReferenceCode || '').startsWith(env.testPrefix));
        if (t.length) { n += t.length; dirty.push(`${o.name}(${t.length})`); }
      } catch { /* غُطّي في فحص 4 */ }
    }
    add('نظافة البيئة', n ? 'FAIL' : 'PASS',
      n ? `${n} صف تست قديم: ${dirty.slice(0, 6).join(', ')} — نظّفه أولاً` : `مفيش صفوف بادئة بـ ${env.testPrefix}`);
  }

  const fails = checks.filter((c) => c.status === 'FAIL');
  const warns = checks.filter((c) => c.status === 'WARN');
  console.log('\n══════════ الخلاصة ══════════');
  if (fails.length) { console.log(`✗ ${fails.length} فحص حاسم فشل. متبدأش الـ run.`); process.exit(2); }
  if (warns.length) { console.log(`⚠️  جاهز مع ${warns.length} تحذير.`); process.exit(1); }
  console.log('✓ البيئة جاهزة.'); process.exit(0);
})().catch((e) => { console.error('[✗] فشل الـ preflight:', e.message); process.exit(2); });
