#!/usr/bin/env node
'use strict';

/**
 * propagation-probe — قياس زمن انتشار التغيير من الـ CMS للموقع.
 *
 * ⚠️ الحالة: الادعاء بأن السبب هو cache/Elasticsearch **غير مُتحقَّق منه**.
 * السكربت ده هو أداة التحقق. شغّليه من جهاز داخل الشبكة اللي بتوصل
 * qcdev، ووثّقي المخرجات في liferay-context.md كـ [LIVE].
 *
 * ما يقيسه:
 *   t0  زمن نجاح الـ PUT
 *   t1  زمن ما يعكس الـ REST القيمة الجديدة        (read-after-write)
 *   t2  زمن ما يعكس الـ Headless Delivery القيمة    (طبقة القراءة العامة)
 *   t3  زمن ما تعكس الصفحة المعروضة القيمة          (--page)
 *
 * التفسير:
 *   t1 ≈ 0 و t3 كبير      → التأخير في العرض/الـ cache، لا في الكتابة
 *   t1 كبير               → التأخير في طبقة الـ CMS نفسها (index/workflow)
 *   t3 ≈ t1               → لا يوجد تأخير عرض إضافي — الـ polling قد يكون أقل أهمية
 *
 * الاستخدام:
 *   node tools/propagation-probe.js --object NewsArticle [--page /qatar-chamber] [--samples 3]
 *
 * السلامة: بينشئ صف تست ببادئة QCTEST- ويحذفه في النهاية — دايماً،
 * حتى لو فشل. مش بيلمس أي بيانات موجودة.
 */

const env = require('../config/env');
const { put, get, byErcPath, sleep } = require('../lib/rest-client');
const { findObject, getEntry } = require('../lib/objects');
const { deleteByErc } = require('../lib/rest-client');
const { fixtureErc, newRunId } = require('../lib/erc');

const args = process.argv.slice(2);
const arg = (n, d) => { const i = args.indexOf(n); return i >= 0 ? args[i + 1] : d; };
const OBJECT = arg('--object', 'NewsArticle');
const PAGE = arg('--page', null);
const SAMPLES = Number(arg('--samples', 3));
const MAX_MS = Number(arg('--max-ms', 60000));

async function pollUntil(label, check, maxMs = MAX_MS, interval = 250) {
  const t = Date.now();
  for (;;) {
    try { if (await check()) return Date.now() - t; } catch { /* لسه */ }
    if (Date.now() - t > maxMs) return null;
    await sleep(interval);
  }
}

async function sample(o, i, runId) {
  const erc = fixtureErc(runId, `probe-${i}`);
  const marker = `PROBE-${runId}-${i}-${Date.now()}`;
  const titleField = o.fields.find((f) => /title|name|label/i.test(f.name) && f.businessType === 'Text')
    || o.fields.find((f) => f.businessType === 'Text');
  if (!titleField) throw new Error(`${o.name}: لا يوجد حقل نصي صالح للفحص`);

  const payload = { externalReferenceCode: erc, [titleField.name]: marker };
  for (const f of o.fields) {
    if (!f.required || f.name in payload) continue;
    if (f.businessType === 'Text' || f.businessType === 'LongText') payload[f.name] = marker;
    else if (f.businessType === 'Integer') payload[f.name] = 100;
    else if (f.businessType === 'Boolean') payload[f.name] = true;
    else if (f.businessType === 'Date' || f.businessType === 'DateTime') payload[f.name] = new Date().toISOString();
  }

  const tPut = Date.now();
  await put(byErcPath(o.restPath, erc), payload);
  const putMs = Date.now() - tPut;

  const t1 = await pollUntil('rest', async () => {
    const e = await getEntry(o, erc);
    return e && String(e[titleField.name]) === marker;
  });

  let t2 = null;
  try {
    t2 = await pollUntil('delivery', async () => {
      const r = await get(`${o.restPath}/scopes/${env.groupId}?page=1&pageSize=100`);
      return (r.items || []).some((it) => it.externalReferenceCode === erc && String(it[titleField.name]) === marker);
    }, 20000);
  } catch { /* غير متاح */ }

  let t3 = null;
  if (PAGE) {
    t3 = await pollUntil('page', async () => {
      const r = await fetch(env.baseUrl + PAGE, { headers: { 'Cache-Control': 'no-cache' } });
      return (await r.text()).includes(marker);
    }, MAX_MS, 500);
  }

  await deleteByErc(o.restPath, erc).catch(() => {});
  return { i, field: titleField.name, putMs, restMs: t1, deliveryMs: t2, pageMs: t3 };
}

