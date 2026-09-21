# Receipt Organizer

A small, local-first command-line application for recording, finding, summarizing, and exporting receipt records. It stores data in SQLite, uses integer cents for money, keeps currencies separate in reports, and requires no cloud service or runtime dependency.

## Why it exists
Receipts often end up scattered across notes and spreadsheets. Receipt Organizer provides a predictable local database and automation-friendly CLI without requiring an account or sending financial records anywhere.

## Features
- Add receipts with purchase date, merchant, amount, ISO-style currency code, category, and note.
- Search merchant/note text and filter by category, currency, and date range.
- Exact decimal handling: values are normalized to two decimal places and stored as integer cents.
- Spending summaries grouped by currency and category; different currencies are never silently combined.
- JSON output for list/show/summary workflows.
- Export filtered data as JSON or standards-compliant CSV.
- SQLite indexes for date and merchant lookups, WAL mode, and parameterized SQL.
- Safe export behavior: existing files are not replaced unless `--force` is supplied.
- Local-only operation; no telemetry, API keys, or network calls.

## Requirements
Python 3.10 or newer. SQLite support is included with normal CPython distributions.

## Installation
```bash
git clone https://github.com/rad03i2/receipt-organizer.git
cd receipt-organizer
python -m pip install -e .
receipt-organizer --version
```

## Usage
```bash
# Add a receipt
receipt-organizer add --date 2026-09-21 --merchant "Corner Shop" --amount 12.50 --currency USD --category Food --note "Lunch"

# List and search
receipt-organizer list
receipt-organizer list --search corner --currency USD --since 2026-09-01
receipt-organizer list --json

# Inspect/delete a record
receipt-organizer show 1 --json
receipt-organizer delete 1

# Totals are reported independently per currency
receipt-organizer summary --since 2026-09-01
receipt-organizer summary --json

# Export
receipt-organizer export --format csv --output receipts.csv
receipt-organizer export --format json --output receipts.json
```

### Configuration
By default the database is stored under `%LOCALAPPDATA%/receipt-organizer/receipts.db` on Windows, or `~/.local/share/receipt-organizer/receipts.db` elsewhere. Override it per command with `--db PATH`, or set `RECEIPT_ORGANIZER_DB`.

No `.env` file is required because the application has no secrets or external services.

## Project structure
```text
src/receipt_organizer/
  __init__.py   package metadata
  core.py       validation, SQLite storage, filtering, summaries, exports
  cli.py        command-line interface
tests/
  test_core.py  functional storage/validation/export tests
.github/workflows/ci.yml
pyproject.toml
```

## Testing
```bash
python -m pip install -e .
python -m unittest discover -s tests -v
```
CI runs the same tests on Python 3.10, 3.12, and 3.13 across Ubuntu, Windows, and macOS.

## Preview / screenshots
This is intentionally a terminal application. A useful repository screenshot should show `add`, `list`, and `summary` output with invented non-sensitive sample receipts. Do not publish screenshots containing real financial information.

## Security & privacy
Records remain on the local machine. SQL values are parameterized and exports require explicit overwrite permission. The SQLite database is **not encrypted**, so do not treat it as a secret vault; protect the device/account and backups appropriately. See [SECURITY.md](SECURITY.md).

## Limitations
- It records structured receipt information; it does not OCR images or parse PDFs.
- It does not perform currency conversion, tax calculation, budgeting, or accounting reconciliation.
- Amounts use two decimal places. This is appropriate for many currencies but not every possible monetary unit.
- There is no GUI, cloud sync, attachment store, or encrypted database.
- Import is intentionally not implemented yet; JSON/CSV exports are for portability and downstream processing.

## Optional roadmap
Possible future work includes receipt-image attachments, explicit import with duplicate detection, configurable currency minor units, and an optional desktop interface. These are not claimed as current features.

## Contributing
See [CONTRIBUTING.md](CONTRIBUTING.md). Keep changes focused, tested, dependency-light, and privacy-preserving.

## License
MIT — see [LICENSE](LICENSE).

## Author
**Radwan Abdulhadi Ahmed**  
**رضوان عبدالهادي أحمد**  
GitHub: **@rad03i2**

---

# منظم الإيصالات — العربية

