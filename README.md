# Kitchen Crib Sheet

A cooking reference for dishes you already know. Keep the amounts and short reminders in Markdown, then build a printable, single-page PDF.

This started as the sheet I tape inside the kitchen cupboard over my stove. An agent helps maintain the wording and layout; a renderer checks that the result fits on paper.

- Canonical Markdown with explicit column groups.
- Standalone HTML and a fragment for in-app previews.
- US Letter or A4 PDF with black text on white, grayscale icons, and a dated footer.
- Layout and text checks before replacing the last successful output.
- No account, API key, browser, or network request needed at build time.

[Download my finished cupboard sheet (PDF)](https://github.com/jwulff/kitchen-crib-sheet/releases/download/v0.1.0/wulff-kitchen-crib-sheet.pdf). It is a personal reference, including my shorthand and unresolved placeholders, rather than a tested recipe collection. The starter example below is separate.

## Install and try it

Requires Python 3.10 or newer and Pango. On macOS, install native dependencies with `brew install pango poppler`; on Ubuntu, use `sudo apt-get install libpango-1.0-0 libpangoft2-1.0-0 poppler-utils fonts-liberation`. Poppler is for visual review.

```sh
git clone https://github.com/jwulff/kitchen-crib-sheet.git
cd kitchen-crib-sheet
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp examples/crib-sheet.md my-recipes.md
.venv/bin/python scripts/build.py my-recipes.md --out output --timezone America/Los_Angeles
```

Open `output/crib-sheet.html` or print `output/crib-sheet.pdf` at 100%. The example is intentionally small. Add your own recipes and rebalance groups as the page fills up. Builds work offline once dependencies are installed. macOS has been exercised locally; Linux is covered by the included CI workflow. Windows has not been tested.

To use the agent instructions, place or symlink this entire directory in your agent's skill directory. For a local Codex installation:

```sh
mkdir -p ~/.codex/skills
ln -s "$(pwd)" ~/.codex/skills/kitchen-crib-sheet
```

The scripts also work without an agent. Use the supplied `SKILL.md` as the entrypoint in other skill-compatible hosts; install locations vary.

Example request:

> Use kitchen-crib-sheet to add my dressing to my-recipes.md: lemon 1T, olive oil 3T, salt and pepper. Keep it in the prep column. Show me the HTML before making a PDF.

## Source format

```markdown
# Kitchen Crib Sheet

<!-- recipes:start -->
## Prep
### 🍋 Lemon Dressing
- Lemon juice, 1T
- Olive oil, 3T
- Salt & pepper
- Shake together
<!-- recipes:end -->

Source notes and longer explanations go here, outside the printable block.
```

One to four groups become columns. Each recipe needs a unique title and a nonempty bullet list. Plain text and `[[Page|label]]` links are supported; arbitrary Markdown, HTML, and embedded resources are rejected or escaped. Content outside the markers is omitted from the product, but is still present in the source file you share.

The renderer preserves values, including uncertain placeholders. It cannot check recipe correctness. The agent should ask about meaningful ambiguities instead of guessing what you meant.

## Build options and review

```sh
.venv/bin/python scripts/build.py my-recipes.md --out output --preview-only
.venv/bin/python scripts/build.py my-recipes.md --out output --date 2026-09-06 --paper a4
.venv/bin/python scripts/build.py my-recipes.md --out output --widths .96,.96,1.04,1.04
pdftoppm -scale-to 1800 -png -singlefile output/crib-sheet.pdf output/check
```

`--widths` takes one positive weight per column. The date defaults to today in UTC; choose an IANA time zone with `--timezone`. Date selection is stable with `--date`; PDF bytes may vary by platform and installed fonts.

Every full build checks pagination, page dimensions, printable bounds, and extracted recipe text. Overfull or malformed input fails before replacing prior outputs. Reword or rebalance; do not silently drop content or reduce everything to unreadable type.

`build.json` records the source hash, date, recipe count, output hashes, and whether a PDF was built. `visual_review: pending` is intentional: a person or agent must inspect a rendered page, especially icon sizing and clipping. Preview-only builds leave any previous PDF alone and mark `pdf_validated: false` in the new receipt.

Icons are embedded as explicitly sized grayscale images to avoid differences in operating-system emoji fonts. Only the [bundled set](assets/emoji/README.md) is supported; a plain title always works. Twemoji attribution travels with generated documents that use those icons.

## Development

```sh
.venv/bin/python -m unittest discover -s tests -v
```

The renderer is pinned to WeasyPrint 69.0 because its layout inspection uses an internal box API. Review the PDF and rerun tests when upgrading it. Contributions should include a small source that demonstrates any layout or text-preservation bug. Keep personal recipes, credentials, generated output, and local environment paths out of contributions.

The optional [private-to-oss skill](skills/private-to-oss/SKILL.md) captures the workflow used to turn a personal skill into a distributable one, with a release record template.

## Inspiration and license

The packaging draws on [archify](https://github.com/tt-a1i/archify) for a skill backed by a concrete renderer, [humanizer](https://github.com/blader/humanizer) for focused editing instructions, and [last30days-skill](https://github.com/mvanhorn/last30days-skill) for separating the skill entrypoint from its runtime and setup. This implementation does not copy their code or prompts.

Code and documentation: [MIT](LICENSE). Bundled Twemoji graphics: [CC BY 4.0](assets/emoji/LICENSE-GRAPHICS), attributed to Twitter, Inc. and other contributors. Source icons are unchanged; generated icons are converted to grayscale. See the [asset notice](assets/emoji/README.md).
