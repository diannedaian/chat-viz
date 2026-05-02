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

## Deploying on Vercel

This repo is a **static site at the repository root** (`index.html`, `viewer.html`, `parser.html`, `src/`, `public/`). A tiny `package.json` exists only so Vercel can run a no-op `npm run build` and use **`outputDirectory: "."`** in `vercel.json` (avoids empty `dist/` style output folders).

In the Vercel project **Settings → General**:

1. **Root Directory** — leave **empty** (must **not** be `apps/web` or any old path; that folder no longer exists).
2. **Framework Preset** — **Other** is fine.
3. **Build Command** / **Output Directory** — prefer leaving them **unset** in the dashboard so `vercel.json` controls them; if you override in the UI, match the repo: build `npm run build`, output **`.`** (repo root).

Redeploy after changing Root Directory. If you still see `404: NOT_FOUND`, open the deployment in Vercel → **Source** and confirm `index.html` appears at the top level of the deployed files.

## Legacy

`scripts/generate_report.py` and `report/report.html` are deprecated and preserved for reference. Original standalone HTML prototypes live in `legacy/standalone/`.
