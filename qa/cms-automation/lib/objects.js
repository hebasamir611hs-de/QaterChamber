'use strict';

/**
 * طبقة معرفة الـ Objects — Phase 2.
 *
 * مصدر الحقيقة هو الـ instance نفسه، مش قايمة مكتوبة بالإيد.
 * السبب: الـ Objects بتتغير كل sprint؛ أي كتالوج ثابت بيبقى stale
 * والتستات تبدأ تفشل لأسباب مش حقيقية.
 *
 * بيتدمج مصدرين:
 *  (أ) listing حي        — بيمسك أي Object جديد
 *  (ب) known-objects.json — بيمسك الـ Objects اللي الـ listing بيخفيها (§5.4/§5.6)
 */

const env = require('../config/env');
const { get, getAll, scopedPath, byErcPath, scopedByErcPath, LiferayError } = require('./rest-client');

let _cache = null;

/**
 * ذاكرة مؤقتة للـ Objects المُحمّلة بشكل كسول (بدون كتالوج كامل).
 * السبب: تحميل الـ 111 Object + علاقاتهم بياخد ٥+ دقايق على qcdev،
 * وأي سيناريو بيحتاج ٢-٥ Objects بس في الغالب.
 */
const _lazyCache = new Map(); // key: name or erc → normalized object

async function loadCatalog({ force = false } = {}) {
  if (_cache && !force) return _cache;

  // §5.3 — pageSize >= 99 على الـ endpoint ده بيرجع 404 وهمي.
  const defs = await getAll('/o/object-admin/v1.0/object-definitions', env.objectDefsPageSize);
  const byErc = new Map(defs.map((d) => [d.externalReferenceCode, d]));

  let recovered = 0;
  let unrecoverable = [];
  try {
    const known = require('../config/known-objects.json');
    for (const k of known) {
      if (byErc.has(k.erc)) continue;
      const d = await get(byErcPath('/o/object-admin/v1.0/object-definitions', k.erc));
      if (d.__notFound) { unrecoverable.push(k.erc); continue; }
      byErc.set(k.erc, d);
      recovered++;
    }
  } catch (e) {
    if (e.code !== 'MODULE_NOT_FOUND') throw e;
  }

  const objects = [];
  for (const d of byErc.values()) {
    if (!d.restContextPath) continue;
    objects.push({
      id: d.id,
      name: d.name,
      erc: d.externalReferenceCode,
      label: pick(d.label) || d.name,
      restPath: d.restContextPath.replace(/\/+$/, ''),
      system: !!d.system,
      titleField: d.titleObjectFieldName || 'externalReferenceCode',
      fields: (d.objectFields || []).map(mapField),
      validationRules: (d.objectValidationRules || []).map((r) => ({
        name: pick(r.name), engine: r.engine, script: r.script,
        errorLabel: r.errorLabel, active: r.active,
      })),
      relationships: [],
    });
  }

  const byId = new Map(objects.map((o) => [o.id, o]));
  for (const o of objects) {
    try {
      const rels = await getAll(
        `/o/object-admin/v1.0/object-definitions/${o.id}/object-relationships`, 100
      );
      o.relationships = rels.map((r) => ({
        name: r.name, type: r.type,
        parentId: r.objectDefinitionId1, childId: r.objectDefinitionId2,
        parentName: byId.get(r.objectDefinitionId1)?.name,
        childName: byId.get(r.objectDefinitionId2)?.name,
        deletionType: r.deletionType,
      }));
    } catch { o.relationships = []; }
  }

  _cache = { objects, byName: index(objects, 'name'), byErc: index(objects, 'erc'),
             meta: { recovered, unrecoverable, loadedAt: new Date().toISOString() } };

  if (recovered) console.log(`[i] ${recovered} Object مخفي عن الـ listing — استُرجع بالـ ERC.`);
  if (unrecoverable.length) console.warn(`[!] ${unrecoverable.length} ERC معروف لم يُسترجع: ${unrecoverable.join(', ')}`);

  return _cache;
}

const index = (arr, key) => new Map(arr.map((o) => [o[key], o]));
const pick = (l) => (typeof l === 'string' ? l : l ? (l.en_US || l['en-US'] || Object.values(l)[0]) : null);

function mapField(f) {
  const settings = {};
  for (const s of f.objectFieldSettings || []) settings[s.name] = s.value;
  return {
    name: f.name,
    label: f.label,
    businessType: f.businessType,
    dbType: f.DBType || f.dbType,
    required: !!f.required,
    localized: !!f.localized,
    indexed: !!f.indexed,
    listTypeErc: f.listTypeDefinitionExternalReferenceCode || null,
    settings,
    acceptedFileExtensions: settings.acceptedFileExtensions || null,
  };
}

/* ------------------------------ بحث ------------------------------ */

/**
 * يحمّل Object واحد بس (بدون كتالوج كامل).
 * 3 محاولات بالترتيب:
 *   1. الذاكرة المؤقتة
 *   2. الكتالوج المُحمّل مسبقاً (لو موجود)
 *   3. GET-by-ERC مباشر
 *   4. البحث في known-objects للاسم → ERC → GET
 */
