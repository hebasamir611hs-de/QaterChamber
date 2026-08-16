'use strict';

/**
 * Web QA Specialist — العقد فقط (§3.3).
 *
 * التنفيذ الفعلي بيتعمل في repo الـ Playwright الموجود عندكم.
 * الملف ده بيعرّف الواجهة اللي الـ orchestrator بيعتمد عليها، عشان
 * الجانبين يتطوّروا مستقلين.
 *
 * المسؤولية الحرجة هنا: **الانتظار للانتشار** جوّه الـ Web specialist.
 * الـ orchestrator مش بيعمل sleep ولا بينتظر — بيسأل الـ specialist
 * "هل ظهر؟" والـ specialist بيـ poll لحد المهلة.
 */

const { stepResult, assertion } = require('../lib/result');
const { waitFor, PropagationTimeout } = require('../lib/propagation');

/**
 * القاعدة اللي كل adapter لازم يلتزم بيها.
 * أي تنفيذ لازم يرجّع stepResult ومايرميش استثناء للـ orchestrator.
 */
class WebSpecialistContract {
  /** @returns {Promise<import('../lib/result')>} */
  async verifyRendered(/* { stepId, url, locate, expected, acIds } */) {
    throw new Error('غير منفَّذ — اربط adapter الـ Playwright بتاعكم');
  }
  async verifyLocale(/* { stepId, url, locale, expected, acIds } */) {
    throw new Error('غير منفَّذ');
  }
  async captureEvidence(/* { stepId, url } */) {
    throw new Error('غير منفَّذ');
  }
}

/**
 * Adapter جاهز للربط بـ Playwright.
 *
 * بيستقبل `page` (Playwright Page) ودوال تحديد العناصر، وبيتكفّل
 * بالباقي: الـ polling، التقاط الأدلة، وتغليف النتيجة.
 *
 * مثال الربط:
 *   const web = new PlaywrightWebSpecialist({
 *     page,
 *     baseUrl: 'https://qcdev.ihorizons.com',
 *     screenshot: async (name) => page.screenshot({ path: `evidence/${name}.png` }),
 *   });
 */
class PlaywrightWebSpecialist extends WebSpecialistContract {
  constructor({ page, baseUrl, screenshot = null }) {
    super();
    if (!page) throw new Error('PlaywrightWebSpecialist: page مطلوب');
    this.page = page;
    this.baseUrl = (baseUrl || '').replace(/\/+$/, '');
    this._screenshot = screenshot;
  }

  async _step(stepId, meta, fn) {
    const t0 = Date.now();
    try {
      const out = await fn();
      const failed = (out.assertions || []).filter((a) => !a.passed);
      return stepResult({
        stepId, specialist: 'web', ...meta, ...out,
        status: failed.length ? 'FAIL' : 'PASS',
        timings: { ms: Date.now() - t0 },
      });
    } catch (e) {
      return stepResult({
        stepId, specialist: 'web', ...meta,
        // انتهاء مهلة الانتشار = BLOCKED مش FAIL:
        // مش مثبت إن ده عيب عرض، ممكن يكون بطء بيئة.
        status: e instanceof PropagationTimeout ? 'BLOCKED' : 'FAIL',
        error: e, evidence: ['exception'],
        timings: { ms: Date.now() - t0 },
      });
    }
  }

  /**
   * بيفتح الصفحة ويـ poll لحد ما المحدِّد يظهر بالنص المتوقع.
   * ما بيقارنش القيم — بيرجّع المعروض والـ orchestrator بيقارن
   * عبر عقد التطبيع (فصل مقصود: الـ specialist بيلاحظ، والـ
   * orchestrator بيحكم).
   */
  async verifyRendered({ stepId, url, selector, expectedText = null, acIds = [], timeoutMs, reloadEachPoll = true }) {
    return this._step(stepId, { action: 'verifyRendered', url, acIds }, async () => {
      const full = url.startsWith('http') ? url : this.baseUrl + url;
      let observedText = null;

      const { waitedMs, attempts } = await waitFor(
        `${selector} على ${url}`,
        async () => {
          if (reloadEachPoll) await this.page.goto(full, { waitUntil: 'domcontentloaded' });
          const el = await this.page.$(selector);
          if (!el) return { ok: false, observed: 'العنصر غير موجود' };
          observedText = (await el.textContent())?.trim() ?? '';
          if (expectedText === null) return { ok: !!observedText, observed: observedText };
          // مطابقة فضفاضة للـ polling فقط؛ الحكم الدقيق للـ orchestrator
          const norm = (s) => String(s).replace(/\s+/g, ' ').trim().toLowerCase();
          return norm(observedText).includes(norm(expectedText).slice(0, 20))
            ? { ok: true, observed: observedText }
            : { ok: false, observed: observedText };
        },
        { timeoutMs }
      );

      const evidence = ['dom-assertion'];
      if (this._screenshot) { await this._screenshot(`${stepId}`); evidence.push('screenshot'); }

      return {
        observed: { text: observedText, selector, waitedMs, attempts },
        assertions: [assertion('rendered-visible', true, { selector, waitedMs })],
        evidence,
      };
    });
  }

  /** تبديل اللغة + التحقق من اتجاه الصفحة. */
  async verifyLocale({ stepId, url, locale = 'ar_SA', selector, acIds = [], timeoutMs }) {
    return this._step(stepId, { action: 'verifyLocale', url, acIds }, async () => {
      const lang = locale.replace('_', '-').toLowerCase();
      const localized = url.replace(/^\//, `/${lang.split('-')[0]}/`);
      const full = (localized.startsWith('http') ? localized : this.baseUrl + localized);

      await this.page.goto(full, { waitUntil: 'domcontentloaded' });
      const dir = await this.page.getAttribute('html', 'dir');
      const htmlLang = await this.page.getAttribute('html', 'lang');

      let text = null;
      if (selector) {
        const { value } = await waitFor(`${selector}@${locale}`, async () => {
          const el = await this.page.$(selector);
          if (!el) return { ok: false, observed: 'غير موجود' };
          text = (await el.textContent())?.trim();
          return text ? { ok: true, value: text } : { ok: false, observed: '' };
        }, { timeoutMs });
        text = value;
      }

      const rtlExpected = /^ar/i.test(locale);
      const evidence = ['dom-assertion'];
      if (this._screenshot) { await this._screenshot(`${stepId}-${lang}`); evidence.push('screenshot'); }

      return {
        observed: { dir, lang: htmlLang, text, url: full },
        assertions: [
          assertion(`locale-direction:${locale}`, rtlExpected ? dir === 'rtl' : dir !== 'rtl',
            { expected: rtlExpected ? 'rtl' : 'ltr', actual: dir }),
          assertion(`locale-lang:${locale}`, !!htmlLang && htmlLang.toLowerCase().startsWith(lang.split('-')[0]),
            { expected: lang, actual: htmlLang }),
        ],
        evidence,
      };
    });
  }

  async captureEvidence({ stepId, url }) {
    return this._step(stepId, { action: 'captureEvidence', url }, async () => {
      if (url) await this.page.goto(url.startsWith('http') ? url : this.baseUrl + url);
      const evidence = [];
      if (this._screenshot) { await this._screenshot(stepId); evidence.push('screenshot'); }
      return { observed: { url }, assertions: [], evidence };
    });
  }
}

module.exports = { WebSpecialistContract, PlaywrightWebSpecialist };
