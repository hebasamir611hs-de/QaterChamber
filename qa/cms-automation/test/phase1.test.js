'use strict';

/** اختبارات الإضافات الخمسة + نموذج الحالات الأربع. */

const { test } = require('node:test');
const assert = require('node:assert');

process.env.QC_PASS = 'dummy';
process.env.QC_GROUP_ID = '37246';

const { contracts, contractForField, compareWithContract } = require('../lib/normalization-contracts');
const { OWNERSHIP, MUTATION, classifyMutation, declareDataPlan } = require('../lib/data-ownership');
const { TestStateModel, STATUS } = require('../lib/test-states');
const { AcOracle } = require('../lib/ac-oracle');
const { diff, toAssertion } = require('../lib/cleanup-verify');

/* ═════════════ عقود التطبيع ═════════════ */

test('العقد يُشتق من businessType لا من التخمين', () => {
  assert.strictEqual(contractForField({ name: 'title', businessType: 'Text' }).id, 'text');
  assert.strictEqual(contractForField({ name: 'body', businessType: 'LongText' }).id, 'richText');
  assert.strictEqual(contractForField({ name: 'publicationDate', businessType: 'Date' }).id, 'dateTime');
  assert.strictEqual(contractForField({ name: 'displayOrder', businessType: 'Integer' }).id, 'number');
  assert.strictEqual(contractForField({ name: 'activeStatus', businessType: 'Boolean' }).id, 'boolean');
  assert.strictEqual(contractForField({ name: 'logoImage', businessType: 'Attachment' }).id, 'attachment');
  assert.strictEqual(contractForField({ name: 'title', businessType: 'Text', localized: true }).id, 'localizedText');
});

test('حقل نصي اسمه redirectUrl يُعامل كـ URL', () => {
  assert.strictEqual(contractForField({ name: 'logoRedirectUrl', businessType: 'LongText' }).id, 'url');
});

test('عقد URL: الشرطة الأخيرة وبارامترات التتبّع لا تُفشِل', () => {
  const r = compareWithContract({ name: 'redirectUrl', businessType: 'Text' },
    '/qatar-chamber/news/', '/qatar-chamber/news?utm_source=x');
  assert.strictEqual(r.match, true);
});

test('عقد الرقم: الفواصل والأرقام العربية لا تُفشِل', () => {
  const r = compareWithContract({ name: 'counterValue', businessType: 'Integer' }, 1963, '١٬٩٦٣');
  assert.strictEqual(r.match, true);
});

test('عقد التاريخ: التخزين UTC مقابل العرض المنسّق بتوقيت قطر', () => {
  const r = compareWithContract({ name: 'publicationDate', businessType: 'Date' },
    '2026-08-15T09:00:00Z', '15/08/2026');
  assert.strictEqual(r.match, true);
  assert.match(r.mode, /formatted/);
});

test('عقد المرفق: المقارنة على اسم الملف لا على الـ id', () => {
  const r = compareWithContract({ name: 'bannerImage', businessType: 'Attachment' },
    { link: { href: '/documents/37246/0/hero-banner.jpg' } },
    'https://cdn.example.com/o/hero-banner.jpg?w=800');
  assert.strictEqual(r.match, true);
});

test('عقد المنطقي: نعم/لا العربية تُقرأ صح', () => {
  assert.strictEqual(compareWithContract({ name: 'active', businessType: 'Boolean' }, true, 'نعم').match, true);
  assert.strictEqual(compareWithContract({ name: 'active', businessType: 'Boolean' }, true, 'لا').match, false);
});

test('عقد المترجَم: علامة (AR) تُتخطّى افتراضياً وتفشل عند طلب ترجمة حقيقية', () => {
  const f = { name: 'title', businessType: 'Text', localized: true };
  assert.strictEqual(compareWithContract(f, { ar_SA: 'News (AR)' }, 'أخبار', { locale: 'ar_SA' }).match, true);
  assert.strictEqual(
    compareWithContract(f, { ar_SA: 'News (AR)' }, 'أخبار', { locale: 'ar_SA', expect: 'real' }).match, false);
});

test('عقد المترجَم: قيمة "?" تُصنَّف تلف مصدر لا عيب عرض', () => {
  const r = compareWithContract({ name: 'x', businessType: 'Text', localized: true },
    { ar_SA: '?' }, 'أي شيء', { locale: 'ar_SA' });
  assert.strictEqual(r.match, false);
  assert.strictEqual(r.mode, 'source-corrupt');
});

