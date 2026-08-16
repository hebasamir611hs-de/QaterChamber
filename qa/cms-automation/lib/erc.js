'use strict';

/**
 * هوية الموارد بالـ ERC + فصل بيانات التست.
 *
 * كل صف بتنشئه التستات لازم يحمل بادئة التست. ده العقد الوحيد اللي
 * لو اتكسر، التنظيف بيسيب بيانات ورا على بيئة مشتركة.
 */

const env = require('../config/env');

/** معرّف run فريد: RUN-20260815T134500Z-a3f9 */
function newRunId(now = new Date()) {
  const stamp = now.toISOString().replace(/[-:]/g, '').replace(/\.\d+Z$/, 'Z');
  const rand = Math.floor(Math.random() * 0xffff).toString(16).padStart(4, '0');
  return `RUN-${stamp}-${rand}`;
}

const slug = (s) =>
  String(s).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 60);

/** ERC لصف تست: QCTEST-{runId}-{slug} */
function fixtureErc(runId, name) {
  if (!runId) throw new Error('fixtureErc: runId مطلوب');
  return `${env.testPrefix}${runId}-${slug(name)}`;
}

/** هل الصف ده ملك للتستات؟ */
const isFixture = (erc) => typeof erc === 'string' && erc.startsWith(env.testPrefix);

/** هل الصف ده بتاع run معيّن؟ */
const isFixtureOfRun = (erc, runId) =>
  typeof erc === 'string' && erc.startsWith(`${env.testPrefix}${runId}-`);

/**
 * بوابة الأمان — تُستدعى قبل أي تعديل.
 *
 * على بيئة مشتركة، أي تعديل على صف مش بتاع التستات هو تلويث لشغل
 * حد تاني. الوضع الافتراضي بيمنعه. التستات اللي محتاجة تعدّل صف
 * موجود لازم تمرر allowExisting:true صراحةً — والتصريح ده بيخلي
 * الاسترجاع إجباري.
 */
function assertMutable(erc, { allowExisting = false, reason = '' } = {}) {
  if (isFixture(erc)) return { ok: true, kind: 'FIXTURE' };
  if (!env.strictFixtureIsolation) return { ok: true, kind: 'EXISTING_UNGUARDED' };
  if (allowExisting) {
    if (!reason) {
      throw new Error(
        `تعديل صف موجود (${erc}) لازم يمرر reason — عشان يتسجّل في سجل التعديلات.`
      );
    }
    return { ok: true, kind: 'EXISTING_GUARDED', reason };
  }
  throw new Error(
    `ممنوع تعديل ${erc}: مش صف تست وبادئة الحماية شغّالة.\n` +
      `لو التست محتاج يعدّل صف موجود فعلاً، مرّر { allowExisting: true, reason: '...' } — ` +
      `وساعتها الاسترجاع بيبقى إجباري.`
  );
}

module.exports = { newRunId, fixtureErc, isFixture, isFixtureOfRun, assertMutable, slug };