أداة سطر أوامر محلية وصغيرة لتسجيل بيانات الإيصالات والبحث فيها وتلخيص المصروفات وتصديرها. تحفظ البيانات في SQLite، وتخزن المبالغ بوحدات صحيحة بعد ضبط منزلتين عشريتين، ولا تجمع العملات المختلفة في إجمالي مضلل، ولا تحتاج إلى خدمة سحابية أو تبعيات تشغيل خارجية.

## لماذا هذا المشروع؟
غالبًا ما تتوزع بيانات الإيصالات بين الملاحظات والجداول. يوفر المشروع قاعدة بيانات محلية منظمة وواجهة أوامر مناسبة للاستخدام اليدوي والأتمتة، من دون حساب أو إرسال البيانات المالية إلى أي جهة.

## الميزات
- إضافة التاريخ والتاجر والمبلغ والعملة والتصنيف والملاحظة.
- البحث في اسم التاجر والملاحظات، مع التصفية حسب التصنيف والعملة والفترة الزمنية.
- معالجة عشرية دقيقة وتخزين المبلغ كعدد صحيح من الوحدات الصغرى.
- ملخصات حسب العملة والتصنيف، مع إبقاء العملات منفصلة دائمًا.
- مخرجات JSON للأوامر المناسبة.
- تصدير JSON وCSV مع إمكانية التصفية.
- SQLite مع فهارس للتاريخ والتاجر واستعلامات ذات معاملات آمنة.
- عدم استبدال ملف التصدير الموجود إلا عند استخدام `--force`.
- تشغيل محلي بلا تتبع أو مفاتيح API أو اتصالات شبكية.

## المتطلبات والتثبيت
يتطلب Python 3.10 أو أحدث.
```bash
git clone https://github.com/rad03i2/receipt-organizer.git
cd receipt-organizer
python -m pip install -e .
```

## أمثلة الاستخدام
```bash
receipt-organizer add --date 2026-09-21 --merchant "متجر محلي" --amount 15.25 --currency USD --category Food
receipt-organizer list --since 2026-09-01
receipt-organizer list --json
receipt-organizer summary
receipt-organizer export --format csv --output receipts.csv
```
يمكن تغيير قاعدة البيانات باستخدام `--db PATH` أو متغير البيئة `RECEIPT_ORGANIZER_DB`. لا يوجد ملف `.env` لأن المشروع لا يحتاج أسرارًا أو خدمات خارجية.

## بنية المشروع والاختبارات
الكود داخل `src/receipt_organizer`، والاختبارات داخل `tests`، وملف CI داخل `.github/workflows`. لتشغيل الاختبارات:
```bash
python -m unittest discover -s tests -v
```
ويختبر CI الإصدارات 3.10 و3.12 و3.13 على Linux وWindows وmacOS.

## المعاينة
لأن المشروع أداة طرفية، يفضل أن تعرض لقطة المشروع أوامر `add` و`list` و`summary` باستخدام بيانات تجريبية غير حساسة فقط.

## الخصوصية والأمان
البيانات تبقى على الجهاز، والاستعلامات تستخدم معاملات SQL، ولا يتم استبدال ملفات التصدير دون إذن صريح. قاعدة SQLite **غير مشفرة**؛ لذلك يجب حماية حساب الجهاز والنسخ الاحتياطية، وعدم اعتبار البرنامج مخزنًا للأسرار. راجع [SECURITY.md](SECURITY.md).

## القيود
لا يقوم المشروع حاليًا بقراءة صور الإيصالات أو PDF أو OCR، ولا يحول العملات أو يحسب الضرائب، ولا يوفر واجهة رسومية أو مزامنة سحابية أو تخزين مرفقات أو تشفيرًا لقاعدة البيانات. المبالغ مضبوطة على منزلتين عشريتين، والتصدير متوفر بينما الاستيراد غير منفذ حاليًا.

## تطوير اختياري مستقبلًا
يمكن إضافة مرفقات الصور، واستيراد مضبوط مع كشف التكرار، ودعم عدد منازل عشرية قابل للتهيئة، وواجهة سطح مكتب. هذه أفكار مستقبلية وليست ميزات حالية.

## المساهمة والترخيص
راجع [CONTRIBUTING.md](CONTRIBUTING.md). المشروع مرخص برخصة MIT الموجودة في [LICENSE](LICENSE).

## المؤلف
**Radwan Abdulhadi Ahmed**  
**رضوان عبدالهادي أحمد**  
GitHub: **@rad03i2**
