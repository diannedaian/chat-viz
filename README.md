# Chat Viz Project

Turn exported chats into a polished, phone-style relationship story viewer.

## Frontend entry points

- `index.html`: landing page (upload + parse-and-tweak flow)
- `viewer.html`: animated phone viewer + customization card + standalone HTML download
- `parser.html`: optional advanced parser page

## Primary workflow

1. Open `index.html`.
2. Pick one input:
   - Upload ChatViz JSON, or
   - Upload WhatsApp TXT.
3. Click **Parse and tweak** to open `viewer.html` with parsed data loaded.
4. Customize in the viewer and optionally click **Download standalone HTML**.

## Data and privacy

- Personal chat history files are ignored via `.gitignore` (for safe GitHub publishing).
- Example schema files are in `public/schemas/`.
- Avoid committing raw personal exports if they contain private conversations.

## Project structure

- `index.html`, `viewer.html`, `parser.html` - flat static frontend entry points for Vercel
- `src/parser/` - WhatsApp parser + data builder
- `src/shared/` - schema validation and shared logic
- `src/data/` - default demo data
- `public/schemas/` - JSON schema and example payloads
- `docs/` - documentation and migration notes
- `legacy/` - deprecated reference artifacts and standalone prototypes

## Legacy

`scripts/generate_report.py` and `report/report.html` are deprecated and preserved for reference. Original standalone HTML prototypes live in `legacy/standalone/`.
