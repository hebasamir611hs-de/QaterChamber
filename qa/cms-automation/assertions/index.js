'use strict';

/**
 * مكتبة تأكيدات CMS — §10.
 *
 * كل دالة بترجع { name, passed, ... } — مش بترمي استثناء.
 * السبب: الخطوة الواحدة ممكن تجمع تأكيدات كتير، وعايزين نشوفها كلها
 * مش أول واحد بيفشل. الحكم بيتجمّع في stepResult.
 */

const N = require('../lib/normalize');
const { assertion } = require('../lib/result');
const { getField } = require('../lib/objects');

/* ------------------------------ المحتوى ------------------------------ */

const fieldExists = (objectDef, fieldName) =>
  assertion(`field-exists:${fieldName}`, !!getField(objectDef, fieldName), {
    detail: getField(objectDef, fieldName) ? undefined : `الحقل غير معرّف على ${objectDef.name}`,
  });

function fieldEquals(entry, fieldName, expected, opts = {}) {
  const actual = entry?.[fieldName];
  const r = N.textMatches(expected, actual, opts);
  return assertion(`field-equals:${fieldName}`, r.match, {
    expected, actual, mode: r.mode,
    detail: r.match ? undefined : `اختلاف عند الحرف ${r.firstDiffAt}`,
  });
}

/** حقل localized: القيمة جوّه خريطة i18n بمفتاح اللغة. */
function localizedEquals(entry, fieldName, locale, expected, opts = {}) {
  const map = entry?.[`${fieldName}_i18n`] ?? entry?.[fieldName];
  const actual = N.pickLocalized(map, locale);
  const r = N.textMatches(expected, actual, opts);
  return assertion(`localized-equals:${fieldName}@${locale}`, r.match, {
    expected, actual, mode: r.mode,
  });
}

const richTextNotEmpty = (entry, fieldName) => {
  const v = N.normalizeText(entry?.[fieldName]);
  return assertion(`rich-text-not-empty:${fieldName}`, v.length > 0, { length: v.length });
};

const attachmentExists = (entry, fieldName) => {
  const v = entry?.[fieldName];
  const ok = !!(v && (v.id || v.link || (typeof v === 'number' && v > 0)));
  return assertion(`attachment-exists:${fieldName}`, ok, { value: v ?? null });
};

/* ------------------------------- الحالة ------------------------------- */

const isActive = (entry, fieldName = 'activeStatus', expected = true) =>
  assertion(`state-active:${fieldName}`, entry?.[fieldName] === expected, {
    expected, actual: entry?.[fieldName] ?? null,
  });

/** نافذة النشر: يظهر فقط بين startDate و endDate لو موجودين. */
function withinSchedule(entry, at = new Date()) {
  const s = entry?.startDate ? new Date(entry.startDate) : null;
  const e = entry?.endDate ? new Date(entry.endDate) : null;
  const t = at.getTime();
  const ok = (!s || t >= s.getTime()) && (!e || t <= e.getTime());
  return assertion('state-within-schedule', ok, {
    startDate: entry?.startDate ?? null, endDate: entry?.endDate ?? null, at: at.toISOString(),
  });
}

/* ------------------------------ الترتيب ------------------------------ */

/**
 * §10 — العرف التحريري: مضاعفات 100.
 * ده عُرف مش قيد على مستوى المنصة، فبيرجع تحذير مش فشل ما لم
 * يُطلب strict.
 */
function displayOrderValid(entry, fieldName = 'displayOrder', { strictHundreds = false } = {}) {
  const v = entry?.[fieldName];
  const positive = Number.isInteger(v) && v > 0;
  const hundreds = positive && v % 100 === 0;
  return assertion(`ordering-valid:${fieldName}`, strictHundreds ? hundreds : positive, {
    value: v ?? null,
    warning: positive && !hundreds
      ? `${v} ليس من مضاعفات 100 — يخالف العرف التحريري (Content-Admin-Guide §0)`
      : undefined,
  });
}

/** الترتيب المعروض مطابق لترتيب displayOrder التصاعدي. */
function orderMatches(entries, renderedKeys, { keyField = 'externalReferenceCode', orderField = 'displayOrder' } = {}) {
  const expected = [...entries]
    .filter((e) => renderedKeys.includes(e[keyField]))
    .sort((a, b) => (a[orderField] ?? 0) - (b[orderField] ?? 0))
    .map((e) => e[keyField]);
  const ok = expected.length === renderedKeys.length && expected.every((k, i) => k === renderedKeys[i]);
  return assertion('ordering-matches-rendered', ok, { expected, actual: renderedKeys });
}

/* ----------------------------- العلاقات ----------------------------- */

/**
 * §10 / §16.F — لا نفترض علاقة لمجرد تشابه بادئة الـ story.
 * الدالة بتتحقق من العلاقة المعرّفة فعلاً في الـ metadata.
 */
