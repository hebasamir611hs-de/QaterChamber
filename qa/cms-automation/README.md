# Qatar Chamber — CMS QA Automation (Phase 1)

تنفيذ خط الأنابيب المعتمد:

```
Phase 0 – Data/Environment Control
  → AC → Scenario Mapping
  → CMS Execution
  → Web Execution
  → Propagation Polling
  → Normalization
  → Cross-System Oracle
  → AC Coverage
  → Cleanup / Restore Verification
```

الأدوار: **QA Orchestrator** + **CMS QA Specialist** + **Web QA Specialist**.
الحكم النهائي ملك الـ Orchestrator وحده.

**الحالة:** Phase 1 كاملة وقابلة للتشغيل. 60 اختبار وحدة ناجح. الـ Web
specialist عقد + adapter جاهز للربط بـ Playwright عندكم.

---

## ⚠️ بند واحد غير مُتحقَّق منه — اقرأه أولاً

**سبب تأخير الانتشار من الـ CMS للموقع لم يُقَس على `qcdev`.**

الفرضية الشائعة (cache الـ portal + إعادة فهرسة Elasticsearch) منقولة من
معرفة عامة بالمنصة، **مش** من قياس حي. ما قدرتش أوصل `qcdev.ihorizons.com`
من بيئة التنفيذ (خارج شبكتكم)، فما ثبّتّش الافتراض.

**اللي عملته بدل كده:**

- آلية الـ polling مبنية وشغّالة — وهي صحيحة **بغض النظر عن السبب**، لأنها
  بتنتظر الشرط نفسه مش بتفترض تفسيراً.
- السبب مُعلَّم `UNVERIFIED` في `lib/propagation.js`.
- `tools/propagation-probe.js` بيقيسه فعلياً.

**المطلوب منكم:**

```bash
node tools/propagation-probe.js --object NewsArticle --page /qatar-chamber --samples 5
```

بيقيس أربع نقاط: زمن الـ PUT، زمن ما يعكس الـ REST القيمة، زمن الـ listing،
زمن ما تعكسها الصفحة. ومن الفروق بينهم بيحدد **أين** التأخير فعلاً:

| الملاحظة | الاستنتاج |
|---|---|
| REST فوري + الصفحة متأخرة | التأخير في طبقة العرض → الـ polling ضروري |
| REST نفسه متأخر | التأخير في الكتابة/الفهرسة، لا في العرض |
| الاتنين متقاربين | مفيش تأخير عرض إضافي — **راجعوا الافتراض من أصله** |

بيطبع كمان `QC_PROPAGATION_TIMEOUT_MS` المناسبة. وثّقوا المخرجات في
`liferay-context.md` كـ `[LIVE]` بالتاريخ.

السكربت بينشئ صف `QCTEST-` ويحذفه دايماً — مش بيلمس أي محتوى تحريري.

---

## التشغيل

```bash
cp .env.example .env      # املأ QC_PASS
npm test                  # 60 اختبار وحدة، بدون شبكة

node tools/preflight.js   # فحص البيئة — لو فشل، لا تكمل
node tools/propagation-probe.js --object NewsArticle --page /qatar-chamber
node scenarios/news-article.slice.js
```

Node 18+. صفر تبعيات.

---

## البنية

```
config/env.js                    كل قيمة بيئة قابلة للتجاوز — لا قيم dev مثبّتة
config/known-objects.json        كتالوج 111 ERC — يُدمج مع الـ listing الحي

lib/rest-client.js               نموذج خطأ موحّد + كل مطبّات المنصة مغلّفة
lib/objects.js                   اكتشاف الـ metadata، ترتيب الحذف، الحقول
lib/erc.js                       هوية الموارد + بوابة عزل بيانات التست
lib/data-ownership.js            Phase 0 — تصنيف الملكية والتعديلات
lib/test-states.js               الحالات الأربع + بوابات الانتقال
lib/normalization-contracts.js   عقد تطبيع لكل نوع حقل
lib/normalize.js                 التحويلات الأولية (HTML، أرقام، عربي، تواريخ)
lib/propagation.js               poll-until-condition — ممنوع sleep ثابت
lib/ac-oracle.js                 AC → التأكيدات اللازمة + قياس التغطية
lib/cleanup-verify.js            إثبات الاسترجاع بالبصمة — لا تسجيل فقط
lib/mutation-log.js              التقاط الحالة السابقة + الاسترجاع LIFO

specialist/cms-specialist.js     عقد قدرات الـ CMS
specialist/web-specialist.js     العقد + adapter جاهز لـ Playwright
orchestrator/qa-orchestrator.js  خط الأنابيب + الحكم

tools/preflight.js               §14 كفحص حي
tools/cleanup.js                 حذف QCTEST-* — الأبناء قبل الآباء
tools/propagation-probe.js       قياس الانتشار (البند غير المُتحقَّق منه)

scenarios/news-article.slice.js  الشريحة الرأسية الأولى
test/                            60 اختبار وحدة
```

