'use strict';

/**
 * Normalization Contracts — عقد تطبيع لكل نوع حقل.
 *
 * القاعدة: المقارنة بين قيمة الـ CMS والقيمة المعروضة **ممنوعة** بدون
 * عقد. كل عقد بيوثّق التحويلات المشروعة اللي الـ fragment بيعملها،
 * فالاختلاف الباقي بيبقى عيب حقيقي.
 *
 * العقد بيحدد أيضاً `strictness`:
 *   strict   لا يُسمح بأي تحويل عدا التطبيع القياسي
 *   lenient  يُسمح بالاقتطاع/الاحتواء (بطاقات، مقتطفات)
 */

const N = require('./normalize');

/* ------------------------------ العقود ------------------------------ */

const contracts = {
  /** نص عادي: عنوان، تسمية، اسم. */
  text: {
    id: 'text',
    allowedTransforms: ['whitespace-collapse', 'entity-decode', 'digit-normalize', 'arabic-form-normalize'],
    normalize: (v, o = {}) => N.normalizeText(v, o),
    compare: (cms, rendered, o = {}) => N.textMatches(cms, rendered, o),
  },

  /** نص غني: بيتخزّن HTML وبيتعرض منسّق — لازم strip. */
  richText: {
    id: 'richText',
    allowedTransforms: ['html-strip', 'whitespace-collapse', 'entity-decode', 'digit-normalize', 'truncation'],
    normalize: (v, o = {}) => N.normalizeText(v, o),
    compare: (cms, rendered, o = {}) =>
      N.textMatches(cms, rendered, { allowContains: true, ...o }),
    defaultStrictness: 'lenient',
  },

  /** نص مقتطع في البطاقات — الاقتطاع سلوك تصميم مش عيب. */
  excerpt: {
    id: 'excerpt',
    allowedTransforms: ['html-strip', 'truncation', 'ellipsis', 'whitespace-collapse'],
    normalize: (v, o = {}) => N.normalizeText(v, o),
    compare: (cms, rendered, o = {}) => N.textMatches(cms, rendered, { allowContains: true, ...o }),
    defaultStrictness: 'lenient',
  },

  /**
   * تاريخ/وقت: التخزين UTC، العرض بتوقيت الشركة.
   * المقارنة على اللحظة الزمنية، مش على السلسلة.
   */
  dateTime: {
    id: 'dateTime',
    allowedTransforms: ['timezone-shift', 'locale-format'],
    normalize: (v) => (v ? new Date(v).toISOString() : null),
    compare: (cms, rendered, o = {}) => {
      const direct = N.sameInstant(cms, rendered, o.toleranceMs ?? 60000);
      if (direct.match) return { match: true, mode: 'instant' };
      // المعروض قد يكون تاريخاً منسّقاً (15/08/2026) مش ISO
      const zone = o.displayZone || 'Asia/Qatar';
      for (const loc of ['en-GB', 'ar-EG', 'en-US']) {
        try {
          if (N.formatInZone(cms, zone, loc) === String(rendered).trim())
            return { match: true, mode: `formatted:${loc}@${zone}` };
        } catch { /* تنسيق غير مدعوم */ }
      }
      return { match: false, mode: 'mismatch', expected: cms, actual: rendered, deltaMs: direct.deltaMs };
    },
  },

  /** رقم: فواصل آلاف، أرقام عربية، لواحق مثل "+". */
  number: {
    id: 'number',
    allowedTransforms: ['digit-normalize', 'thousands-separator', 'suffix'],
    normalize: (v) => {
      const s = N.normalizeDigits(String(v ?? '')).replace(/[,٬\s]/g, '');
      const m = s.match(/-?\d+(\.\d+)?/);
      return m ? Number(m[0]) : null;
    },
    compare(cms, rendered, o = {}) {
      const a = this.normalize(cms), b = this.normalize(rendered);
      if (a === null || b === null) return { match: false, mode: 'unparseable', expected: cms, actual: rendered };
      const tol = o.tolerance ?? 0;
      return { match: Math.abs(a - b) <= tol, mode: 'numeric', expected: a, actual: b };
    },
  },

  /** رابط: نسبي مقابل مطلق، شرطة أخيرة، بارامترات تتبّع. */
  url: {
    id: 'url',
    allowedTransforms: ['relative-to-absolute', 'trailing-slash', 'tracking-params'],
    normalize: (v, o = {}) => {
      let s = String(v ?? '').trim();
      if (!s) return '';
      try {
        const u = new URL(s, o.baseUrl || 'https://placeholder.invalid');
        for (const p of [...u.searchParams.keys()])
          if (/^(utm_|fbclid|gclid)/i.test(p)) u.searchParams.delete(p);
        let path = u.pathname.replace(/\/+$/, '') || '/';
        return (o.compareHost ? u.host : '') + path + (u.search || '');
      } catch { return s.replace(/\/+$/, ''); }
    },
    compare(cms, rendered, o = {}) {
      const a = this.normalize(cms, o), b = this.normalize(rendered, o);
      return { match: a === b, mode: 'url', expected: a, actual: b };
    },
  },

  /** منطقي: "نعم/لا"، "Yes/No"، checkbox. */
  boolean: {
    id: 'boolean',
    allowedTransforms: ['label-mapping'],
    normalize: (v) => {
      if (typeof v === 'boolean') return v;
      const s = String(v ?? '').trim().toLowerCase();
      if (['true', 'yes', '1', 'on', 'نعم', 'مفعل'].includes(s)) return true;
      if (['false', 'no', '0', 'off', 'لا', 'معطل'].includes(s)) return false;
      return null;
    },
    compare(cms, rendered) {
      const a = this.normalize(cms), b = this.normalize(rendered);
      return { match: a !== null && a === b, mode: 'boolean', expected: a, actual: b };
    },
  },

  /** مرفق: المقارنة على اسم الملف مش الـ id — الـ id مبيظهرش في الـ DOM. */
  attachment: {
    id: 'attachment',
    allowedTransforms: ['id-to-url', 'cdn-prefix', 'resize-params'],
    normalize: (v) => {
      if (!v) return null;
      const s = typeof v === 'object' ? (v.link?.href || v.contentUrl || v.name || '') : String(v);
      const file = String(s).split('?')[0].split('/').pop() || '';
      return file.toLowerCase();
    },
    compare(cms, rendered) {
      const a = this.normalize(cms), b = this.normalize(rendered);
      return { match: !!a && !!b && (a === b || b.includes(a) || a.includes(b)), mode: 'filename', expected: a, actual: b };
    },
  },

  /**
   * قيمة مترجمة: بتقرأ من خريطة i18n بأي صيغة مفتاح، وبتحترم
   * تصنيف العربي (real/pending/corrupt) بدل ما تقارن نص خام.
   */
  localizedText: {
    id: 'localizedText',
    allowedTransforms: ['locale-key-normalize', 'whitespace-collapse', 'digit-normalize'],
    normalize: (v, o = {}) => N.normalizeText(N.pickLocalized(v, o.locale || 'en_US') ?? v, o),
    compare(cms, rendered, o = {}) {
      const locale = o.locale || 'en_US';
      const src = N.pickLocalized(cms, locale) ?? cms;
      if (/^ar/i.test(locale)) {
        const kind = N.classifyArabic(src);
        if (kind === 'corrupt')
          return { match: false, mode: 'source-corrupt', expected: src, actual: rendered,
                   detail: 'قيمة المصدر "?" — تلف بيانات موثّق، ليس عيب عرض' };
        if (kind === 'pending' && o.expect !== 'real')
          return { match: true, mode: 'pending-translation-skipped',
                   detail: 'المصدر يحمل علامة (AR) — تُتخطّى ما لم يطلب السيناريو ترجمة حقيقية' };
      }
      return N.textMatches(src, rendered, o);
    },
  },

  /** هوية: علاقات ومعرّفات — مقارنة صارمة بلا تحويل. */
  identity: {
    id: 'identity',
    allowedTransforms: [],
    normalize: (v) => (v === null || v === undefined ? null : String(v)),
    compare(cms, rendered) {
      const a = this.normalize(cms), b = this.normalize(rendered);
      return { match: a === b, mode: 'identity', expected: a, actual: b };
    },
  },
};

