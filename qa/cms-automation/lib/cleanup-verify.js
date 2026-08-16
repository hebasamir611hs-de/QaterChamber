'use strict';

/**
 * التحقق من التنظيف — إثبات، مش تسجيل.
 *
 * سجل التعديلات بيقول "نفّذت الاسترجاع". ده مش نفس "البيئة رجعت".
 * الفرق بيتراكم بصمت: كل run بيسيب أثر صغير، وبعد شهر نص السويت
 * بيفشل لأسباب متراكمة محدش يعرف مصدرها.
 *
 * الآلية: بصمة قبل/بعد لكل Object (العدد + مفاتيح الصفوف).
 * أي فرق = الـ run بيتعلّم DIRTY حتى لو كل التستات نجحت.
 */

const fs = require('fs');
const path = require('path');
const env = require('./env-shim');
const { getAll } = require('./rest-client');
const { loadCatalog, entriesPath } = require('./objects');

/** يلتقط بصمة البيئة. */
async function capture({ objects = null } = {}) {
  const cat = objects ? { objects } : await loadCatalog();
  const snap = { takenAt: new Date().toISOString(), baseUrl: env.baseUrl, groupId: env.groupId, objects: {} };

  for (const o of cat.objects) {
    try {
      const items = await getAll(entriesPath(o), 100);
      snap.objects[o.name] = {
        count: items.length,
        keys: items.map((i) => i.externalReferenceCode || String(i.id)).sort(),
      };
    } catch (e) {
      snap.objects[o.name] = { error: String(e.message).slice(0, 200) };
    }
  }
  return snap;
}

const save = (snap, file) => {
  fs.mkdirSync(path.dirname(path.resolve(file)), { recursive: true });
  fs.writeFileSync(file, JSON.stringify(snap, null, 2), 'utf8');
  return file;
};

const load = (file) => JSON.parse(fs.readFileSync(file, 'utf8'));

/**
 * يقارن بصمتين.
 *
 * LEFTOVER  صفوف زايدة   → التنظيف ناقص           (HIGH)
 * DATA_LOSS صفوف ناقصة  → حذفنا بيانات أصلية      (CRITICAL)
 *
 * ملاحظة مقصودة: العدّادات التلقائية (viewCount/downloadCount) مش
 * جزء من البصمة لأنها بتتغيّر مع كل زيارة. إدخالها كان هيخلّي كل
 * مقارنة DIRTY وبالتالي بلا معنى.
 */
function diff(before, after) {
  const names = new Set([...Object.keys(before.objects), ...Object.keys(after.objects)]);
  const findings = [];

  for (const name of [...names].sort()) {
    const b = before.objects[name], a = after.objects[name];
    if (!b) { findings.push({ object: name, kind: 'OBJECT_ADDED', severity: 'INFO' }); continue; }
    if (!a) { findings.push({ object: name, kind: 'OBJECT_REMOVED', severity: 'HIGH' }); continue; }
    if (b.error || a.error) { findings.push({ object: name, kind: 'READ_ERROR', severity: 'HIGH', detail: b.error || a.error }); continue; }

    const bk = new Set(b.keys), ak = new Set(a.keys);
    const leftover = a.keys.filter((k) => !bk.has(k));
    const missing = b.keys.filter((k) => !ak.has(k));

    if (leftover.length)
      findings.push({ object: name, kind: 'LEFTOVER', severity: 'HIGH',
        count: leftover.length, keys: leftover.slice(0, 20),
        testOwned: leftover.filter((k) => k.startsWith(env.testPrefix)).length });
    if (missing.length)
      findings.push({ object: name, kind: 'DATA_LOSS', severity: 'CRITICAL',
        count: missing.length, keys: missing.slice(0, 20) });
  }

  const critical = findings.filter((f) => f.severity === 'CRITICAL');
  const high = findings.filter((f) => f.severity === 'HIGH');

  return {
    clean: findings.length === 0,
    verdict: critical.length ? 'DATA_LOSS' : high.length ? 'DIRTY' : 'CLEAN',
    findings, critical: critical.length, high: high.length,
    /**
     * التمييز ده مهم على بيئة مشتركة: الصفوف الزايدة اللي **مش**
     * بتحمل بادئة التست على الأرجح شغل حد تاني، مش تنظيف ناقص منّنا.
     */
    foreignChanges: findings
      .filter((f) => f.kind === 'LEFTOVER' && f.count > (f.testOwned || 0))
      .map((f) => ({ object: f.object, foreign: f.count - (f.testOwned || 0) })),
  };
}

/** الشكل الجاهز للـ orchestrator — تأكيد واحد يحسم نظافة الـ run. */
function toAssertion(result) {
  return {
    name: 'cleanup-verified',
    passed: result.verdict === 'CLEAN',
    blocking: result.verdict === 'DATA_LOSS',
    verdict: result.verdict,
    findings: result.findings.length,
    foreignChanges: result.foreignChanges,
    detail:
      result.verdict === 'CLEAN' ? undefined
      : result.verdict === 'DATA_LOSS' ? 'فقدان بيانات أصلية — استرجاع DB (إجراء طوارئ)'
      : result.foreignChanges.length ? 'تغييرات ليست من هذا الـ run — بيئة مشتركة'
      : 'تنظيف ناقص — أعد تشغيل cleanup',
  };
}

module.exports = { capture, save, load, diff, toAssertion };
