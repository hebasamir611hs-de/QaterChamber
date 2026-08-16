'use strict';

/**
 * اختبارات وحدة للمنطق الحرج — بدون اتصال حي.
 *   node --test test/
 */

const { test } = require('node:test');
const assert = require('node:assert');

process.env.QC_PASS = 'dummy';
process.env.QC_GROUP_ID = '37246';

const N = require('../lib/normalize');
const { deletionOrder } = require('../lib/objects');
const { checkReversible } = require('../lib/mutation-log');
const { stepResult, scenarioVerdict } = require('../lib/result');
const { fixtureErc, isFixture, assertMutable, newRunId } = require('../lib/erc');
const { waitFor, PropagationTimeout } = require('../lib/propagation');
const A = require('../assertions');

/* ============================ التطبيع ============================ */

test('التطبيع: يشيل HTML ويوحّد المسافات', () => {
  assert.strictEqual(N.normalizeText('<p>Qatar&nbsp;Chamber</p>  <br/> News'), 'Qatar Chamber News');
});

test('التطبيع: الأرقام العربية تساوي ASCII', () => {
  assert.strictEqual(N.normalizeDigits('تأسست ١٩٦٣'), 'تأسست 1963');
});

test('التطبيع: المقارنة تقبل الاقتطاع بـ …', () => {
  const r = N.textMatches('Qatar Chamber launches new digital services platform', 'Qatar Chamber launches new…');
  assert.strictEqual(r.match, true);
  assert.strictEqual(r.mode, 'truncated');
});

test('التطبيع: الاقتطاع القصير جداً لا يُقبل كتطابق', () => {
  const r = N.textMatches('Qatar Chamber launches platform', 'Qat…');
  assert.strictEqual(r.match, false);
});

test('التطبيع: اختلاف حقيقي يُرصد ولا يُبتلع', () => {
  const r = N.textMatches('Qatar Chamber', 'Doha Chamber');
  assert.strictEqual(r.match, false);
  assert.strictEqual(r.mode, 'mismatch');
});

test('التطبيع: مفاتيح اللغة بالشرطة والشرطة السفلية تُقرأ الاتنين', () => {
  assert.strictEqual(N.pickLocalized({ 'en-US': 'Hi' }, 'en_US'), 'Hi');
  assert.strictEqual(N.pickLocalized({ en_US: 'Hi' }, 'en-US'), 'Hi');
});

test('تصنيف العربي: real / pending / corrupt / empty', () => {
  assert.strictEqual(N.classifyArabic('غرفة قطر'), 'real');
  assert.strictEqual(N.classifyArabic('Header Configuration (AR)'), 'pending');
  assert.strictEqual(N.classifyArabic('?'), 'corrupt');
  assert.strictEqual(N.classifyArabic('   '), 'empty');
});

test('التواريخ: نفس اللحظة رغم اختلاف صيغة العرض', () => {
  const r = N.sameInstant('2026-08-15T09:00:00Z', '2026-08-15T12:00:00+03:00');
  assert.strictEqual(r.match, true);
});

/* ======================= ترتيب الحذف ======================= */

test('ترتيب الحذف: الأبناء قبل الآباء، والشجرة الذاتية بلا دورة', () => {
  const objs = [
    { id: 1, name: 'FooterNavigationColumn', relationships: [{ type: 'oneToMany', parentId: 1, childId: 2 }] },
    { id: 2, name: 'FooterNavigationLink', relationships: [] },
    { id: 3, name: 'ServiceInformationGroup', relationships: [{ type: 'oneToMany', parentId: 3, childId: 4 }] },
    { id: 4, name: 'ServiceInformationGroupItem', relationships: [] },
    { id: 5, name: 'NavItem', relationships: [{ type: 'oneToMany', parentId: 5, childId: 5 }] },
  ];
  const order = deletionOrder(objs).map((o) => o.name);
  assert.ok(order.indexOf('FooterNavigationLink') < order.indexOf('FooterNavigationColumn'));
  assert.ok(order.indexOf('ServiceInformationGroupItem') < order.indexOf('ServiceInformationGroup'));
  assert.strictEqual(order.length, 5);
});

/* =================== التعديلات غير القابلة للتراجع =================== */

const objWithRisky = {
  name: 'Demo',
  fields: [
    { name: 'activeStatus', businessType: 'Boolean', required: true },
    { name: 'optionalFlag', businessType: 'Boolean', required: false },
    { name: 'logoImage', businessType: 'Attachment', required: false },
    { name: 'title', businessType: 'Text', required: true },
  ],
};

test('عدم قابلية التراجع: Boolean مطلوب يُرصد قبل التعديل', () => {
  const r = checkReversible(objWithRisky, { activeStatus: false });
  assert.strictEqual(r.reversible, false);
  assert.strictEqual(r.blockers[0].type, 'REQUIRED_BOOLEAN');
});

test('عدم قابلية التراجع: المرفقات تُرصد', () => {
  assert.strictEqual(checkReversible(objWithRisky, { logoImage: 123 }).reversible, false);
});

test('عدم قابلية التراجع: التعديل الآمن يمر', () => {
  const r = checkReversible(objWithRisky, { title: 'x', optionalFlag: false });
  assert.strictEqual(r.reversible, true);
  assert.strictEqual(r.blockers.length, 0);
});

/* ======================= عزل بيانات التست ======================= */

test('ERC: بناء معرّف صف تست ببادئة الـ run', () => {
  const erc = fixtureErc('RUN-X', 'News Alpha!');
  assert.strictEqual(erc, 'QCTEST-RUN-X-news-alpha');
  assert.ok(isFixture(erc));
});