/* -------------------- الاشتقاق من الـ metadata -------------------- */

/**
 * businessType بتاع Liferay → عقد التطبيع.
 * الاشتقاق من الـ metadata مش من تخمين اسم الحقل، إلا في حالة
 * الروابط اللي بتتخزّن Text لكن دلالتها URL.
 */
function contractForField(field) {
  if (!field) return contracts.text;
  const { businessType, localized, name = '' } = field;

  if (/url|link|redirect|href/i.test(name) && ['Text', 'LongText'].includes(businessType))
    return contracts.url;

  switch (businessType) {
    case 'LongText':      return contracts.richText;
    case 'RichText':      return contracts.richText;
    case 'Date':
    case 'DateTime':      return contracts.dateTime;
    case 'Integer':
    case 'LongInteger':
    case 'Decimal':
    case 'PrecisionDecimal': return contracts.number;
    case 'Boolean':       return contracts.boolean;
    case 'Attachment':    return contracts.attachment;
    case 'Relationship':  return contracts.identity;
    case 'Picklist':      return contracts.text;
    case 'Text':
    default:              return localized ? contracts.localizedText : contracts.text;
  }
}

/**
 * المقارنة الرسمية. بترجع سجل كامل عشان يتحط في الـ evidence:
 * أي عقد اتستخدم، أي تحويلات مسموحة، والنتيجة.
 */
function compareWithContract(field, cmsValue, renderedValue, opts = {}) {
  const contract = opts.contract ? contracts[opts.contract] : contractForField(field);
  if (!contract) throw new Error(`عقد تطبيع غير معروف: ${opts.contract}`);
  const r = contract.compare(cmsValue, renderedValue, opts);
  return {
    contract: contract.id,
    allowedTransforms: contract.allowedTransforms,
    match: !!r.match,
    mode: r.mode,
    expected: r.expected ?? cmsValue,
    actual: r.actual ?? renderedValue,
    detail: r.detail,
    fieldName: field?.name,
    businessType: field?.businessType,
  };
}

module.exports = { contracts, contractForField, compareWithContract };
