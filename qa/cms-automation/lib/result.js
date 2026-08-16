'use strict';

/**
 * عقد النتيجة المهيكل — §13.
 *
 * كل استدعاء للـ specialist بيرجع الشكل ده. الـ orchestrator بيستهلك
 * البيانات، مش نص حر.
 *
 * إضافة على §13: حقل `verdictScope`. الـ specialist بيحكم على خطوته
 * بس — القرار النهائي للسيناريو ملك الـ orchestrator (§16.E). الحقل
 * ده بيخلي القاعدة دي مفروضة بالكود مش بالنية.
 */

const VALID = ['PASS', 'FAIL', 'BLOCKED'];

function stepResult({
  stepId, status, specialist, action,
  resourceType, erc, url,
  acIds = [],
  observed = {}, expected = {},
  assertions = [], evidence = [],
  error = null, timings = {},
}) {
  if (!stepId) throw new Error('stepResult: stepId مطلوب');
  if (!VALID.includes(status)) throw new Error(`stepResult: status غير صالح "${status}"`);

  return {
    stepId,
    status,
    verdictScope: 'STEP',   // الـ specialist لا يملك حكم السيناريو
    specialist: specialist || 'cms',
    action: action || null,
    resourceType: resourceType || null,
    erc: erc || null,
    url: url || null,
    /** ربط بمعايير القبول — بدونه التغطية غير قابلة للقياس. */
    acIds,
    observed,
    expected,
    assertions,
    evidence,
    error: error
      ? { message: String(error.message || error), kind: error.kind || 'UNKNOWN',
          blocking: !!error.isBlocking }
      : null,
    timings,
    at: new Date().toISOString(),
  };
}

/** تأكيد واحد داخل خطوة. */
const assertion = (name, passed, detail = {}) => ({ name, passed: !!passed, ...detail });

/**
 * حكم السيناريو — ملك الـ orchestrator وحده.
 *
 * القواعد:
 *  - أي خطوة BLOCKED → السيناريو BLOCKED (مش FAIL). التمييز ده مهم:
 *    عطل منصة مش عيب منتج، وخلطهم بيدفن الأعطال الحقيقية.
 *  - أي خطوة FAIL → FAIL
 *  - غير كده → PASS
 *  - أي AC مطلوب بدون خطوة بتغطيه → BLOCKED (تغطية ناقصة)
 */
function scenarioVerdict(steps, { requiredAcIds = [] } = {}) {
  const covered = new Set(steps.flatMap((s) => s.acIds || []));
  const uncovered = requiredAcIds.filter((a) => !covered.has(a));

  const blocked = steps.filter((s) => s.status === 'BLOCKED');
  const failed = steps.filter((s) => s.status === 'FAIL');

  let status = 'PASS';
  if (failed.length) status = 'FAIL';
  if (blocked.length || uncovered.length) status = 'BLOCKED';

  return {
    status,
    verdictScope: 'SCENARIO',
    totalSteps: steps.length,
    passed: steps.filter((s) => s.status === 'PASS').length,
    failed: failed.map((s) => s.stepId),
    blocked: blocked.map((s) => s.stepId),
    /** أين وقع العطل — CMS أم Web؟ §12 بيطلب التمييز ده صراحةً. */
    failureSurface: failed.length
      ? [...new Set(failed.map((s) => s.specialist))]
      : [],
    coverage: {
      required: requiredAcIds, covered: [...covered].filter((a) => requiredAcIds.includes(a)),
      uncovered,
    },
    at: new Date().toISOString(),
  };
}

module.exports = { stepResult, assertion, scenarioVerdict, VALID };