test('الحماية: تعديل صف موجود مرفوض افتراضياً', () => {
  assert.throws(() => assertMutable('QCDEMO-129364-launch'), /ممنوع تعديل/);
});

test('الحماية: مسموح بتصريح صريح + سبب', () => {
  const r = assertMutable('QCDEMO-129364-launch', { allowExisting: true, reason: 'AC-3 يتطلب صفاً حقيقياً' });
  assert.strictEqual(r.kind, 'EXISTING_GUARDED');
});

test('الحماية: التصريح بدون سبب مرفوض', () => {
  assert.throws(() => assertMutable('QCDEMO-1', { allowExisting: true }), /reason/);
});

test('الحماية: صفوف التست تمر بدون تصريح', () => {
  assert.strictEqual(assertMutable('QCTEST-RUN-1-x').kind, 'FIXTURE');
});

test('runId فريد', () => {
  assert.notStrictEqual(newRunId(), newRunId());
});

/* ========================= انتظار الانتشار ========================= */

test('الانتشار: ينجح بعد عدة محاولات بدل sleep ثابت', async () => {
  let n = 0;
  const r = await waitFor('قيمة تجريبية', async () => (++n >= 3 ? { ok: true, value: n } : { ok: false, observed: n }),
    { timeoutMs: 2000, intervalMs: 10 });
  assert.strictEqual(r.value, 3);
  assert.strictEqual(r.attempts, 3);
});

test('الانتشار: انتهاء المهلة يرمي PropagationTimeout مع آخر ملاحظة', async () => {
  await assert.rejects(
    () => waitFor('لن يتحقق', async () => ({ ok: false, observed: 'activeStatus=true' }),
      { timeoutMs: 60, intervalMs: 10 }),
    (e) => e instanceof PropagationTimeout && e.lastObserved === 'activeStatus=true'
  );
});

/* ========================= عقد النتيجة ========================= */

test('حكم السيناريو: BLOCKED يغلب FAIL', () => {
  const v = scenarioVerdict([
    stepResult({ stepId: 'S1', status: 'FAIL', specialist: 'cms' }),
    stepResult({ stepId: 'S2', status: 'BLOCKED', specialist: 'web' }),
  ]);
  assert.strictEqual(v.status, 'BLOCKED');
});

test('حكم السيناريو: يميّز سطح العطل CMS مقابل Web', () => {
  const v = scenarioVerdict([
    stepResult({ stepId: 'S1', status: 'PASS', specialist: 'cms' }),
    stepResult({ stepId: 'S2', status: 'FAIL', specialist: 'web' }),
  ]);
  assert.strictEqual(v.status, 'FAIL');
  assert.deepStrictEqual(v.failureSurface, ['web']);
});

test('حكم السيناريو: AC غير مغطّى = BLOCKED مش PASS', () => {
  const v = scenarioVerdict(
    [stepResult({ stepId: 'S1', status: 'PASS', specialist: 'cms', acIds: ['AC-1'] })],
    { requiredAcIds: ['AC-1', 'AC-2'] }
  );
  assert.strictEqual(v.status, 'BLOCKED');
  assert.deepStrictEqual(v.coverage.uncovered, ['AC-2']);
});

test('عقد النتيجة: الـ specialist لا يملك حكم السيناريو', () => {
  assert.strictEqual(stepResult({ stepId: 'S1', status: 'PASS' }).verdictScope, 'STEP');
});

/* ========================== التأكيدات ========================== */

test('التأكيد: علامة (AR) لا تفشّل تستاً عاماً', () => {
  const e = { titleAr: 'News Article (AR)' };
  assert.strictEqual(A.arabicContent(e, 'titleAr').passed, true);
  assert.strictEqual(A.arabicContent(e, 'titleAr', { expect: 'real' }).passed, false);
});

test('التأكيد: قيمة "?" تفشل دائماً', () => {
  assert.strictEqual(A.arabicContent({ x: '?' }, 'x').passed, false);
});

test('التأكيد: displayOrder غير مضاعف 100 يحذّر ولا يفشل افتراضياً', () => {
  const r = A.displayOrderValid({ displayOrder: 150 });
  assert.strictEqual(r.passed, true);
  assert.match(r.warning, /مضاعفات 100/);
  assert.strictEqual(A.displayOrderValid({ displayOrder: 150 }, 'displayOrder', { strictHundreds: true }).passed, false);
});

test('التأكيد: رابط فوتر بدون عمود أب يفشل', () => {
  assert.strictEqual(A.footerLinkHasColumn({}).passed, false);
  assert.strictEqual(
    A.footerLinkHasColumn({ r_footerNavColumnLinks_c_footerNavigationColumnId: 46203 }).passed, true);
});

test('التأكيد: لا نفترض علاقة غير معرّفة في الـ metadata', () => {
  const o = { name: 'MediationPage', fields: [{ name: 'title', businessType: 'Text' }] };
  const r = A.relationshipSet(o, { r_fake: 1 }, 'r_fake');
  assert.strictEqual(r.passed, false);
  assert.strictEqual(r.blocking, true);
});

test('التأكيد: المقارنة عبر الأنظمة تعبر طبقة التطبيع', () => {
  const r = A.crossSystemText('<p>غرفة قطر ١٩٦٣</p>', 'غرفة قطر 1963', 'title');
  assert.strictEqual(r.passed, true);
});

test('التأكيد: ترتيب معروض مخالف لـ displayOrder يفشل', () => {
  const entries = [
    { externalReferenceCode: 'A', displayOrder: 200 },
    { externalReferenceCode: 'B', displayOrder: 100 },
  ];
  assert.strictEqual(A.orderMatches(entries, ['B', 'A']).passed, true);
  assert.strictEqual(A.orderMatches(entries, ['A', 'B']).passed, false);
});