test('العقد لا يبتلع اختلافاً حقيقياً', () => {
  assert.strictEqual(compareWithContract({ name: 'title', businessType: 'Text' }, 'Qatar Chamber', 'Dubai Chamber').match, false);
});

/* ═════════════ ملكية البيانات ═════════════ */

const objRisky = {
  name: 'NewsArticle',
  fields: [
    { name: 'activeStatus', businessType: 'Boolean', required: true },
    { name: 'thumbnailImage', businessType: 'Attachment', required: false },
    { name: 'title', businessType: 'Text', required: true },
  ],
};

test('DISPOSABLE: عدم قابلية التراجع غير ضارّ — الحذف يغطّيها', () => {
  const c = classifyMutation(objRisky, 'QCTEST-RUN-1-x', { activeStatus: false });
  assert.strictEqual(c.mutation, MUTATION.DISPOSABLE);
  assert.strictEqual(c.allowed, true);
  assert.strictEqual(c.cleanup, 'DELETE');
});

test('SNAPSHOT_RESTORE + حقل غير قابل للتراجع = PROHIBITED', () => {
  const c = classifyMutation(objRisky, 'QCDEMO-129364-real', { activeStatus: false });
  assert.strictEqual(c.mutation, MUTATION.PROHIBITED);
  assert.strictEqual(c.allowed, false);
});

test('صف موجود بتعديل آمن = REVERSIBLE', () => {
  const c = classifyMutation(objRisky, 'QCDEMO-129364-real', { title: 'x' });
  assert.strictEqual(c.mutation, MUTATION.REVERSIBLE);
  assert.strictEqual(c.cleanup, 'RESTORE');
});

test('إعلان البيانات: فارغ = غير صالح', () => {
  assert.strictEqual(declareDataPlan('S1', []).valid, false);
});

test('إعلان البيانات: SNAPSHOT_RESTORE بلا سبب = غير صالح', () => {
  const p = declareDataPlan('S1', [{ ownership: OWNERSHIP.SNAPSHOT_RESTORE, erc: 'QCDEMO-1' }]);
  assert.strictEqual(p.valid, false);
  assert.match(p.error, /reason/);
});

test('إعلان البيانات: disposable صالح ويُلخَّص', () => {
  const p = declareDataPlan('S1', [{ ownership: OWNERSHIP.DISPOSABLE, name: 'news' }]);
  assert.strictEqual(p.valid, true);
  assert.strictEqual(p.summary.disposable, 1);
});

/* ═════════════ الحالات الأربع ═════════════ */

test('البوابة: لا يمكن تقييم PRESENTATION قبل SYSTEM', () => {
  const m = new TestStateModel('S1');
  assert.strictEqual(m.canEvaluate('PRESENTATION').ok, false);
  assert.strictEqual(m.canEvaluate('PRESENTATION').blockedBy, 'TEST');
});

test('البوابة: فشل SYSTEM يمنع تنفيذ PRESENTATION أصلاً', async () => {
  const m = new TestStateModel('S1');
  await m.evaluate('TEST', async () => ({ satisfied: true }));
  await m.evaluate('DATA', async () => ({ satisfied: true }));
  await m.evaluate('SYSTEM', async () => ({ satisfied: false }));

  let ran = false;
  const r = await m.evaluate('PRESENTATION', async () => { ran = true; return { satisfied: true }; });

  assert.strictEqual(ran, false, 'ما كانش المفروض يشتغل');
  assert.strictEqual(r.status, STATUS.BLOCKED);
});

test('تشخيص السطح: توقّف عند SYSTEM ⇒ cms، عند PRESENTATION ⇒ web', async () => {
  const a = new TestStateModel('A');
  await a.evaluate('TEST', async () => ({ satisfied: true }));
  await a.evaluate('DATA', async () => ({ satisfied: true }));
  await a.evaluate('SYSTEM', async () => ({ satisfied: false }));
  assert.strictEqual(a.failureSurface, 'cms');

  const b = new TestStateModel('B');
  for (const s of ['TEST', 'DATA', 'SYSTEM']) await b.evaluate(s, async () => ({ satisfied: true }));
  await b.evaluate('PRESENTATION', async () => ({ satisfied: false }));
  assert.strictEqual(b.failureSurface, 'web');
});

