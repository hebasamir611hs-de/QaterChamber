'use strict';

/**
 * سجل التعديلات + الاسترجاع — §7.
 *
 * كل تعديل بيتسجّل مع حالته السابقة قبل ما يحصل. الاسترجاع LIFO.
 *
 * الجزء اللي وثيقة التسليم مغطّاهوش: المنصة أحياناً **مش بتسمح**
 * بالتراجع. §3 بيوثّق حالتين:
 *   - Boolean بـ required:true مش ممكن يترجّع لـ false (400)
 *   - Attachment: الاسترجاع بيرجّع id الملف، مش بيرفع الملف
 * الوعد بالـ rollback من غير الفحص ده وعد كاذب — فبنفحص قبل التعديل
 * ونرفض، مش بنكتشف بعد الفشل.
 */

const fs = require('fs');
const path = require('path');
const env = require('../config/env');
const { put, scopedByErcPath } = require('./rest-client');
const { irreversibleFields, getEntry } = require('./objects');

const runDir = (runId) => path.join(env.runsDir, runId);
const logFile = (runId) => path.join(runDir(runId), 'mutation-log.jsonl');

/** حقول محسوبة/متطايرة — إرجاعها بيكتب فوق قيم حقيقية أو بيرفضه السيرفر. */
const VOLATILE = new Set([
  'dateCreated', 'dateModified', 'creator', 'status', 'actions',
  'viewCount', 'downloadCount', '__status', '__ok', '__notFound',
]);

const stripVolatile = (obj) => {
  const c = JSON.parse(JSON.stringify(obj));
  for (const k of VOLATILE) delete c[k];
  return c;
};

/**
 * يفحص هل التعديل ده قابل للتراجع.
 * بيرجع { reversible, blockers[] }.
 */
function checkReversible(objectDef, patch) {
  const risky = irreversibleFields(objectDef);
  const blockers = [];
  for (const f of risky) {
    if (!(f.name in patch)) continue;
    if (f.businessType === 'Boolean' && f.required) {
      blockers.push({
        field: f.name, type: 'REQUIRED_BOOLEAN',
        detail: `Boolean بـ required:true — المنصة بترفض إرجاعه لـ false (400). ` +
                `صمّم التست بحيث يحذف صف تست بدل ما يقفل الحقل ده على صف موجود.`,
      });
    }
    if (f.businessType === 'Attachment') {
      blockers.push({
        field: f.name, type: 'ATTACHMENT',
        detail: `الاسترجاع بيرجّع id الملف مش الملف نفسه، ورفع الملفات multipart. ` +
                `عدّل المرفقات على صفوف تست فقط.`,
      });
    }
  }
  return { reversible: blockers.length === 0, blockers };
}

function createLog(runId) {
  fs.mkdirSync(runDir(runId), { recursive: true });
  const file = logFile(runId);

  return {
    runId,
    file,

    /**
     * يلتقط الحالة السابقة قبل تعديل صف موجود.
     * بيرفض لو التعديل غير قابل للتراجع — إلا لو force صراحةً.
     */
    async capture(objectDef, erc, patch = {}, { force = false, reason = '' } = {}) {
      // نجيب الحالة السابقة أولاً — لأن الحماية تختلف حسب الحالة:
      //   صف جديد   → التنظيف حذف → لا معنى لفحص قابلية التراجع
      //   صف موجود → التنظيف استرجاع → الفحص مطلوب
      const prior = await getEntry(objectDef, erc);
      const action = prior ? 'RESTORE' : 'DELETE';

      let blockers = [], reversible = true;
      if (action === 'RESTORE') {
        ({ reversible, blockers } = checkReversible(objectDef, patch));
        if (!reversible && !force) {
          const msg = blockers.map((b) => `  • ${b.field}: ${b.detail}`).join('\n');
          throw new Error(
            `تعديل غير قابل للتراجع على صف موجود ${objectDef.name}/${erc}:\n${msg}\n` +
              `مرّر { force: true, reason } لو مقبول — وساعتها استرجاع الـ DB بيبقى الخيار الوحيد.`
          );
        }
      }

      const entry = {
        at: new Date().toISOString(),
        objectName: objectDef.name,
        restPath: objectDef.restPath,
        erc,
        action,
        reason,
        irreversible: !reversible,
        blockers: blockers.length ? blockers : undefined,
        priorState: prior ? stripVolatile(prior) : null,
      };
      fs.appendFileSync(file, JSON.stringify(entry) + '\n', 'utf8');
      return entry;
    },

    entries() {
      if (!fs.existsSync(file)) return [];
      return fs.readFileSync(file, 'utf8').split('\n').filter(Boolean).map((l) => JSON.parse(l));
    },
  };
}

/**
 * الاسترجاع. LIFO.
 * الصفوف اللي ماكانتش موجودة (action=DELETE) بيتكفّل بيها التنظيف
 * عن طريق البادئة — مش بنمسحها هنا عشان مانكررش الحذف.
 */
async function restore(runId, { dryRun = false } = {}) {
  const log = createLog(runId);
  const entries = log.entries().reverse();
  if (!entries.length) return { restored: 0, failures: [], skipped: 0 };

  let restored = 0, skipped = 0;
  const failures = [];

  for (const e of entries) {
    if (e.action === 'DELETE') { skipped++; continue; }
    try {
      if (!dryRun) await put(scopedByErcPath(e.restPath, e.erc), e.priorState);
      restored++;
    } catch (err) {
      failures.push({ objectName: e.objectName, erc: e.erc, error: String(err.message).slice(0, 300) });
    }
  }

  if (failures.length) {
    fs.writeFileSync(
      path.join(runDir(runId), 'restore-failures.json'),
      JSON.stringify(failures, null, 2), 'utf8'
    );
  } else if (!dryRun && fs.existsSync(logFile(runId))) {
    fs.renameSync(logFile(runId), logFile(runId).replace('.jsonl', `.done.jsonl`));
  }

  return { restored, skipped, failures };
}

module.exports = { createLog, restore, checkReversible, stripVolatile };
