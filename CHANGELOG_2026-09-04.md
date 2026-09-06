# ملخص الشغل — إصدار 2026-09-04

ملخص لكل التعديلات اللي اتعملت على أتمتة اختبارات Control_Panel (Liferay CMS)
للصفحة الرئيسية (Home Page) وشاشة GM Message، قبل رفعها بفرجن جديدة.

## أهم حاجة اتضافت: Object Authoring Page Object جديد
- ملف جديد: [cms/pages/components/object_authoring_page.py](cms/pages/components/object_authoring_page.py)
- بيمثّل شاشة `object-authoring -> manage-<slug>` اللي هي مسار Draft /
  Submit for Review / Publish / Unpublish الحقيقي لأي Object Definition —
  ده اتكتشف إنه بديل عن الـ Object Definitions Editor الخام، اللي معظم
  الـ Objects عليه مفيش عليها Workflow أصلاً (زي Promotional Banner، News
  Article... إلخ).
- استُخدم عشان يفك الـ block اللي كان قافل TC 135279 (Latest News) بعد ما
  كانت متسكّنة (skipped) بسبب "No Workflow" على الـ Object Definition
  الخام.

## تعديلات على Admin Page Objects (cms/pages)
- **home_community_partners_admin_page.py** — استكمال شغل من سيشن سابقة
  انقطعت (خطأ اتصال أثناء اختبار رفع اللوجو)، مع توثيق كامل لكل حقل
  وأي اختلاف بين خطوات الحالة الأصلية (Test Case) والسلوك الحقيقي في
  المنتج.
- **home_featured_event_admin_page.py** — تأكيد Bug حقيقي بالمنتج: حقل
  `pinnedEvent` في الـ Upcoming Event Pins مبيغيّرش الكارت الظاهر فعليًا
  في الـ Home Page (اتجرب بقيمتين حقيقيتين مختلفتين ومازال مفيش تغيير).
- **home_latest_news_admin_page.py** — أكبر تعديل (280+ سطر): ربط الصفحة
  بالمسار الجديد `object-authoring` بدل المسار القديم المسدود.
- **home_promo_banners_admin_page.py** (370+ سطر) و **home_services_admin_page.py**
  (290+ سطر) — توسعة كبيرة لتغطية باقي حالات PBI 129368 و PBI 129371،
  مبنية على فحص حي (live) لشاشة الـ Workflow في Liferay Site Administration.

## تعديلات على ملفات الاختبارات (cms/tests)
- اختبارات جديدة/موسّعة لـ: Community Partners (PBI 129385)، Featured
  Event/Pinned Event (PBI 129382)، Latest News (PBI 129372)، Promo
  Banners (PBI 129368)، Home Services (PBI 129371)، Strategic Direction
  (PBI 129381)، وGM Message (PBI 129397).
- كل حالة موثّق فيها: مصدر النص الأصلي من Azure DevOps، وأي انحراف/تعديل
  عن نص الحالة الأصلي (disclosed substitution) بدل ما يتلخبط الاختبار مع
  المنتج بصمت.
- صور fixtures جديدة مُستخدمة فعليًا في اختبارات الرفع (upload):
  `news_thumbnail.png`, `promo_banner.png`, `promo_banner_v2_qctest.png`,
  `service_card.png`.

## pytest.ini
- إضافة marker جديد `media` (لتغطية News/Media Gallery/Podcast/Publications).
- إضافة markers جديدة لـ Axis 4 (`workflow`, `svc`, `uat`) وPBI جديدة
  (`pbi_129371`, `pbi_129372`) وعشرات الـ `tc_<id>` الجديدة لتتبع كل
  Test Case حقيقي اتكتب أو اتصلّح حالته (من SKIPPED لحالة اتكتبت فعلاً،
  أو العكس بسبب اكتشاف Bug حقيقي).

## تعديلات على web/pages (اختبارات الموقع العام Public Web)
- Home Community Partners / Latest News / Promo Banners / Home Services —
  تحديثات مرتبطة بنفس الـ PBIs فوق للتأكد من ظهور المحتوى صح في الصفحة
  العامة بعد أي تعديل في الـ CMS.

## .claude/context/active/standards.md
- توثيق قسم جديد: "Object Authoring — Draft / Preview / Publish /
  Unpublish Lifecycle" (المسار البديل المكتشف ده، عشان أي شغل جاي بعد
  كده يستخدمه بدل ما يكتشفه من الأول).

## حاجات اتسابت من غير ما تترفع (scratch/debug فقط)
- كل ملفات `scratch_*` و`bug_evidence_*` (سكرين شوتس وسكريبتات فحص مؤقتة)
  ومجلدات `.allure-results-*` — دي مخرجات تشغيل محلية مش جزء من الكود.
- `.claude/settings.json` — إعدادات صلاحيات محلية على الجهاز، متسيبتش
  عمدًا برا الـ commit ده (فيه `.claude/settings.local.json` بالفعل في
  gitignore لنفس السبب؛ لو الفريق عايز يشاركها لازم قرار منفصل).
