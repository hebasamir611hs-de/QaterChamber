'use strict';

/**
 * عميل Liferay REST — §15: كل مطبّات المنصة مغلّفة هنا،
 * فمفيش تست محتاج يعرفها.
 *
 * نموذج خطأ موحّد: كل فشل بيرمي LiferayError بحقول مهيكلة،
 * عشان الـ orchestrator يقدر يفرّق بين BLOCKED و FAIL.
 */

const env = require('../config/env');

class LiferayError extends Error {
  constructor(message, { status, method, path, body, kind } = {}) {
    super(message);
    this.name = 'LiferayError';
    this.status = status;
    this.method = method;
    this.path = path;
    this.body = body;
    /** kind: AUTH | SCOPE | NOT_FOUND | VALIDATION | PLATFORM | NETWORK */
    this.kind = kind || classify(status, message);
  }
  /** أخطاء المنصة/الشبكة = BLOCKED مش FAIL — مش عيب في المنتج. */
  get isBlocking() {
    return ['AUTH', 'SCOPE', 'PLATFORM', 'NETWORK'].includes(this.kind);
  }
}

function classify(status, msg = '') {
  if (status === 401 || status === 403) return 'AUTH';
  if (status === 409) return 'SCOPE';
  if (status === 404) return 'NOT_FOUND';
  if (status === 400 || status === 422) return 'VALIDATION';
  if (status >= 500) return 'PLATFORM';
  if (/fetch failed|ECONNREFUSED|ETIMEDOUT/i.test(msg)) return 'NETWORK';
  return 'PLATFORM';
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function authHeader() {
  return 'Basic ' + Buffer.from(`${env.user}:${env.pass}`).toString('base64');
}

/**
 * طلب واحد. 404 بترجع كـ { __notFound: true } مش استثناء —
 * لأن "مش موجود" حالة متوقعة في بروتوكول GET-by-ERC (§7).
 */
async function request(method, path, body, opts = {}) {
  const { retries = 2, expectJson = true, multipart = false } = opts;
  const url = path.startsWith('http') ? path : env.baseUrl + path;
  let lastErr;

  for (let attempt = 0; attempt <= retries; attempt++) {
    let res;
    try {
      res = await fetch(url, {
        method,
        headers: {
          Authorization: authHeader(),
          Accept: 'application/json',
          ...(body && !multipart ? { 'Content-Type': 'application/json' } : {}),
        },
        body: body ? (multipart ? body : JSON.stringify(body)) : undefined,
      });
    } catch (e) {
      lastErr = new LiferayError(`فشل الاتصال: ${e.message}`, { method, path, kind: 'NETWORK' });
      if (attempt === retries) throw lastErr;
      await sleep(400 * (attempt + 1));
      continue;
    }

    if (res.status === 404) return { __notFound: true, __status: 404 };

    // §5.2 — الـ Objects site-scoped؛ المسار المجرّد بيرجع 409 مش 404.
    // ده أخطر خطأ في المنصة دي لأنه بيتفسر غلط على إنه "مفيش بيانات".
    if (res.status === 409 && path.includes('/o/c/')) {
      throw new LiferayError(
        `409 على ${path} — الـ Object site-scoped. استخدم scopedPath() لإضافة ` +
          `/scopes/${env.groupId}. راجع liferay-context §5.2`,
        { status: 409, method, path, kind: 'SCOPE' }
      );
    }

    if (res.status >= 500 && attempt < retries) {
      await sleep(400 * (attempt + 1));
      continue;
    }

    if (!res.ok) {
      const text = await res.text().catch(() => '');
      throw new LiferayError(`${method} ${path} → ${res.status} ${text.slice(0, 400)}`, {
        status: res.status, method, path, body: text.slice(0, 2000),
      });
    }

    if (!expectJson || res.status === 204) return { __ok: true, __status: res.status };
    const text = await res.text();
    return text ? JSON.parse(text) : { __ok: true, __status: res.status };
  }
  throw lastErr;
}

const get = (p, o) => request('GET', p, null, o);
const put = (p, b, o) => request('PUT', p, b, o);
const post = (p, b, o) => request('POST', p, b, o);
const del = (p, o) => request('DELETE', p, null, { expectJson: false, ...o });

/**
 * جلب كل الصفحات.
 * §5 — totalCount تلميح مش ضمان؛ بنقف على أول صفحة فاضية كمان.
 */
async function getAll(path, pageSize = 100) {
  const items = [];
  let page = 1;
  for (;;) {
    const sep = path.includes('?') ? '&' : '?';
    const res = await get(`${path}${sep}page=${page}&pageSize=${pageSize}`);
    if (res.__notFound) break;
    const batch = res.items || [];
    items.push(...batch);
    const total = res.totalCount ?? items.length;
    if (batch.length === 0 || items.length >= total) break;
    if (++page > 500) throw new LiferayError(`getAll تجاوز 500 صفحة على ${path}`, { path });
  }
  return items;
}

/* --------------------------- مساعدات المسارات --------------------------- */

/** مجموعة صفوف Object — لازم scoped. §8 */
const scopedPath = (restContextPath) =>
  `${restContextPath.replace(/\/+$/, '')}/scopes/${env.groupId}`;

/** عنصر مفرد بالـ ERC — للمصادر غير site-scoped (زي object-definitions). */
const byErcPath = (restContextPath, erc) =>
  `${restContextPath.replace(/\/+$/, '')}/by-external-reference-code/${encodeURIComponent(erc)}`;

/**
 * عنصر مفرد بالـ ERC داخل site-scoped Object entry.
 * اكتشاف حي 2026-08-16: على qcdev، الـ PUT بالـ ERC بدون scope
 * بيرجع 400 VALIDATION (مش 409/404) — يعني الـ endpoint موجود لكنه
 * بيقرأ الـ payload من غير سياق الموقع. لازم /scopes/{groupId} صراحةً.
 */
const scopedByErcPath = (restContextPath, erc) =>
  `${scopedPath(restContextPath)}/by-external-reference-code/${encodeURIComponent(erc)}`;

/**
 * حذف بالـ ERC.
 * 404 = اتمسح خلاص (ممكن cascade من الأب) = نجاح. §7
 */
async function deleteByErc(restContextPath, erc) {
  // نبدأ بالـ scoped — ده الصح لصفوف الـ Objects.
  try {
    return await del(scopedByErcPath(restContextPath, erc));
  } catch (e) {
    // fallback للمسار المجرّد — للمصادر غير site-scoped (زي object-definitions)
    if (e.status !== 404) throw e;
    return await del(byErcPath(restContextPath, erc));
  }
}

module.exports = {
  LiferayError, request, get, put, post, del, getAll,
  scopedPath, byErcPath, scopedByErcPath, deleteByErc, sleep,
};
