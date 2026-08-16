'use strict';

/**
 * QA Orchestrator — خط الأنابيب المعتمد.
 *
 *  Phase 0 – Data/Environment Control
 *    → AC → Scenario Mapping
 *    → CMS Execution
 *    → Web Execution
 *    → Propagation Polling
 *    → Normalization
 *    → Cross-System Oracle
 *    → AC Coverage
 *    → Cleanup / Restore Verification
 *
 * الـ orchestrator بيملك حكم السيناريو وحده (§16.E). الـ specialists
 * بيرجّعوا خطوات وأدلة، مش أحكام.
 */

const env = require('../config/env');
const { TestStateModel, STATUS } = require('../lib/test-states');
const { AcOracle } = require('../lib/ac-oracle');
const { declareDataPlan } = require('../lib/data-ownership');
const { compareWithContract } = require('../lib/normalization-contracts');
const cleanupVerify = require('../lib/cleanup-verify');
const { stepResult, assertion } = require('../lib/result');
const { newRunId } = require('../lib/erc');
const objects = require('../lib/objects');

class QaOrchestrator {
  /**
   * @param {object} o
   * @param {object} o.cms          CmsSpecialist
   * @param {object} [o.web]        WebSpecialist (Playwright) — اختياري
   * @param {boolean} [o.verifyCleanup=true]
   */
  constructor({ cms, web = null, runId = null, verifyCleanup = true }) {
    this.cms = cms;
    this.web = web;
    this.runId = runId || cms?.runId || newRunId();
    this.verifyCleanup = verifyCleanup;
  }

  /**
   * @param {object} scenario
   *   id, title
   *   acceptanceCriteria: [{ id, description, requiredAssertions[] }]
   *   dataPlan:  [{ ownership, objectName, name|erc, payload, reason? }]
   *   cms:       async (ctx) => step[]      تنفيذ الـ CMS
   *   web:       async (ctx) => step[]      تنفيذ الـ Web
   *   correlate: (ctx) => [{ field, objectName, cms, rendered, label, options }]
   */
  async run(scenario) {
    const steps = [];
    const state = new TestStateModel(scenario.id, {
      requiredAcIds: (scenario.acceptanceCriteria || []).map((c) => c.id),
    });
    const ctx = { runId: this.runId, cms: this.cms, web: this.web, state, data: {}, rendered: {} };
    const t0 = Date.now();
    let baseline = null;

    /* ───────── Phase 0 — التحكم في البيانات والبيئة ───────── */
    const plan = declareDataPlan(scenario.id, scenario.dataPlan || []);
    if (!plan.valid) {
      state.set('TEST', STATUS.BLOCKED, { reason: plan.error });
      return this._finish(scenario, steps, state, null, t0, plan.error);
    }
    if (this.verifyCleanup) {
      try { baseline = await cleanupVerify.capture(); }
      catch (e) { console.warn(`[!] تعذّر التقاط البصمة الأساسية: ${e.message}`); }
    }

    /* ───────── AC → Scenario Mapping ───────── */
    const oracle = new AcOracle(scenario.acceptanceCriteria || []);
    await state.evaluate('TEST', async () => {
      const ok = oracle.requiredIds.length > 0;
      return {
        satisfied: ok,
        detail: ok
          ? { acIds: oracle.requiredIds, dataPlan: plan.summary }
          : { reason: 'السيناريو بلا معايير قبول — لا يوجد oracle يحكم عليه' },
      };
    });
    if (state.states.TEST.status !== STATUS.SATISFIED) {
      return this._finish(scenario, steps, state, oracle, t0, 'لا يوجد oracle');
    }

    /* ───────── DATA — تجهيز البيانات ───────── */
    await state.evaluate('DATA', async () => {
      const out = scenario.cms ? await scenario.cms(ctx) : [];
      steps.push(...out);
      const bad = out.filter((s) => s.status !== 'PASS');
      return {
        satisfied: bad.length === 0,
        blocked: bad.some((s) => s.status === 'BLOCKED'),
        detail: { steps: out.length, failed: bad.map((s) => s.stepId) },
      };
    });

    /* ───────── SYSTEM — الـ CMS حفظ/نشر ───────── *
     * البوابة: لو DATA مش SATISFIED، دي BLOCKED من غير تنفيذ.
     * كده فشل الكتابة مبيتقراش كعيب في الـ fragment.               */
    await state.evaluate('SYSTEM', async () => {
      const verifySteps = scenario.verifyCms ? await scenario.verifyCms(ctx) : [];
      steps.push(...verifySteps);
      const bad = verifySteps.filter((s) => s.status !== 'PASS');
      return {
        satisfied: bad.length === 0,
        blocked: bad.some((s) => s.status === 'BLOCKED'),
        detail: { verified: verifySteps.length, failed: bad.map((s) => s.stepId) },
      };
    });

    /* ───────── PRESENTATION — Web Execution + Propagation Polling ───────── */
    await state.evaluate('PRESENTATION', async () => {
      if (!this.web || !scenario.web) {
        return { satisfied: false, blocked: true, detail: { reason: 'Web specialist غير موصول — العرض غير متحقَّق منه' } };
      }
      const out = await scenario.web(ctx);   // الـ polling جوّه الـ web specialist
      steps.push(...out);
      const bad = out.filter((s) => s.status !== 'PASS');
      return {
        satisfied: bad.length === 0,
        blocked: bad.some((s) => s.status === 'BLOCKED'),
        detail: { steps: out.length, failed: bad.map((s) => s.stepId) },
      };
    });

    /* ───────── Normalization + Cross-System Oracle ───────── */
    if (scenario.correlate && state.states.PRESENTATION.status === STATUS.SATISFIED) {
      steps.push(await this._correlate(scenario, ctx));
    }

    return this._finish(scenario, steps, state, oracle, t0, null, baseline);
  }

