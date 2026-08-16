'use strict';

/**
 * إعدادات البيئة — §14: لا شيء من قيم dev مكتوب في الإطار نفسه.
 * كل قيمة قابلة للتجاوز عبر متغير بيئة.
 */

function required(name, fallback) {
  const v = process.env[name] ?? fallback;
  if (v === undefined || v === null || v === '') {
    throw new Error(
      `متغير البيئة ${name} مطلوب ولم يُضبط. راجع .env.example`
    );
  }
  return v;
}

const env = {
  baseUrl: (process.env.QC_BASE_URL || 'https://qcdev.ihorizons.com').replace(/\/+$/, ''),
  user: process.env.QC_USER || 'test@liferay.com',
  get pass() { return required('QC_PASS'); },

  /** groupId للموقع. site-scoped — إلزامي لكل قراءة صفوف. */
  groupId: process.env.QC_GROUP_ID || '37246',
  siteErc: process.env.QC_SITE_ERC || 'QCDEMO-SITE-qatar-chamber',
  sitePath: process.env.QC_SITE_PATH || '/qatar-chamber',

  defaultLocale: process.env.QC_DEFAULT_LOCALE || 'en_US',
  locales: (process.env.QC_LOCALES || 'en_US,ar_SA').split(',').map((s) => s.trim()),

  /** بادئة بيانات التست — أي صف بيبدأ بيها ملك للـ QA ويتمسح. */
  testPrefix: process.env.QC_TEST_PREFIX || 'QCTEST-',

  /** مهلة انتظار انتشار التغيير من الـ CMS للموقع (cache + reindex). */
  propagationTimeoutMs: Number(process.env.QC_PROPAGATION_TIMEOUT_MS || 30000),
  propagationIntervalMs: Number(process.env.QC_PROPAGATION_INTERVAL_MS || 1500),

  /** سقف pageSize على object-definitions — 99+ يرجع 404 وهمي. */
  objectDefsPageSize: Number(process.env.QC_OBJECT_DEFS_PAGE_SIZE || 50),

  runsDir: process.env.QC_RUNS_DIR || 'runs',

  /**
   * وضع الأمان: يمنع أي تعديل على صف لا يحمل بادئة التست.
   * شغّله على البيئات المشتركة. اطفيه فقط بقرار واعٍ.
   */
  strictFixtureIsolation: process.env.QC_STRICT_ISOLATION !== 'false',
};

module.exports = env;