test('كل الحالات مُرضية ⇒ لا سطح عطل', async () => {
  const m = new TestStateModel('S');
  for (const s of ['TEST', 'DATA', 'SYSTEM', 'PRESENTATION']) await m.evaluate(s, async () => ({ satisfied: true }));
  assert.strictEqual(m.haltedAt, null);
  assert.strictEqual(m.failureSurface, null);
});

/* ═════════════ AC Oracle ═════════════ */

const oracle = new AcOracle([
  { id: 'AC-1', description: 'الخبر يُحفظ', requiredAssertions: ['mutation-persisted', 'bilingual:title'] },
  { id: 'AC-2', description: 'الخبر يظهر', requiredAssertions: ['cross-system:homepage-title'] },
  { id: 'AC-3', description: 'اختياري', optional: true, requiredAssertions: ['x'] },
]);

test('AC يُثبَت بالتأكيدات لا بحالة الخطوة', () => {
  const steps = [{ stepId: 'S1', assertions: [
    { name: 'mutation-persisted', passed: true },
    { name: 'bilingual:title', passed: true },
  ] }];
  const r = oracle.evaluate(steps);
  assert.deepStrictEqual(r.proven, ['AC-1']);
  assert.deepStrictEqual(r.notCovered, ['AC-2']);
  assert.strictEqual(r.complete, false);
});

test('خطوة PASS لا تُثبت AC إن كان تأكيده لم يُنفَّذ', () => {
  const steps = [{ stepId: 'S1', status: 'PASS', assertions: [{ name: 'شيء-آخر', passed: true }] }];
  assert.strictEqual(oracle.evaluate(steps).proven.length, 0);
});

test('تأكيد فاشل يجعل الـ AC FAILED لا NOT_COVERED', () => {
  const r = oracle.evaluate([{ stepId: 'S1', assertions: [{ name: 'cross-system:homepage-title', passed: false }] }]);
  assert.deepStrictEqual(r.failed, ['AC-2']);
});

test('الأنماط بالنجمة مدعومة', () => {
  const o = new AcOracle([{ id: 'AC-9', requiredAssertions: ['cross-system:*'] }]);
  assert.deepStrictEqual(o.evaluate([{ assertions: [{ name: 'cross-system:anything', passed: true }] }]).proven, ['AC-9']);
});

test('الـ AC الاختياري لا يمنع الاكتمال', () => {
  const r = oracle.evaluate([{ assertions: [
    { name: 'mutation-persisted', passed: true },
    { name: 'bilingual:title', passed: true },
    { name: 'cross-system:homepage-title', passed: true },
  ] }]);
  assert.strictEqual(r.complete, true);
  assert.strictEqual(r.coverageRatio, 1);
});

/* ═════════════ التحقق من التنظيف ═════════════ */

const snap = (o) => ({ takenAt: 'x', objects: o });

test('التنظيف: بيئة مطابقة = CLEAN', () => {
  const b = snap({ News: { count: 2, keys: ['A', 'B'] } });
  assert.strictEqual(diff(b, JSON.parse(JSON.stringify(b))).verdict, 'CLEAN');
});

test('التنظيف: صف تست متبقٍّ = DIRTY', () => {
  const r = diff(snap({ News: { count: 1, keys: ['A'] } }),
                 snap({ News: { count: 2, keys: ['A', 'QCTEST-RUN-1-x'] } }));
  assert.strictEqual(r.verdict, 'DIRTY');
  assert.strictEqual(r.findings[0].testOwned, 1);
  assert.strictEqual(r.foreignChanges.length, 0);
});

test('التنظيف: صف غريب يُميَّز عن تنظيفنا الناقص', () => {
  const r = diff(snap({ News: { count: 1, keys: ['A'] } }),
                 snap({ News: { count: 2, keys: ['A', 'QCDEMO-جديد'] } }));
  assert.strictEqual(r.foreignChanges[0].foreign, 1);
  assert.match(toAssertion(r).detail, /بيئة مشتركة/);
});

test('التنظيف: فقدان بيانات أصلية = حاجب', () => {
  const r = diff(snap({ News: { count: 2, keys: ['A', 'B'] } }), snap({ News: { count: 1, keys: ['A'] } }));
  assert.strictEqual(r.verdict, 'DATA_LOSS');
  assert.strictEqual(toAssertion(r).blocking, true);
});