  /**
   * المقارنة عبر الأنظمة — عبر عقد تطبيع مشتق من الـ metadata،
   * مش مقارنة نصية خام.
   */
  async _correlate(scenario, ctx) {
    const pairs = scenario.correlate(ctx) || [];
    const assertions = [];
    for (const p of pairs) {
      let field = null;
      if (p.objectName && p.field) {
        try { field = objects.getField(await objects.findObject(p.objectName), p.field); }
        catch { field = null; }
      }
      const r = compareWithContract(field || { name: p.field, businessType: p.businessType }, p.cms, p.rendered, p.options || {});
      assertions.push(assertion(`cross-system:${p.label}`, r.match, {
        contract: r.contract, mode: r.mode,
        expected: r.expected, actual: r.actual, detail: r.detail,
        allowedTransforms: r.allowedTransforms,
      }));
    }
    const failed = assertions.filter((a) => !a.passed);
    return stepResult({
      stepId: 'X-CORRELATE', specialist: 'orchestrator', action: 'cross-system-oracle',
      status: failed.length ? 'FAIL' : 'PASS',
      acIds: [...new Set(pairs.flatMap((p) => p.acIds || []))],
      assertions, evidence: ['normalization-contract', 'cross-system-comparison'],
    });
  }

  /* ───────── Cleanup / Restore Verification + الحكم ───────── */
  async _finish(scenario, steps, state, oracle, t0, note, baseline) {
    // التنظيف بيشتغل دايماً — حتى لو السيناريو فشل أو انفجر.
    if (this.cms) steps.push(await this.cms.rollbackFixture('CLEANUP'));

    let cleanup = null;
    if (this.verifyCleanup && baseline) {
      try {
        const after = await cleanupVerify.capture();
        const d = cleanupVerify.diff(baseline, after);
        cleanup = cleanupVerify.toAssertion(d);
        steps.push(stepResult({
          stepId: 'CLEANUP-VERIFY', specialist: 'orchestrator', action: 'verify-restore',
          status: cleanup.passed ? 'PASS' : cleanup.blocking ? 'BLOCKED' : 'FAIL',
          assertions: [cleanup], observed: { verdict: d.verdict, foreignChanges: d.foreignChanges },
          evidence: ['environment-fingerprint'],
        }));
      } catch (e) {
        console.warn(`[!] تعذّر التحقق من التنظيف: ${e.message}`);
      }
    }

    /* ───────── AC Coverage ───────── */
    const coverage = oracle ? oracle.evaluate(steps) : null;

    /* ───────── الحكم — ملك الـ orchestrator وحده ───────── */
    const blocked = steps.filter((s) => s.status === 'BLOCKED');
    const failed = steps.filter((s) => s.status === 'FAIL');

    let status = 'PASS';
    if (failed.length) status = 'FAIL';
    if (blocked.length) status = 'BLOCKED';
    // التغطية الكاملة شرط ضروري: PASS بدون إثبات كل AC ممنوع.
    if (status === 'PASS' && coverage && !coverage.complete) status = 'BLOCKED';

    return {
      scenarioId: scenario.id,
      title: scenario.title,
      status,
      verdictScope: 'SCENARIO',
      runId: this.runId,
      states: state.summary(),
      failureSurface: state.failureSurface,
      coverage: coverage && {
        proven: coverage.proven, failed: coverage.failed,
        notCovered: coverage.notCovered,
        ratio: Number(coverage.coverageRatio.toFixed(2)),
        criteria: coverage.criteria,
      },
      cleanup,
      steps,
      note,
      durationMs: Date.now() - t0,
      environment: { baseUrl: env.baseUrl, groupId: env.groupId },
      at: new Date().toISOString(),
    };
  }
}

