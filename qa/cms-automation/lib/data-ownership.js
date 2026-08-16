'use strict';

/**
 * Phase 0 — التحكم في البيانات والبيئة.
 *
 * كل تست لازم يعلن ملكية بياناته **قبل** ما يشتغل. الإعلان ده
 * بيحدد استراتيجية التنظيف، ومن غيره مفيش تنظيف صحيح ممكن.
 *
 * التصنيفات الثلاثة:
 *
 *  DISPOSABLE      التست بينشئ الصف بنفسه ببادئة التست.
 *                  التنظيف = حذف. مفيش استرجاع. الأأمن — الافتراضي.
 *
 *  TEST_OWNED      صف موجود مُخصَّص للـ QA بالاتفاق (مش بيلمسه محرر).
 *                  التنظيف = استرجاع الحالة السابقة.
 *
 *  SNAPSHOT_RESTORE صف إنتاجي/تحريري حقيقي لازم التست يلمسه.
 *                  يتطلب تصريح صريح + سبب + قابلية تراجع مؤكدة.
 *                  لو التعديل غير قابل للتراجع → مرفوض.
 */

const OWNERSHIP = {
  DISPOSABLE: 'DISPOSABLE',
  TEST_OWNED: 'TEST_OWNED',
  SNAPSHOT_RESTORE: 'SNAPSHOT_RESTORE',
};

/**
 * تصنيف التعديل — الفجوة رقم 5، بالصيغة اللي اتفقنا عليها.
 *
 *  REVERSIBLE   يمكن إرجاعه بـ PUT للحالة السابقة
 *  DISPOSABLE   لا يحتاج إرجاع — الصف نفسه بيتحذف
 *  PROHIBITED   المنصة لا تسمح بالتراجع → ممنوع أثناء الأتمتة
 */
const MUTATION = {
  REVERSIBLE: 'REVERSIBLE',
  DISPOSABLE: 'DISPOSABLE',
  PROHIBITED: 'PROHIBITED',
};

const env = require('./env-shim');
const { irreversibleFields } = require('./objects');
const { isFixture } = require('./erc');

/**
 * يصنّف تعديلاً مقترحاً قبل تنفيذه.
 *
 * القاعدة الحاكمة: عدم قابلية التراجع تبقى غير ضارّة **فقط** لو
 * الصف disposable (هيتحذف بالكامل بعدين). على صف موجود، نفس
 * التعديل يبقى PROHIBITED.
 */
function classifyMutation(objectDef, erc, patch, { ownership } = {}) {
  const own = ownership || (isFixture(erc) ? OWNERSHIP.DISPOSABLE : OWNERSHIP.SNAPSHOT_RESTORE);

  const risky = irreversibleFields(objectDef).filter((f) => f.name in (patch || {}));
  const reasons = risky.map((f) => ({
    field: f.name,
    type: f.businessType === 'Attachment' ? 'ATTACHMENT' : 'REQUIRED_BOOLEAN',
    detail:
      f.businessType === 'Attachment'
        ? 'الاسترجاع يعيد معرّف الملف لا الملف؛ الرفع multipart'
        : 'Boolean بـ required:true — المنصة ترفض إرجاعه إلى false (400)',
  }));

  if (own === OWNERSHIP.DISPOSABLE) {
    return {
      ownership: own,
      mutation: MUTATION.DISPOSABLE,
      allowed: true,
      cleanup: 'DELETE',
      reasons,
      note: risky.length
        ? 'حقول غير قابلة للتراجع موجودة، لكن الصف disposable — الحذف يغطّيها'
        : undefined,
    };
  }

  if (risky.length) {
    return {
      ownership: own,
      mutation: MUTATION.PROHIBITED,
      allowed: false,
      cleanup: 'NONE',
      reasons,
      note:
        'تعديل غير قابل للتراجع على صف غير disposable. أعد تصميم التست ليستخدم صف تست، ' +
        'أو صعّد لاسترجاع DB — وهو إجراء طوارئ لا جزء من مسار التست.',
    };
  }

  return {
    ownership: own,
    mutation: MUTATION.REVERSIBLE,
    allowed: true,
    cleanup: 'RESTORE',
    reasons: [],
  };
}

/**
 * إعلان بيانات السيناريو. الـ orchestrator بيطلبه قبل التنفيذ.
 * سيناريو بدون إعلان = BLOCKED، مش PASS بالصدفة.
 */
function declareDataPlan(scenarioId, items = []) {
  if (!items.length) {
    return { scenarioId, valid: false, error: 'إعلان البيانات فارغ — كل سيناريو يجب أن يعلن ملكية بياناته' };
  }
  const invalid = items.filter((i) => !OWNERSHIP[i.ownership]);
  if (invalid.length) {
    return { scenarioId, valid: false, error: `ownership غير صالح: ${invalid.map((i) => i.ownership).join(', ')}` };
  }
  const needsAuth = items.filter((i) => i.ownership === OWNERSHIP.SNAPSHOT_RESTORE && !i.reason);
  if (needsAuth.length) {
    return {
      scenarioId, valid: false,
      error: `SNAPSHOT_RESTORE يتطلب reason صريحاً: ${needsAuth.map((i) => i.erc || i.name).join(', ')}`,
    };
  }
  return {
    scenarioId, valid: true, items,
    summary: {
      disposable: items.filter((i) => i.ownership === OWNERSHIP.DISPOSABLE).length,
      testOwned: items.filter((i) => i.ownership === OWNERSHIP.TEST_OWNED).length,
      snapshotRestore: items.filter((i) => i.ownership === OWNERSHIP.SNAPSHOT_RESTORE).length,
    },
  };
}

module.exports = { OWNERSHIP, MUTATION, classifyMutation, declareDataPlan };
