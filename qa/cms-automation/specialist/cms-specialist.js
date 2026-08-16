'use strict';

/**
 * CMS QA Specialist — §3.2 / §17 Phase 3.
 *
 * العقد اللي الـ orchestrator بينادي عليه. كل دالة بترجع stepResult
 * مهيكل (§13) ومش بترمي استثناء للسيناريو — الأخطاء بتترجم لحالة
 * FAIL أو BLOCKED عشان الـ orchestrator يفرّق بين عيب المنتج وعطل
 * المنصة.
 *
 * الـ specialist بيحكم على خطوته بس. حكم السيناريو ملك الـ orchestrator.
 */

const env = require('../config/env');
const { put, byErcPath, scopedByErcPath, LiferayError } = require('../lib/rest-client');
const objects = require('../lib/objects');
const A = require('../assertions');
const { stepResult, assertion } = require('../lib/result');
const { createLog } = require('../lib/mutation-log');
const { assertMutable, fixtureErc } = require('../lib/erc');
const { waitForCmsValue, PropagationTimeout } = require('../lib/propagation');

class CmsSpecialist {
  constructor({ runId }) {
    if (!runId) throw new Error('CmsSpecialist: runId مطلوب');
    this.runId = runId;
    this.log = createLog(runId);
  }

  /** يغلّف أي خطوة: بيحوّل الاستثناءات لحالة مهيكلة. */
  async _step(stepId, meta, fn) {
    const t0 = Date.now();
    try {
      const out = await fn();
      const assertions = out.assertions || [];
      const failed = assertions.filter((a) => !a.passed);
      const blockingFail = failed.some((a) => a.blocking);
      return stepResult({
        stepId, specialist: 'cms', ...meta, ...out,
        status: blockingFail ? 'BLOCKED' : failed.length ? 'FAIL' : 'PASS',
        timings: { ms: Date.now() - t0 },
      });
    } catch (e) {
      const blocking =
        e instanceof PropagationTimeout ||
        (e instanceof LiferayError && e.isBlocking);
      return stepResult({
        stepId, specialist: 'cms', ...meta,
        status: blocking ? 'BLOCKED' : 'FAIL',
        error: e,
        evidence: ['exception'],
        timings: { ms: Date.now() - t0 },
      });
    }
  }

  /* ------------------------------ اكتشاف ------------------------------ */

  findObject(nameOrErc) { return objects.findObject(nameOrErc); }

  async describeObject(stepId, name, { acIds = [] } = {}) {
    return this._step(stepId, { action: 'describe', resourceType: name, acIds }, async () => {
      const o = await objects.findObject(name);
      return {
        observed: {
          name: o.name, erc: o.erc, restPath: o.restPath, titleField: o.titleField,
          fieldCount: o.fields.length,
          localizedFields: o.fields.filter((f) => f.localized).map((f) => f.name),
          requiredFields: o.fields.filter((f) => f.required).map((f) => f.name),
          relationships: o.relationships.map((r) => `${r.parentName}→${r.childName}`),
          irreversibleFields: objects.irreversibleFields(o).map((f) => f.name),
        },
        assertions: [A.validationRules(o)],
        evidence: ['object-metadata'],
      };
    });
  }

  /* ------------------------------- قراءة ------------------------------- */

  async getEntry(stepId, objectName, erc, { acIds = [] } = {}) {
    return this._step(stepId, { action: 'read', resourceType: objectName, erc, acIds }, async () => {
      const o = await objects.findObject(objectName);
      const entry = await objects.getEntry(o, erc);
      return {
        observed: entry ? summarize(entry) : null,
        assertions: [assertion('entry-exists', !!entry, { erc })],
        evidence: ['api-response'],
        _entry: entry,
      };
    });
  }

  /* -------------------------- إنشاء / تعديل -------------------------- */

  /**
   * PUT idempotent بالـ ERC (§7). بيلتقط الحالة السابقة قبل الكتابة.
   *
   * الأمان: لو الـ ERC مش بادئ ببادئة التست، بيترفض إلا لو
   * allowExisting:true + reason — وساعتها الاسترجاع بيبقى إجباري.
   */
  async createOrUpdateEntry(stepId, objectName, erc, payload, opts = {}) {
    const { acIds = [], allowExisting = false, reason = '', force = false } = opts;
    return this._step(
      stepId,
      { action: 'createOrUpdate', resourceType: objectName, erc, acIds },
      async () => {
        const o = await objects.findObject(objectName);
        const guard = assertMutable(erc, { allowExisting, reason });

        const captured = await this.log.capture(o, erc, payload, { force, reason });

        await put(scopedByErcPath(o.restPath, erc), payload);

        // read-after-write: نتأكد بس إن الصف موجود بالـ ERC الصح — كافي
        // لإثبات إن الكتابة وصلت. المقارنة التفصيلية للحقول شغل خطوة
        // verifyEntry، عشان الحقول اللي بيغيّرها السيرفر (تواريخ،
        // أشكال المرفقات) مبتفشّلش الكتابة نفسها.
        const { value: after, waitedMs } = await waitForCmsValue(
          o, erc,
          (e) => e && e.externalReferenceCode === erc,
          opts
        );

        return {
          expected: payload,
          observed: summarize(after),
          assertions: [
            assertion('mutation-persisted', true, { waitedMs }),
            assertion('prior-state-captured', !!captured, {
              action: captured.action,
              irreversible: captured.irreversible || false,
            }),
          ],
          evidence: ['api-response', 'mutation-log'],
          _entry: after,
          _guard: guard.kind,
        };
      }
    );
  }