---

## 1. Phase 0 — التحكم في البيانات

كل سيناريو **لازم** يعلن ملكية بياناته قبل التنفيذ. سيناريو بدون إعلان =
`BLOCKED`، مش PASS بالصدفة.

| الملكية | المعنى | التنظيف |
|---|---|---|
| `DISPOSABLE` | التست ينشئ الصف ببادئة `QCTEST-` | حذف |
| `TEST_OWNED` | صف موجود مخصَّص للـ QA بالاتفاق | استرجاع |
| `SNAPSHOT_RESTORE` | صف تحريري حقيقي — يتطلب تصريح + سبب | استرجاع |

### تصنيف التعديلات

| التصنيف | متى | النتيجة |
|---|---|---|
| `REVERSIBLE` | يمكن إرجاعه بـ PUT | مسموح |
| `DISPOSABLE` | الصف نفسه سيُحذف | مسموح — حتى لو الحقل غير قابل للتراجع |
| `PROHIBITED` | حقل غير قابل للتراجع على صف غير disposable | **مرفوض** |

القاعدة الحاكمة: عدم قابلية التراجع تبقى غير ضارّة **فقط** على صف
disposable. نفس التعديل على صف موجود = `PROHIBITED`.

استرجاع الـ DB **إجراء طوارئ**، مش جزء من مسار التست. لو سيناريو محتاجه،
السيناريو غلط.

الحقول غير القابلة للتراجع على هذا الـ instance:
- `Boolean` بـ `required: true` — المنصة ترفض إرجاعه لـ `false` (400)
- `Attachment` — الاسترجاع يعيد المعرّف لا الملف؛ الرفع multipart

---

## 2. الحالات الأربع

| الحالة | السؤال |
|---|---|
| `TEST` | إحنا بنختبر إيه؟ |
| `DATA` | إيه البيانات المطلوبة؟ |
| `SYSTEM` | هل الـ CMS حفظ/نشر؟ |
| `PRESENTATION` | هل ظهر للمستخدم صح؟ |

القيمة في **بوابات الانتقال**: `PRESENTATION` مش بتتقيّم أصلاً لو `SYSTEM`
مش SATISFIED — الدالة ما بتشتغلش.

من غير البوابة دي، فشل الكتابة بيتقرأ كعيب في الـ fragment، والتحقيق
بيروح في الاتجاه الغلط. النموذج بيدّي `failureSurface` تلقائياً:

```
توقّف عند SYSTEM       → السطح: cms
توقّف عند PRESENTATION → السطح: web
```

---

## 3. عقود التطبيع

المقارنة بين قيمة الـ CMS والمعروض **ممنوعة بدون عقد**. العقد بيُشتق من
`businessType` في الـ metadata، مش من تخمين اسم الحقل.

| العقد | من | التحويلات المسموحة |
|---|---|---|
| `text` | Text | مسافات، كيانات HTML، أرقام، أشكال عربية |
| `richText` | LongText | + إزالة HTML، اقتطاع |
| `excerpt` | (صريح) | + "…"، احتواء |
| `dateTime` | Date/DateTime | إزاحة توقيت، تنسيق محلي |
| `number` | Integer/Decimal | فواصل آلاف، أرقام عربية، لواحق |
| `url` | Text باسم فيه url/link/redirect | نسبي↔مطلق، شرطة أخيرة، بارامترات تتبّع |
| `boolean` | Boolean | نعم/لا، Yes/No |
| `attachment` | Attachment | معرّف→رابط، بادئة CDN — المقارنة على اسم الملف |
| `localizedText` | أي حقل localized | مفاتيح اللغة + تصنيف العربي |
| `identity` | Relationship | لا شيء — مقارنة صارمة |

أمثلة مغطّاة باختبارات:

```
CMS: 1963                    المعروض: ١٬٩٦٣              ✓ تطابق
CMS: 2026-08-15T09:00:00Z    المعروض: 15/08/2026         ✓ تطابق (Asia/Qatar)
CMS: /qatar-chamber/news/    المعروض: /...news?utm_x=1   ✓ تطابق
CMS: "Qatar Chamber"         المعروض: "Dubai Chamber"    ✗ اختلاف حقيقي
```

### الحقول العربية

`liferay-context §12` بيوثّق ثلاث حالات في البيانات الحية. العقد بيميّزها:

