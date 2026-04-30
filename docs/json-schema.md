# JSON Schema

Schema lives at `public/schemas/chat-viz.schema.json`.

## Required top-level keys

- `meta`
- `people`
- `metrics`
- `slides`
- `customization`

## Notes

- `people` must contain at least 2 entries.
- `metrics.languageShare` is expressed in percentages from `0` to `100`.
- `customization.relationshipType` must be one of:
  - `romantic`
  - `friendship`
  - `family`
- `customization.startDate` and `customization.endDate` use `YYYY-MM-DD`.

## Example

Use `public/schemas/schema-example.json` as a template.