  /** تجهيز صف تست جديد — الـ ERC بيتبني تلقائياً ببادئة الـ run. */
  async prepareFixture(stepId, objectName, name, payload, opts = {}) {
    const erc = fixtureErc(this.runId, name);
    const r = await this.createOrUpdateEntry(stepId, objectName, erc,
      { ...payload, externalReferenceCode: erc }, opts);
    r.erc = erc;
    return r;
  }

  /* ------------------------------ تحقق ------------------------------ */

  /**
   * تحقق مركّب من صف واحد.
   * checks: { fields:{name:value}, localized:[{field,locale,value}],
   *           active:{field,expected}, ordering:{field,strictHundreds},
   *           arabic:[{field,expect}], relationships:[field], bilingual:[field] }
   */
  async verifyEntry(stepId, objectName, erc, checks = {}, { acIds = [] } = {}) {
    return this._step(stepId, { action: 'verify', resourceType: objectName, erc, acIds }, async () => {
      const o = await objects.findObject(objectName);
      const entry = await objects.getEntry(o, erc);
      if (!entry) {
        return {
          assertions: [assertion('entry-exists', false, { erc })],
          evidence: ['api-response'],
        };
      }

      const a = [];
      for (const [f, v] of Object.entries(checks.fields || {})) a.push(A.fieldEquals(entry, f, v));
      for (const l of checks.localized || []) a.push(A.localizedEquals(entry, l.field, l.locale, l.value));
      for (const b of checks.bilingual || []) {
        const spec = typeof b === 'string' ? { field: b } : b;
        a.push(A.bothLocalesFilled(entry, spec.field, { requireRealArabic: spec.requireRealArabic }));
      }
      for (const ar of checks.arabic || []) a.push(A.arabicContent(entry, ar.field, { expect: ar.expect }));
      for (const rel of checks.relationships || []) a.push(A.relationshipSet(o, entry, rel));
      for (const at of checks.attachments || []) a.push(A.attachmentExists(entry, at));
      if (checks.active) a.push(A.isActive(entry, checks.active.field, checks.active.expected));
      if (checks.schedule) a.push(A.withinSchedule(entry));
      if (checks.ordering) a.push(A.displayOrderValid(entry, checks.ordering.field, checks.ordering));

      return { observed: summarize(entry), assertions: a, evidence: ['api-response'], _entry: entry };
    });
  }

  /** تحقق من الترتيب المعروض مقابل displayOrder في الـ CMS. */
  async verifyOrdering(stepId, objectName, renderedKeys, opts = {}) {
    return this._step(stepId, { action: 'verifyOrdering', resourceType: objectName, acIds: opts.acIds || [] },
      async () => {
        const o = await objects.findObject(objectName);
        const entries = await objects.listEntries(o);
        return {
          observed: { renderedKeys, cmsCount: entries.length },
          assertions: [A.orderMatches(entries, renderedKeys, opts)],
          evidence: ['api-response'],
        };
      });
  }

  /* --------------------------- عبر الأنظمة --------------------------- */

  /**
   * §11 خطوة 6 — لكن عبر طبقة التطبيع، مش مقارنة خام.
   * الـ orchestrator بينادي عليها بعد ما الـ Web specialist يرجّع المعروض.
   */
  async correlate(stepId, pairs, { acIds = [] } = {}) {
    return this._step(stepId, { action: 'correlate', acIds }, async () => ({
      assertions: pairs.map((p) =>
        p.type === 'date'
          ? A.crossSystemDate(p.cms, p.rendered, p.label, p.toleranceMs)
          : A.crossSystemText(p.cms, p.rendered, p.label, p.options || {})
      ),
      observed: { pairs: pairs.length },
      evidence: ['cross-system-comparison'],
    }));
  }

  /* ----------------------------- استرجاع ----------------------------- */

  async rollbackFixture(stepId) {
    const { restore } = require('../lib/mutation-log');
    return this._step(stepId, { action: 'rollback' }, async () => {
      const r = await restore(this.runId);
      return {
        observed: r,
        assertions: [assertion('rollback-complete', r.failures.length === 0, {
          restored: r.restored, skipped: r.skipped, failures: r.failures.length,
          blocking: r.failures.length > 0,
        })],
        evidence: ['mutation-log'],
      };
    });
  }
}

function summarize(entry) {
  const o = {};
  for (const [k, v] of Object.entries(entry || {})) {
    if (k.startsWith('__') || k === 'actions') continue;
    o[k] = v;
  }
  return o;
}

module.exports = { CmsSpecialist };
