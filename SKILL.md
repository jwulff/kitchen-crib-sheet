---
name: kitchen-crib-sheet
description: Maintain a compact cooking crib sheet in Markdown, preview printable HTML, and generate a verified one-page PDF for recipes the user already knows.
---

# Kitchen Crib Sheet

The user already knows how to cook these dishes. Preserve short reminders of amounts, order, time, and temperature. Do not expand them into tutorials or invent missing quantities. Keep ambiguities until the user resolves them.

## Maintain the source

Read the existing Markdown before editing. Use [examples/crib-sheet.md](examples/crib-sheet.md) only to start a new sheet. The printable block has one `recipes:start/end` marker pair, one to four `##` column groups, `###` recipe titles, and flat `- ` lines. The `#` heading supplies the sheet title. Notes and provenance belong outside the markers. They remain in the shared Markdown, so review them before distributing it.

Group by how the cook looks things up, then balance complete recipes across columns. Shorten wording before shrinking type. Preserve amounts, units, temperatures, times, and meaningful ingredient qualifiers. Do not delete recipes to force a one-page fit. Titles have no numbering; use a fitting supported emoji when useful, or leave a title plain. See [assets/emoji/README.md](assets/emoji/README.md) for the bundled set.

## Render

Run from this skill's directory using the Python environment described in [README.md](README.md). Keep the user's source and output paths explicit.

```sh
.venv/bin/python scripts/build.py /path/to/crib-sheet.md --out /path/to/output --timezone America/Los_Angeles
```

Use `--preview-only` when the user asks to see a revision or pauses PDF generation. `preview.html` is an embeddable fragment; `crib-sheet.html` is standalone. Show the actual artifact through the host's supported preview/file mechanism. A localhost URL usually will not work on a remote phone.

A final print request ends with `crib-sheet.pdf`. Default: US Letter portrait, white background, black text, grayscale fixed-size icons, 0.35-inch margins, generation date. `--paper a4`, `--date YYYY-MM-DD`, and relative `--widths .96,.96,1.04,1.04` are optional. The icon attribution must remain when Twemoji assets are used.

## Verify and deliver

The builder checks one page, paper size, printable bounds, and every recipe line before replacing outputs. A failure leaves the previous outputs intact. Read `build.json` to distinguish a fresh PDF from an older file left by a preview-only run.

Then render the actual PDF, for example:

```sh
pdftoppm -scale-to 1800 -png -singlefile /path/to/output/crib-sheet.pdf /path/to/output/check
```

Inspect that page: all recipes present, no clipping, readable type, balanced columns, normal-sized aligned icons, and dated footer. Browser appearance is insufficient evidence for PDF emoji sizing. If the host cannot inspect a PDF or page image, report visual review as incomplete. Deliver the PDF only as verified after inspecting it; automated checks alone do not establish visual quality.

For printing, use the PDF at 100% scale. Archive or publish only as requested, using the user's chosen service; no cloud account is required by this skill.
