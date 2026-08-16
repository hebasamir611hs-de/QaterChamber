'use strict';

/**
 * طبقة التطبيع — الفجوة رقم 1 في وثيقة التسليم.
 *
 * §11 بيفترض `CMS value == rendered value`. ده غلط عملياً: الـ fragment
 * بيحوّل القيمة قبل ما يعرضها. المقارنة الخام بتنتج false failures
 * أكتر من الأعطال الحقيقية، وبعد كام مرة الفريق بيبطّل يصدّق السويت.
 *
 * كل دالة هنا بتعالج تحويل موثّق واحد.
 */

/* ------------------------- تطبيع مفاتيح اللغة ------------------------- */

/**
 * §5.7 — صيغة مفتاح اللغة بتختلف بين الـ APIs:
 * list-type-entries بيستخدم en-US، و object-admin بيستخدم en_US.
 */
const localeUnderscore = (l) => String(l).replace('-', '_');
const localeHyphen = (l) => String(l).replace('_', '-');

/** يقرأ قيمة مترجمة مهما كانت صيغة المفتاح. */
function pickLocalized(i18nMap, locale) {
  if (!i18nMap) return undefined;
  if (typeof i18nMap === 'string') return i18nMap;
  return i18nMap[locale] ?? i18nMap[localeUnderscore(locale)] ?? i18nMap[localeHyphen(locale)];
}

/* --------------------------- تطبيع النصوص --------------------------- */

const stripHtml = (s) =>
  String(s ?? '')
    .replace(/<br\s*\/?>/gi, ' ')
    .replace(/<\/(p|div|li|h[1-6])>/gi, ' ')
    .replace(/<[^>]+>/g, '')
    .replace(/&nbsp;/gi, ' ')
    .replace(/&amp;/gi, '&')
    .replace(/&lt;/gi, '<')
    .replace(/&gt;/gi, '>')
    .replace(/&quot;/gi, '"')
    .replace(/&#(\d+);/g, (_, d) => String.fromCharCode(Number(d)));

/** مسافات متعددة/غير قياسية → مسافة واحدة. NBSP و RTL marks متضمّنة. */
const collapseWs = (s) =>
  String(s ?? '')
    .replace(/[   ]/g, ' ')
    .replace(/[‎‏؜​]/g, '') // علامات اتجاه غير مرئية
    .replace(/\s+/g, ' ')
    .trim();

/**
 * الأرقام العربية-الهندية → ASCII.
 * الموقع ممكن يعرض ١٩٦٣ والـ CMS مخزّن 1963 — نفس القيمة، مقارنة فاشلة.
 */
const arabicDigits = '٠١٢٣٤٥٦٧٨٩';
const easternDigits = '۰۱۲۳۴۵۶۷۸۹';
const normalizeDigits = (s) =>
  String(s ?? '').replace(/[٠-٩۰-۹]/g, (d) => {
    const i = arabicDigits.indexOf(d);
    return String(i >= 0 ? i : easternDigits.indexOf(d));
  });

/** تطبيع أشكال الحروف العربية اللي بتختلف بالإدخال بدون فرق دلالي. */
const normalizeArabic = (s) =>
  String(s ?? '')
    .replace(/[ـ]/g, '')          // تطويل
    .replace(/[ً-ْ]/g, '')   // تشكيل
    .replace(/[أإآ]/g, 'ا')
    .replace(/ى/g, 'ي')
    .replace(/ة/g, 'ه');

/**
 * التطبيع القياسي لمقارنة نص CMS بنص معروض.
 * strictArabic=true بيوقف تطبيع شكل الحروف (لتستات الإملاء الدقيق).
 */
function normalizeText(s, { strictArabic = false } = {}) {
  let out = collapseWs(stripHtml(s));
  out = normalizeDigits(out);
  if (!strictArabic) out = normalizeArabic(out);
  return out;
}

/* ------------------------- المقارنة مع الاقتطاع ------------------------- */

const ELLIPSIS = /(\.\.\.|…|…)\s*$/;

/**
 * الـ cards بتقتطع العناوين الطويلة. المقارنة الخام هتفشل رغم إن
 * المعروض صحيح. الدالة دي بتتعامل مع الاقتطاع كتطابق مقبول
 * ما دام البادئة مطابقة.
 */
function textMatches(cmsValue, renderedValue, opts = {}) {
  const a = normalizeText(cmsValue, opts);
  const b = normalizeText(renderedValue, opts);

  if (a === b) return { match: true, mode: 'exact' };

  if (ELLIPSIS.test(b)) {
    const stem = b.replace(ELLIPSIS, '').trim();
    if (stem.length >= 8 && a.startsWith(stem)) {
      return { match: true, mode: 'truncated', renderedStem: stem };
    }
  }
  if (opts.allowContains && a.includes(b) && b.length >= 8) {
    return { match: true, mode: 'contains' };
  }
  return {
    match: false, mode: 'mismatch',
    expected: a, actual: b,
    firstDiffAt: firstDiff(a, b),
  };
}

function firstDiff(a, b) {
  const n = Math.min(a.length, b.length);
  for (let i = 0; i < n; i++) if (a[i] !== b[i]) return i;
  return a.length === b.length ? -1 : n;
}

/* ---------------------------- علامات الترجمة ---------------------------- */

/**
 * §12 — البيانات الحية فيها ثلاث حالات للحقل العربي:
 *   real          ترجمة حقيقية
 *   pending       "English text (AR)" — علامة موثّقة، مش باج
 *   corrupt       "?" حرفياً (6 حقول مؤكدة)
 *   empty
 *
 * §9 بيقول: متفشلش تست عام بسبب علامة (AR) المقصودة.
 */
function classifyArabic(value) {
  const raw = String(value ?? '').trim();
  if (!raw) return 'empty';
  if (/^\?+$/.test(raw)) return 'corrupt';
  if (/\(AR\)\s*$/i.test(raw)) return 'pending';
  if (/[؀-ۿ]/.test(raw)) return 'real';
  return 'pending'; // لاتيني بدون علامة = برضه مش مترجم
}

const hasRealArabic = (v) => classifyArabic(v) === 'real';

/* ------------------------------ التواريخ ------------------------------ */

/**
 * التخزين UTC، العرض بتوقيت الشركة (Asia/Qatar). مقارنة السلاسل الخام
 * هتفشل دايماً. بنقارن اللحظة الزمنية نفسها.
 */
function sameInstant(cmsIso, renderedIso, toleranceMs = 60000) {
  const a = new Date(cmsIso).getTime();
  const b = new Date(renderedIso).getTime();
  if (Number.isNaN(a) || Number.isNaN(b)) return { match: false, reason: 'تاريخ غير صالح' };
  return { match: Math.abs(a - b) <= toleranceMs, deltaMs: Math.abs(a - b) };
}

/** تنسيق التاريخ بتوقيت العرض — لمقارنة نص التاريخ المعروض. */
function formatInZone(iso, zone = 'Asia/Qatar', locale = 'en-GB') {
  return new Intl.DateTimeFormat(locale, {
    timeZone: zone, year: 'numeric', month: '2-digit', day: '2-digit',
  }).format(new Date(iso));
}

module.exports = {
  localeUnderscore, localeHyphen, pickLocalized,
  stripHtml, collapseWs, normalizeDigits, normalizeArabic, normalizeText,
  textMatches, classifyArabic, hasRealArabic,
  sameInstant, formatInZone,
};
