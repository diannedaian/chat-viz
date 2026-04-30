# Migration Notes

## What changed

- New app entrypoints:
  - `apps/web/index.html` (landing + upload)
  - `apps/web/parser.html` (WhatsApp parser/export)
  - `apps/web/viewer.html` (phone-viewer)
- Shared source modules now live under `src/`.
- JSON schema and examples are under `public/schemas/`.

## Legacy status

- `Dianne x Yifan.html` remains as the original standalone prototype.
- Python report generation is deprecated for this workflow.
- Existing `scripts/generate_report.py` and `report/` are preserved for reference only.

## Recommended next extension

- Add provider-specific parser adapters (`wechatParser`, `imessageParser`) that emit the same normalized event model as `whatsappParser`.