| التصنيف | مثال | السلوك الافتراضي |
|---|---|---|
| `real` | `غرفة قطر` | يُقارن |
| `pending` | `Header Configuration (AR)` | **يُتخطّى** — علامة موثّقة مش باج |
| `corrupt` | `?` | يفشل دائماً — تلف مصدر لا عيب عرض |
| `empty` | | يفشل |

`expect: 'real'` بيخلي `pending` يفشل — للسيناريوهات اللي بتطلب ترجمة فعلية.

---

## 4. AC → Oracle

كل معيار قبول بيعلن **التأكيدات اللازمة لإثباته**:

```js
{ id: 'AC-2',
  description: 'الخبر يظهر في البطاقة وصفحة التفاصيل',
  requiredAssertions: ['cross-system:homepage-title', 'cross-system:detail-title'] }
```

الـ AC ما بيعتبرش مُثبَتاً إلا لما **كل** تأكيداته تنجح فعلياً — مش لما
الخطوة اللي بتحمل الـ id بتاعه تنجح.

الفرق مش شكلي: خطوة واحدة ممكن تحمل ٥ تأكيدات وتُعلَن PASS والتأكيد الخاص
بالـ AC مكانش اتنفّذ أصلاً. مغطّى باختبار.

`PASS` بتغطية ناقصة **ممنوع** — الحكم بيبقى `BLOCKED`.

---

## 5. التحقق من التنظيف

سجل التعديلات بيقول "نفّذت الاسترجاع". ده مش نفس "البيئة رجعت".

بصمة قبل/بعد لكل Object. أي فرق = الـ run بيتعلّم `DIRTY` حتى لو كل
التستات نجحت.

| النتيجة | المعنى |
|---|---|
| `CLEAN` | مطابقة تامة |
| `DIRTY` | صفوف زايدة — تنظيف ناقص |
| `DATA_LOSS` | صفوف أصلية اختفت — **حاجب**، استرجاع DB |

على بيئة مشتركة، الأداة بتميّز الصفوف الزايدة اللي **مش** بتحمل بادئة
التست وبتصنّفها `foreignChanges` — شغل حد تاني، مش تنظيف ناقص منّكم.

---

## 6. مطبّات المنصة المغلّفة

من `liferay-context.md`. كل واحدة كانت هتكسر الإطار بصمت:

| المطبّ | لو اتجاهلناه | المعالجة |
|---|---|---|
| الـ Objects site-scoped | المسار المجرّد يرجع **409 مش 404** → يُقرأ كـ "لا بيانات" | `scopedPath()` + خطأ صريح |
| `pageSize >= 99` على object-definitions | 404 وهمي → الاكتشاف يفشل كلياً | السقف 50 |
| الـ listing يخفي Objects سليمة | صفوف تست تبقى والبصمة تقول CLEAN | دمج `known-objects.json` |
| مفاتيح اللغة `en_US` مقابل `en-US` | مقارنات تفشل عشوائياً | تُقرأ الصيغتان |
| `?filter=` يرمي URISyntaxException | — | غير مستخدم — جلب + فلترة محلية |
| `curl` يفسد العربي | بيانات تست عربية تُخزَّن غلط | `node fetch` فقط |

**العلاقات:** ٣ فقط عبر الـ 111 Object. الترتيب محسوب من العلاقات الحية،
فلو الديفيلوبرز ضافوا علاقة بيتصحّح لوحده. `preflight` بيحذّر لو العدد
اتغيّر.

---

## 7. حدود معروفة

- **Fragments مش في الـ REST** على هذا الإصدار — أي تحقق من العرض لازم
  Playwright. مفيش بديل.
- **Content Structures** (٦ فقط) — GET-only.
- **الـ Web specialist** عقد + adapter، مش تنفيذ. يُربط بـ repo الـ
  Playwright عندكم.
- **`qcdev` بيئة مشتركة** — `liferay-context §1` بيقول إنها
  *"actively being worked on by other people/pipelines"*. التحقق من التنظيف
  بيميّز تغييراتهم عن تغييراتكم، لكنه مش بيمنع تداخل النتائج.

---

## الخطوة التالية

1. `npm test` — يمشي بدون شبكة
2. `node tools/preflight.js` — من داخل الشبكة
3. `node tools/propagation-probe.js` — **البند غير المُتحقَّق منه**؛ وثّقوا النتيجة
4. اربطوا الـ Playwright adapter وعدّلوا المحدِّدات في
   `scenarios/news-article.slice.js` على الـ DOM الحقيقي
5. شغّلوا الشريحة كاملة → لازم تطلع `PASS` بتغطية 100%

قبل نقطة 5 ما تنجحش، **متوسّعوش لأي Object تاني**.