async function findObject(nameOrErc) {
  // 1) ذاكرة مؤقتة
  if (_lazyCache.has(nameOrErc)) return _lazyCache.get(nameOrErc);

  // 2) الكتالوج لو محمّل
  if (_cache) {
    const o = _cache.byName.get(nameOrErc) || _cache.byErc.get(nameOrErc);
    if (o) { _lazyCache.set(nameOrErc, o); return o; }
  }

  // 3) GET-by-ERC مباشر لو المفتاح يشبه ERC
  if (/^(QCDEMO|QC_)/.test(nameOrErc)) {
    const d = await get(byErcPath('/o/object-admin/v1.0/object-definitions', nameOrErc));
    if (!d.__notFound && d.restContextPath) {
      const norm = await normalizeDef(d);
      _lazyCache.set(nameOrErc, norm);
      _lazyCache.set(norm.name, norm);
      return norm;
    }
  }

  // 4) البحث في known-objects بالاسم
  try {
    const known = require('../config/known-objects.json');
    const k = known.find((x) => x.name === nameOrErc || x.erc === nameOrErc);
    if (k) {
      const d = await get(byErcPath('/o/object-admin/v1.0/object-definitions', k.erc));
      if (!d.__notFound && d.restContextPath) {
        const norm = await normalizeDef(d);
        _lazyCache.set(nameOrErc, norm);
        _lazyCache.set(norm.name, norm);
        _lazyCache.set(norm.erc, norm);
        return norm;
      }
    }
  } catch (e) {
    if (e.code !== 'MODULE_NOT_FOUND') throw e;
  }

  throw new LiferayError(
    `Object "${nameOrErc}" غير موجود. جرّبي اسم مختلف أو ERC، أو أضيفيه في config/known-objects.json.`,
    { kind: 'NOT_FOUND' }
  );
}

/** يحوّل Object definition من الشكل الخام لشكل الفريمورك — بيجيب علاقاته. */
async function normalizeDef(d) {
  const obj = {
    id: d.id,
    name: d.name,
    erc: d.externalReferenceCode,
    label: pick(d.label) || d.name,
    restPath: d.restContextPath.replace(/\/+$/, ''),
    system: !!d.system,
    titleField: d.titleObjectFieldName || 'externalReferenceCode',
    fields: (d.objectFields || []).map(mapField),
    validationRules: (d.objectValidationRules || []).map((r) => ({
      name: pick(r.name), engine: r.engine, script: r.script,
      errorLabel: r.errorLabel, active: r.active,
    })),
    relationships: [],
  };
  try {
    const rels = await getAll(
      `/o/object-admin/v1.0/object-definitions/${d.id}/object-relationships`, 100
    );
    obj.relationships = rels.map((r) => ({
      name: r.name, type: r.type,
      parentId: r.objectDefinitionId1, childId: r.objectDefinitionId2,
      deletionType: r.deletionType,
    }));
  } catch { /* بدون علاقات ولا يضر — أغلب الـ Objects بلا علاقات */ }
  return obj;
}

const getField = (o, fieldName) => o.fields.find((f) => f.name === fieldName) || null;

/** الحقول اللي لا يمكن التراجع عن تعديلها — الفجوة رقم 5. */
function irreversibleFields(o) {
  return o.fields.filter(
    (f) =>
      // §3 — Boolean بـ required:true مش ممكن يترجّع لـ false (400)
      (f.businessType === 'Boolean' && f.required) ||
      // الاسترجاع بيرجّع id الملف، مش بيرفع الملف تاني
      f.businessType === 'Attachment'
  );
}

/* ------------------------ ترتيب الحذف ------------------------ */

/**
 * الأبناء قبل الآباء. §7 — 3 علاقات بس موجودة فعلياً؛ الترتيب
 * محسوب من العلاقات الحية مش من قايمة ثابتة، فلو الديفيلوبرز
 * ضافوا علاقة الترتيب بيتصحّح لوحده.
 */
function deletionOrder(objects) {
  const byId = new Map(objects.map((o) => [o.id, o]));
  const children = new Map(objects.map((o) => [o.id, new Set()]));
  for (const o of objects) {
    for (const r of o.relationships) {
      if (!['oneToMany', 'oneToOne'].includes(r.type)) continue;
      if (!byId.has(r.parentId) || !byId.has(r.childId)) continue;
      if (r.parentId === r.childId) continue; // شجرة ذاتية — تتعالج بالعمق
      children.get(r.parentId).add(r.childId);
    }
  }
  const order = [], state = new Map();
  const visit = (id) => {
    if (state.get(id)) return;
    state.set(id, 1);
    for (const c of children.get(id) || []) visit(c);
    state.set(id, 2);
    order.push(byId.get(id));
  };
  objects.forEach((o) => visit(o.id));
  return order;
}

const isSelfReferencing = (o) => o.relationships.some((r) => r.parentId === r.childId);

/* ------------------------ عمليات الصفوف ------------------------ */

const entriesPath = (o) => scopedPath(o.restPath);

async function listEntries(o, pageSize = 100) {
  return getAll(entriesPath(o), pageSize);
}

/**
 * GET بالـ ERC. بيرجع null لو مش موجود — مش استثناء (§7).
 * الـ path scoped لأن الـ Objects site-scoped (اكتشاف حي 2026-08-16).
 */
async function getEntry(o, erc) {
  const r = await get(scopedByErcPath(o.restPath, erc));
  return r.__notFound ? null : r;
}

module.exports = {
  loadCatalog, findObject, getField, irreversibleFields,
  deletionOrder, isSelfReferencing,
  entriesPath, listEntries, getEntry,
};
