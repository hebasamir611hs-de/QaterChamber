'use strict';

/**
 * انتظار انتشار التغيير — الفجوة رقم 2 في وثيقة التسليم.
 *
 * الملاحظة: تعديل الـ CMS مش بيظهر على الموقع فوراً في الحالة العامة.
 *
 * ⚠️ السبب **غير مُتحقَّق منه على هذا الـ instance**.
 * الفرضية الشائعة (cache الـ portal + إعادة فهرسة Elasticsearch)
 * منقولة من معرفة عامة بالمنصة، مش من قياس حي على qcdev.
 * شغّل `tools/propagation-probe.js` من داخل الشبكة ووثّق النتيجة
 * في liferay-context.md كـ [LIVE] قبل اعتماد السبب كقاعدة منصة.
 *
 * ملاحظة مهمة: آلية الـ polling دي صحيحة **بغض النظر عن السبب** —
 * هي بتنتظر الشرط نفسه مش بتفترض تفسيراً. اللي محتاج تحقق هو
 * التفسير والمهلة المناسبة، مش وجود الانتظار.
 *
 * القاعدة: ممنوع sleep بقيمة ثابتة.
 * - sleep قصير  → التست بيفشل عشوائياً
 * - sleep طويل  → السويت بتبقى بطيئة والفشل بيتأخر اكتشافه
 * الصح: poll على الشرط نفسه بمهلة قصوى.
 */

const env = require('../config/env');
const { sleep } = require('./rest-client');

class PropagationTimeout extends Error {
  constructor(what, ms, lastObserved) {
    super(`لم ينتشر التغيير خلال ${ms}ms: ${what}`);
    this.name = 'PropagationTimeout';
    this.what = what;
    this.timeoutMs = ms;
    this.lastObserved = lastObserved;
    /** انتهاء المهلة = BLOCKED مش FAIL — مش عيب في المنتج بالضرورة. */
    this.kind = 'PROPAGATION';
  }
}

/**
 * ينفّذ check() بشكل متكرر لحد ما ترجع truthy أو تنتهي المهلة.
 *
 * check يرجع إما:
 *   - قيمة truthy → نجاح، بترجع كما هي
 *   - { ok: true, value } → نجاح
 *   - { ok: false, observed } → لسه، مع تسجيل آخر ملاحظة للتشخيص
 */
async function waitFor(what, check, opts = {}) {
  const timeoutMs = opts.timeoutMs ?? env.propagationTimeoutMs;
  const intervalMs = opts.intervalMs ?? env.propagationIntervalMs;
  const started = Date.now();
  let lastObserved;
  let attempts = 0;

  for (;;) {
    attempts++;
    let r;
    try {
      r = await check();
    } catch (e) {
      lastObserved = `خطأ: ${e.message}`;
      r = null;
    }

    if (r && typeof r === 'object' && 'ok' in r) {
      if (r.ok) return { value: r.value ?? r, waitedMs: Date.now() - started, attempts };
      lastObserved = r.observed ?? lastObserved;
    } else if (r) {
      return { value: r, waitedMs: Date.now() - started, attempts };
    }

    if (Date.now() - started >= timeoutMs) {
      throw new PropagationTimeout(what, timeoutMs, lastObserved);
    }
    await sleep(intervalMs);
  }
}

/**
 * ينتظر لحد ما الـ CMS نفسه يرجّع القيمة المتوقعة (read-after-write).
 * الخطوة دي بتفصل "الكتابة مامرّتش" عن "الموقع لسه مأدّاش".
 */
async function waitForCmsValue(objectDef, erc, predicate, opts = {}) {
  const { getEntry } = require('./objects');
  return waitFor(
    `${objectDef.name}/${erc} يعكس القيمة الجديدة في الـ CMS`,
    async () => {
      const e = await getEntry(objectDef, erc);
      if (!e) return { ok: false, observed: 'الصف غير موجود' };
      const ok = predicate(e);
      return ok ? { ok: true, value: e } : { ok: false, observed: summarize(e) };
    },
    opts
  );
}

const summarize = (e) => {
  const o = {};
  for (const [k, v] of Object.entries(e)) {
    if (typeof v === 'object' || k.startsWith('__')) continue;
    o[k] = v;
    if (Object.keys(o).length >= 6) break;
  }
  return JSON.stringify(o);
};

module.exports = { waitFor, waitForCmsValue, PropagationTimeout };
