#!/usr/bin/env node
'use strict';

/**
 * الشريحة الرأسية الأولى — NewsArticle.
 *
 * بتمشّي خط الأنابيب كامل على Object واحد قبل التوسّع للـ 111:
 *
 *   Phase 0 → AC Mapping → CMS → Web → Propagation → Normalization
 *   → Cross-System Oracle → AC Coverage → Cleanup Verification
 *
 * بدون Web specialist موصول، السيناريو بيرجع BLOCKED — **مش PASS**.
 * ده مقصود: §16.A بيحذّر من إعلان نجاح feature بناءً على نص التغطية.
 *
 *   node scenarios/news-article.slice.js
 */

const { CmsSpecialist } = require('../specialist/cms-specialist');
const { QaOrchestrator, printReport } = require('../orchestrator/qa-orchestrator');
const { OWNERSHIP } = require('../lib/data-ownership');
const { newRunId, fixtureErc } = require('../lib/erc');
const { get } = require('../lib/rest-client');
const { findObject } = require('../lib/objects');
const env = require('../config/env');

/**
 * يستعير مرجع مرفق من صف موجود.
 * NewsArticle بيطلب thumbnailImage (Attachment). عشان الشريحة تشتغل
 * من غير ما نرفع ملف multipart، بنستعير id ملف من أول خبر موجود.
 */
async function borrowThumbnail() {
  const o = await findObject('NewsArticle');
  const list = await get(`${o.restPath}/scopes/${env.groupId}?page=1&pageSize=1`);
  const t = list.items?.[0]?.thumbnailImage;
  const id = typeof t === 'object' ? t?.id : t;
  if (!id) throw new Error('لا يوجد خبر لأستعير منه thumbnail — أضف خبر يدوياً أولاً.');
  return id;
}

function buildScenario(runId) {
  const titleEn = `QA Slice ${runId}`;
  const titleAr = `شريحة اختبار ${runId}`;
  const fixtureName = 'slice-news';
  const erc = fixtureErc(runId, fixtureName);

  return {
    id: 'QC-SLICE-NEWS-01',
    title: 'خبر جديد في الـ CMS يظهر على الصفحة الرئيسية وصفحة التفاصيل بالعربي والإنجليزي',

    /* ── AC → Oracle: كل معيار بيعلن التأكيدات اللازمة لإثباته ── */
    acceptanceCriteria: [
      { id: 'AC-1', description: 'الخبر يُحفظ في الـ CMS باللغتين',
        requiredAssertions: ['mutation-persisted', 'bilingual:title'] },
      { id: 'AC-2', description: 'الخبر يظهر في بطاقة آخر الأخبار وصفحة التفاصيل',
        requiredAssertions: ['cross-system:homepage-title', 'cross-system:detail-title'] },
      { id: 'AC-3', description: 'النسخة العربية تُعرض بترجمة حقيقية واتجاه RTL',
        requiredAssertions: ['cross-system:arabic-title', 'locale-direction:ar_SA'] },
    ],

    /* ── Phase 0: إعلان ملكية البيانات ── */
    dataPlan: [
      { ownership: OWNERSHIP.DISPOSABLE, objectName: 'NewsArticle', name: fixtureName,
        note: 'صف تست ينشئه التست ويُحذف — لا يُلمس أي محتوى تحريري' },
    ],

    /* ── CMS Execution ── */
    async cms(ctx) {
      const steps = [];
      steps.push(await ctx.cms.describeObject('CMS-00', 'NewsArticle'));

      // NewsArticle بيطلب thumbnailImage — نستعير id من خبر موجود
      const thumbnailImage = await borrowThumbnail();

      const created = await ctx.cms.prepareFixture('CMS-01', 'NewsArticle', fixtureName, {
        title_i18n: { en_US: titleEn, ar_SA: titleAr },
        publicationDate: new Date().toISOString().slice(0, 10),
        thumbnailImage,
      }, { acIds: ['AC-1'] });
      steps.push(created);
      ctx.data = { erc: created.erc || erc, titleEn, titleAr };
      return steps;
    },

    /* ── System State: هل الـ CMS حفظ فعلاً؟ ── */
    async verifyCms(ctx) {
      return [await ctx.cms.verifyEntry('CMS-02', 'NewsArticle', ctx.data.erc, {
        bilingual: [{ field: 'title', requireRealArabic: true }],
      }, { acIds: ['AC-1'] })];
    },

    /* ── Web Execution + Propagation Polling ── */
    async web(ctx) {
      const steps = [];
      const home = await ctx.web.verifyRendered({
        stepId: 'WEB-03', url: env.sitePath,
        selector: '[data-qc-news] .qc-news-card__title',
        expectedText: ctx.data.titleEn, acIds: ['AC-2'],
      });
      steps.push(home);
      ctx.rendered.homepageTitle = home.observed?.text;

      const detail = await ctx.web.verifyRendered({
        stepId: 'WEB-04', url: `${env.sitePath}/news/${ctx.data.erc}`,
        selector: 'h1', expectedText: ctx.data.titleEn, acIds: ['AC-2'],
      });
      steps.push(detail);
      ctx.rendered.detailTitle = detail.observed?.text;

      const ar = await ctx.web.verifyLocale({
        stepId: 'WEB-05', url: env.sitePath, locale: 'ar_SA',
        selector: '[data-qc-news] .qc-news-card__title', acIds: ['AC-3'],
      });
      steps.push(ar);
      ctx.rendered.arabicTitle = ar.observed?.text;

      return steps;
    },

    /* ── Cross-System Oracle: عبر عقود التطبيع ── */
    correlate(ctx) {
      return [
        { label: 'homepage-title', objectName: 'NewsArticle', field: 'title',
          cms: ctx.data.titleEn, rendered: ctx.rendered.homepageTitle,
          options: { locale: 'en_US' }, acIds: ['AC-2'] },
        { label: 'detail-title', objectName: 'NewsArticle', field: 'title',
          cms: ctx.data.titleEn, rendered: ctx.rendered.detailTitle,
          options: { locale: 'en_US' }, acIds: ['AC-2'] },
        { label: 'arabic-title', objectName: 'NewsArticle', field: 'title',
          cms: ctx.data.titleAr, rendered: ctx.rendered.arabicTitle,
          options: { locale: 'ar_SA', expect: 'real' }, acIds: ['AC-3'] },
      ];
    },
  };
}

async function main({ web = null, verifyCleanup = false } = {}) {
  const runId = newRunId();
  const cms = new CmsSpecialist({ runId });
  // verifyCleanup=false افتراضياً — التقاط البصمة الكاملة بيعمل 300+ طلب
  // على qcdev. فعّليه فقط لو محتاجة إثبات إن البيئة رجعت مطابقة.
  const orchestrator = new QaOrchestrator({ cms, web, runId, verifyCleanup });

  console.log(`▶ الشريحة الرأسية — NewsArticle`);
  console.log(`  البيئة: ${env.baseUrl}   groupId: ${env.groupId}`);
  console.log(`  runId: ${runId}`);
  if (!web) console.log(`  ⚠️  Web specialist غير موصول — العرض لن يُتحقَّق منه، والحكم سيكون BLOCKED.`);

  const report = await orchestrator.run(buildScenario(runId));
  printReport(report);
  return report;
}

if (require.main === module) {
  main().then((r) => process.exit(r.status === 'PASS' ? 0 : r.status === 'FAIL' ? 1 : 2))
        .catch((e) => { console.error('[✗]', e.message); process.exit(3); });
}

module.exports = { main, buildScenario };
