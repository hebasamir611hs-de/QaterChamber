'use strict';

/**
 * نموذج الحالات الأربع.
 *
 *  TEST          إحنا بنختبر إيه؟        النية + معايير القبول
 *  DATA          إيه البيانات المطلوبة؟   الملكية + التجهيز
 *  SYSTEM        هل الـ CMS حفظ/نشر؟     read-after-write مؤكد
 *  PRESENTATION  هل ظهر صح للمستخدم؟     العرض متحقَّق منه
 *
 * القيمة الحقيقية في **بوابات الانتقال**: مينفعش تحكم على العرض
 * وانت مش متأكد إن الـ CMS حفظ أصلاً. من غير البوابة دي، فشل
 * الكتابة بيتقرأ كعيب في الـ fragment — وده بيوجّه التحقيق في
 * الاتجاه الغلط.
 */

const ORDER = ['TEST', 'DATA', 'SYSTEM', 'PRESENTATION'];

const STATUS = {
  PENDING: 'PENDING',
  SATISFIED: 'SATISFIED',
  FAILED: 'FAILED',
  BLOCKED: 'BLOCKED',
  SKIPPED: 'SKIPPED',
};

class TestStateModel {
  constructor(scenarioId, { requiredAcIds = [] } = {}) {
    this.scenarioId = scenarioId;
    this.requiredAcIds = requiredAcIds;
    this.states = {
      TEST: st('ما الذي نختبره'),
      DATA: st('البيانات المطلوبة'),
      SYSTEM: st('حفظ/نشر الـ CMS'),
      PRESENTATION: st('العرض للمستخدم'),
    };
    this.transitions = [];
  }

  /** هل الحالة دي مسموح تقييمها دلوقتي؟ */
  canEvaluate(name) {
    const i = ORDER.indexOf(name);
    if (i < 0) throw new Error(`حالة غير معروفة: ${name}`);
    for (let k = 0; k < i; k++) {
      const prev = this.states[ORDER[k]];
      if (prev.status !== STATUS.SATISFIED) {
        return {
          ok: false,
          reason: `${name} لا يمكن تقييمها: ${ORDER[k]} حالتها ${prev.status}`,
          blockedBy: ORDER[k],
        };
      }
    }
    return { ok: true };
  }

  set(name, status, detail = {}) {
    if (!STATUS[status]) throw new Error(`status غير صالح: ${status}`);
    const s = this.states[name];
    if (!s) throw new Error(`حالة غير معروفة: ${name}`);
    s.status = status;
    s.detail = detail;
    s.at = new Date().toISOString();
    this.transitions.push({ state: name, status, at: s.at, ...detail });
    return s;
  }

  /**
   * يقيّم حالة عبر دالة، مع احترام البوابة.
   * لو الحالة السابقة مش SATISFIED، دي بترجع BLOCKED من غير ما
   * تشغّل الفحص أصلاً — يعني مفيش استهلاك وقت ولا نتيجة مضلّلة.
   */
  async evaluate(name, fn) {
    const gate = this.canEvaluate(name);
    if (!gate.ok) {
      this.set(name, STATUS.BLOCKED, { reason: gate.reason, blockedBy: gate.blockedBy });
      return { status: STATUS.BLOCKED, reason: gate.reason };
    }
    try {
      const r = await fn();
      const status = r.satisfied ? STATUS.SATISFIED : r.blocked ? STATUS.BLOCKED : STATUS.FAILED;
      this.set(name, status, r.detail || {});
      return { status, ...r };
    } catch (e) {
      const blocked = e.kind === 'PROPAGATION' || e.isBlocking;
      this.set(name, blocked ? STATUS.BLOCKED : STATUS.FAILED, { error: e.message });
      return { status: blocked ? STATUS.BLOCKED : STATUS.FAILED, error: e };
    }
  }

  /** أين توقّف السيناريو — الحالة الأولى غير المُرضية. */
  get haltedAt() {
    return ORDER.find((n) => this.states[n].status !== STATUS.SATISFIED) || null;
  }

  /**
   * تشخيص السطح: العطل في الـ CMS ولا في العرض؟
   * ده الفرق اللي §12 بيطلبه، ونموذج الحالات بيوفّره مجاناً.
   */
  get failureSurface() {
    const h = this.haltedAt;
    if (!h) return null;
    return { TEST: 'scenario-definition', DATA: 'test-data', SYSTEM: 'cms', PRESENTATION: 'web' }[h];
  }

  summary() {
    return {
      scenarioId: this.scenarioId,
      states: Object.fromEntries(ORDER.map((n) => [n, this.states[n].status])),
      haltedAt: this.haltedAt,
      failureSurface: this.failureSurface,
      transitions: this.transitions,
    };
  }
}

const st = (label) => ({ label, status: STATUS.PENDING, detail: {}, at: null });

module.exports = { TestStateModel, STATUS, ORDER };