(async () => {
  const runId = newRunId();
  console.log(`propagation-probe — ${env.baseUrl}`);
  console.log(`Object: ${OBJECT}   عينات: ${SAMPLES}   صفحة: ${PAGE || '(غير مفحوصة)'}`);
  console.log(`runId: ${runId}\n`);

  const o = await findObject(OBJECT);
  const rows = [];
  for (let i = 1; i <= SAMPLES; i++) {
    process.stdout.write(`  عينة ${i}/${SAMPLES} ... `);
    try { const r = await sample(o, i, runId); rows.push(r); console.log('تم'); }
    catch (e) { console.log(`فشل: ${e.message.slice(0, 100)}`); }
  }

  if (!rows.length) { console.log('\nلا توجد عينات ناجحة.'); process.exit(2); }

  const col = (k) => rows.map((r) => r[k]).filter((v) => v !== null && v !== undefined);
  const stat = (k) => {
    const v = col(k);
    if (!v.length) return 'n/a';
    return `min ${Math.min(...v)}ms  متوسط ${Math.round(v.reduce((a, b) => a + b, 0) / v.length)}ms  max ${Math.max(...v)}ms`;
  };

  console.log('\n══════════ النتيجة ══════════');
  console.log(`PUT                    ${stat('putMs')}`);
  console.log(`REST read-after-write  ${stat('restMs')}`);
  console.log(`Scoped listing         ${stat('deliveryMs')}`);
  console.log(`الصفحة المعروضة        ${PAGE ? stat('pageMs') : 'لم تُفحص (مرّر --page)'}`);

  const rest = col('restMs'), page = col('pageMs');
  const avg = (a) => (a.length ? a.reduce((x, y) => x + y, 0) / a.length : null);
  const rAvg = avg(rest), pAvg = avg(page);

  console.log('\n──────── التفسير ────────');
  if (rAvg !== null && rAvg > 2000)
    console.log(`• الـ CMS نفسه بيتأخر (~${Math.round(rAvg)}ms) — التأخير في الكتابة/الفهرسة مش في العرض.`);
  else if (rAvg !== null)
    console.log(`• الـ CMS بيعكس فوراً (~${Math.round(rAvg)}ms) — الكتابة ليست مصدر التأخير.`);

  if (pAvg === null && PAGE)
    console.log(`• الصفحة لم تعكس التغيير خلال ${MAX_MS}ms — تأخير عرض كبير أو الصفحة لا تعرض هذا الـ Object.`);
  else if (pAvg !== null && rAvg !== null)
    console.log(pAvg - rAvg > 1000
      ? `• تأخير عرض إضافي ~${Math.round(pAvg - rAvg)}ms بعد ثبات الـ CMS → polling على طبقة العرض ضروري.`
      : `• لا يوجد تأخير عرض إضافي ملموس → السبب ليس cache العرض. راجع الافتراض.`);

  console.log('\nالمهلة المقترحة لـ QC_PROPAGATION_TIMEOUT_MS:',
    Math.max(10000, Math.ceil(((pAvg ?? rAvg ?? 5000) * 3) / 1000) * 1000), 'ms');
  console.log('\n⚠️  وثّقي المخرجات دي في liferay-context.md كـ [LIVE] مع التاريخ.');
  console.log('   لحد ما يحصل ده، سبب التأخير يفضل UNVERIFIED — آلية الـ polling صحيحة');
  console.log('   بغض النظر عن السبب، لكن التفسير مش مثبت.');
  process.exit(0);
})().catch((e) => { console.error('[✗]', e.message); process.exit(2); });