/** تقرير نصي مختصر للترمينال. */
function printReport(r) {
  const icon = { PASS: '✓', FAIL: '✗', BLOCKED: '⏸' }[r.status];
  console.log(`\n${'─'.repeat(58)}`);
  console.log(`${icon} ${r.scenarioId} — ${r.title || ''}`);
  console.log(`${'─'.repeat(58)}`);

  console.log('\nالحالات الأربع:');
  for (const [k, v] of Object.entries(r.states.states)) {
    console.log(`  ${v === 'SATISFIED' ? '✓' : v === 'PENDING' ? '·' : '✗'} ${k.padEnd(14)} ${v}`);
  }
  if (r.states.haltedAt) console.log(`  ↳ توقّف عند ${r.states.haltedAt} — السطح: ${r.failureSurface}`);

  if (r.coverage) {
    console.log(`\nتغطية معايير القبول: ${(r.coverage.ratio * 100).toFixed(0)}%`);
    for (const c of r.coverage.criteria) {
      const m = { PROVEN: '✓', FAILED: '✗', NOT_COVERED: '○' }[c.status];
      console.log(`  ${m} ${c.id.padEnd(8)} ${c.status.padEnd(12)} ${c.description || ''}`);
      c.missing?.forEach((x) => console.log(`        ○ تأكيد مفقود: ${x}`));
      c.failed?.forEach((x) => console.log(`        ✗ ${x.assertion} (${x.stepId})`));
    }
  }

  const bad = r.steps.filter((s) => s.status !== 'PASS');
  if (bad.length) {
    console.log('\nالخطوات غير الناجحة:');
    for (const s of bad) {
      console.log(`  ${s.status === 'FAIL' ? '✗' : '⏸'} ${s.stepId} [${s.specialist}] ${s.error?.message?.slice(0, 80) || ''}`);
      (s.assertions || []).filter((a) => !a.passed)
        .forEach((a) => console.log(`      ✗ ${a.name}${a.detail ? ' — ' + a.detail : ''}`));
    }
  }

  if (r.cleanup) {
    console.log(`\nالتنظيف: ${r.cleanup.verdict}${r.cleanup.detail ? ' — ' + r.cleanup.detail : ''}`);
    r.cleanup.foreignChanges?.forEach((f) =>
      console.log(`  ⚠️  ${f.object}: ${f.foreign} تغيير ليس من هذا الـ run (بيئة مشتركة)`));
  }

  console.log(`\nالحكم: ${r.status}   المدة: ${(r.durationMs / 1000).toFixed(1)}s   runId: ${r.runId}`);
}

module.exports = { QaOrchestrator, printReport };
