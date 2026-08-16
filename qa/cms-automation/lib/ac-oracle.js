'use strict';

/**
 * AC → Oracle mapping.
 *
 * المشكلة اللي بيحلّها: PASS/FAIL على مستوى السيناريو مش قابل للقياس.
 * لو سيناريو نجح، ده مش معناه إن معايير القبول اتغطّت — ممكن يكون
 * غطّى واحد وساب اتنين.
 *
 * العقد: كل AC بيعلن **التأكيدات اللازمة لإثباته**. الـ AC ما بيعتبرش
 * مُثبَتاً إلا لما كل تأكيداته تنجح فعلياً — مش لما الخطوة اللي
 * بتحمل الـ id بتاعه تنجح.
 *
 * الفرق ده مش شكلي: خطوة واحدة ممكن تحمل 5 تأكيدات وتُعلَن PASS
 * والتأكيد الخاص بالـ AC مكانش اتنفّذ أصلاً.
 */

class AcOracle {
  /**
   * @param {Array<{id, description, requiredAssertions: string[], optional?: boolean}>} criteria
   */
  constructor(criteria = []) {
    this.criteria = criteria;
    this.byId = new Map(criteria.map((c) => [c.id, c]));
    const dup = criteria.map((c) => c.id).filter((id, i, a) => a.indexOf(id) !== i);
    if (dup.length) throw new Error(`AC مكرر: ${dup.join(', ')}`);
  }

  get requiredIds() {
    return this.criteria.filter((c) => !c.optional).map((c) => c.id);
  }

  /**
   * يقيّم التغطية من خطوات فعلية.
   * بيفحص أسماء التأكيدات الناجحة، مش حالة الخطوة.
   */
  evaluate(steps) {
    const passedAssertions = new Set();
    const failedAssertions = new Map();

    for (const s of steps) {
      for (const a of s.assertions || []) {
        const key = a.name;
        if (a.passed) passedAssertions.add(key);
        else failedAssertions.set(key, { stepId: s.stepId, detail: a.detail });
      }
    }

    const results = this.criteria.map((c) => {
      const missing = [];
      const failed = [];
      for (const req of c.requiredAssertions || []) {
        const matcher = toMatcher(req);
        const hit = [...passedAssertions].some((n) => matcher(n));
        if (hit) continue;
        const failHit = [...failedAssertions.keys()].find((n) => matcher(n));
        if (failHit) failed.push({ assertion: req, ...failedAssertions.get(failHit) });
        else missing.push(req);
      }
      const status = failed.length ? 'FAILED' : missing.length ? 'NOT_COVERED' : 'PROVEN';
      return { id: c.id, description: c.description, optional: !!c.optional, status, failed, missing };
    });

    const required = results.filter((r) => !r.optional);
    return {
      criteria: results,
      proven: required.filter((r) => r.status === 'PROVEN').map((r) => r.id),
      failed: required.filter((r) => r.status === 'FAILED').map((r) => r.id),
      notCovered: required.filter((r) => r.status === 'NOT_COVERED').map((r) => r.id),
      coverageRatio: required.length
        ? required.filter((r) => r.status === 'PROVEN').length / required.length
        : 1,
      /** التغطية الكاملة شرط ضروري لـ PASS — مش تحسين اختياري. */
      complete: required.every((r) => r.status === 'PROVEN'),
    };
  }
}

/** يدعم المطابقة الحرفية أو بادئة بـ * (مثل "cross-system:*"). */
function toMatcher(pattern) {
  if (pattern.endsWith('*')) {
    const p = pattern.slice(0, -1);
    return (n) => n.startsWith(p);
  }
  return (n) => n === pattern;
}

module.exports = { AcOracle };