function relationshipSet(objectDef, entry, relationshipFieldName) {
  const declared = objectDef.fields.some((f) => f.name === relationshipFieldName && f.businessType === 'Relationship');
  if (!declared) {
    return assertion(`relationship-set:${relationshipFieldName}`, false, {
      detail: `${relationshipFieldName} غير معرّف كعلاقة على ${objectDef.name} — ` +
              `لا تفترض علاقة من تشابه البادئة (§16.F)`,
      blocking: true,
    });
  }
  const v = entry?.[relationshipFieldName];
  return assertion(`relationship-set:${relationshipFieldName}`, !!v && v !== 0, { value: v ?? null });
}

/** الغلطة الأشهر في الفوتر: رابط بدون عمود أب لا يظهر حتى لو active. */
const footerLinkHasColumn = (entry) =>
  relationshipSetRaw(entry, 'r_footerNavColumnLinks_c_footerNavigationColumnId',
    'رابط فوتر بدون عمود أب لن يظهر إطلاقاً حتى لو active=true');

function relationshipSetRaw(entry, field, hint) {
  const v = entry?.[field];
  return assertion(`relationship-set:${field}`, !!v && v !== 0, { value: v ?? null, detail: hint });
}

/* ----------------------------- التوطين ----------------------------- */

/**
 * §9/§12 — ثلاث نتائج ممكنة: real | pending | corrupt | empty.
 *
 * expect='real'    التست بيطلب ترجمة حقيقية → pending يفشل
 * expect='present' أي قيمة مقبولة ما عدا corrupt/empty (الافتراضي)
 *
 * القاعدة: متفشلش تست عام بسبب علامة (AR) المقصودة.
 */
function arabicContent(entry, fieldName, { expect = 'present', locale = 'ar_SA' } = {}) {
  const map = entry?.[`${fieldName}_i18n`] ?? entry?.[fieldName];
  const value = N.pickLocalized(map, locale) ?? entry?.[fieldName];
  const kind = N.classifyArabic(value);

  const passed = expect === 'real' ? kind === 'real' : kind === 'real' || kind === 'pending';

  return assertion(`arabic:${fieldName}`, passed, {
    kind, value: value ?? null, expect,
    detail:
      kind === 'corrupt' ? 'القيمة "?" حرفياً — تلف بيانات موثّق (liferay-context §12)'
      : kind === 'pending' && expect === 'real' ? 'علامة ترجمة معلّقة "(AR)" — لكن السيناريو يطلب ترجمة حقيقية'
      : kind === 'pending' ? 'علامة ترجمة معلّقة مقبولة في هذا السياق'
      : undefined,
  });
}

/** كلا اللغتين مملوءتان — قاعدة "املأ اللغتين" في دليل المحرر. */
function bothLocalesFilled(entry, fieldName, { requireRealArabic = false } = {}) {
  const en = N.pickLocalized(entry?.[`${fieldName}_i18n`] ?? entry?.[fieldName], 'en_US');
  const ar = arabicContent(entry, fieldName, { expect: requireRealArabic ? 'real' : 'present' });
  const enOk = !!N.normalizeText(en);
  return assertion(`bilingual:${fieldName}`, enOk && ar.passed, {
    en: en ?? null, arKind: ar.kind,
    detail: !enOk ? 'الإنجليزية فارغة' : !ar.passed ? ar.detail : undefined,
  });
}

/* ------------------- قواعد التحقق من الـ metadata ------------------- */

/**
 * §10 — نحمّل قواعد التحقق من الـ Object metadata بدل تكرار مئات
 * القواعد يدوياً. بنرجّعها كتقرير للـ orchestrator يقرر.
 */
const validationRules = (objectDef) =>
  assertion(`validation-rules-loaded:${objectDef.name}`, true, {
    count: objectDef.validationRules.length,
    rules: objectDef.validationRules.map((r) => r.name),
  });

/* ------------------------- المقارنة عبر الأنظمة ------------------------- */

/**
 * تأكيد CMS ↔ Web. مش مقارنة نصية خام (§11 كان بيفترض كده).
 * بيمر بطبقة التطبيع ويقبل الاقتطاع كتطابق مشروع.
 */
function crossSystemText(cmsValue, renderedValue, label, opts = {}) {
  const r = N.textMatches(cmsValue, renderedValue, opts);
  return assertion(`cross-system:${label}`, r.match, {
    cms: cmsValue, rendered: renderedValue, mode: r.mode,
    detail: r.match
      ? (r.mode !== 'exact' ? `تطابق عبر "${r.mode}" — الـ fragment حوّل القيمة` : undefined)
      : `اختلاف عند الحرف ${r.firstDiffAt}`,
  });
}

const crossSystemDate = (cmsIso, renderedIso, label, toleranceMs) => {
  const r = N.sameInstant(cmsIso, renderedIso, toleranceMs);
  return assertion(`cross-system-date:${label}`, r.match, { cms: cmsIso, rendered: renderedIso, deltaMs: r.deltaMs });
};

module.exports = {
  fieldExists, fieldEquals, localizedEquals, richTextNotEmpty, attachmentExists,
  isActive, withinSchedule,
  displayOrderValid, orderMatches,
  relationshipSet, footerLinkHasColumn,
  arabicContent, bothLocalesFilled,
  validationRules,
  crossSystemText, crossSystemDate,
};
