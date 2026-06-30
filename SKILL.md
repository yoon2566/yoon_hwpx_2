---
name: yoon-hwpx-2
description: Safe Korean HWPX document workflow for Codex. Use when working with Hangul/HWPX files, preserving original Korean document forms, splitting pages or sections, editing text nodes or table cells, removing hp:linesegarray warnings, validating HWPX ZIP/XML structure, or troubleshooting Hancom damage/security warnings caused by stale layout caches, generic ZIP rewrites, preview-cache edits, or section/package drift without using local Hancom Office.
---

# Yoon HWPX 2

Use this skill for `.hwpx` only. Do not create or directly edit legacy binary `.hwp` files.

## Core Rules

- Never modify the original HWPX in place.
- Treat HWPX as a ZIP/XML package.
- Preserve the original form: section structure, tables, merged cells, margins, styles, images, and ZIP entry order whenever possible.
- Prefer changing only `hp:t` text nodes in `Contents/section*.xml`.
- Remove `hp:linesegarray` after text edits, page splits, or content moves.
- For final files that must open in Hancom, prefer raw ZIP-preserving tools in `scripts/hwpxskill/` over generic `ZipFile` rewriting.
- Do not update `Preview/PrvText.txt` or `Preview/PrvImage.png` unless the user explicitly asks; stale previews are less risky than repackaging damage.
- When a single-section split or edited output validates but Hancom reports damage, rebuild from the closest preserve-sections source and edit only the target section/paragraphs.
- Do not use `Hwp.exe`, Hancom COM automation, GUI conversion, or local Hancom Office.
- Do not claim success without validation logs.
- If the user has a top-level project/result folder rule, create a numbered top-level subfolder and place deliverables plus logs there.

## Bundled Scripts

- `scripts/hwpxskill/`: full workflow tools from `hwpxskill`.
  - `validate.py`: structural ZIP/XML validation.
  - `text_extract.py`: text extraction.
  - `analyze_template.py`: style/table/section analysis.
  - `hwpx_slots.py`: editable slot extraction.
  - `edit_hwpx.py`: original-form and raw ZIP-preserving text/cell/slot edits. Prefer this for Hancom-facing final deliverables.
  - `finalize_hwpx.py`: raw ZIP-preserving `hp:linesegarray` stripping and layout-risk checks. Prefer this over ad hoc ZIP rewrites.
  - `page_guard.py`: reference-vs-output structure and page-drift guard.
  - `content_guard.py`: required/forbidden content checks.
- `scripts/yoon-safe/`: lightweight safe-edit tools from `yoon_hwpx`; useful for analysis, drafts, and controlled text-node edits, but not the first choice when Hancom has already shown damage warnings.
  - `analyze_hwpx.py`, `extract_text_map.py`, `apply_text_map.py`, `remove_linesegarray.py`, `validate_hwpx.py`.
- `scripts/extract_page3.py`: section-child extraction utility. Defaults to the culture-center third-page range but accepts `--source-section` and `--children`.

## References

Read these only when needed:

- `references/hwpx-format.md`: OWPML/HWPX XML format details.
- `references/yoon-02-hwpx-structure.md`: compact HWPX package structure notes.
- `references/yoon-03-safe-edit-workflow.md`: safe text-node editing workflow.
- `references/yoon-04-linesegarray-warning.md`: Hancom warning caused by stale `hp:linesegarray`.
- `references/yoon-06-troubleshooting.md`: common HWPX failure modes.
- `references/yoon-07-hancom-damage-recovery.md`: recovery workflow for files that validate but Hancom says are damaged.

## Windows Setup

Use the workspace `.venv`; create it if missing. Do not install packages globally.

```powershell
if (-not (Test-Path -LiteralPath ".\.venv\Scripts\python.exe")) {
  python -m venv .venv
}
.\.venv\Scripts\python.exe -m pip install lxml
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
```

## Inspect A Source HWPX

Run both validators when possible.

```powershell
$py = ".\.venv\Scripts\python.exe"
$skill = "C:\Users\User\.codex\skills\yoon-hwpx-2"
$src = "input.hwpx"

& $py "$skill\scripts\hwpxskill\validate.py" $src
& $py "$skill\scripts\yoon-safe\validate_hwpx.py" $src
& $py "$skill\scripts\hwpxskill\text_extract.py" $src --format markdown | Out-File ".\source_text.md" -Encoding UTF8
& $py "$skill\scripts\yoon-safe\extract_text_map.py" $src --output ".\source_text_map.json"
```

## Split A Page Or Section Range

HWPX does not always store physical pages directly. First inspect sections and top-level child ranges, then extract the range that corresponds to the visible page.

```powershell
$py = ".\.venv\Scripts\python.exe"
$skill = "C:\Users\User\.codex\skills\yoon-hwpx-2"
$src = "source.hwpx"

& $py "$skill\scripts\extract_page3.py" $src --inspect | Out-File ".\structure_inspect.json" -Encoding UTF8
```

For the culture-center original where page 3 is the lower lecture plan:

```powershell
& $py "$skill\scripts\extract_page3.py" $src `
  --mode single-section `
  --source-section "Contents/section1.xml" `
  --children "12-23" `
  --output ".\page3_lower_plan.hwpx" `
  --report ".\page3_lower_plan_report.json"

& $py "$skill\scripts\yoon-safe\validate_hwpx.py" ".\page3_lower_plan.hwpx" --expect-no-linesegarray |
  Out-File ".\page3_lower_plan_validate.json" -Encoding UTF8
```

If Hancom is sensitive to removing section entries, create a fallback:

```powershell
& $py "$skill\scripts\extract_page3.py" $src `
  --mode preserve-sections `
  --source-section "Contents/section1.xml" `
  --children "12-23" `
  --output ".\page3_lower_plan_preserve_sections.hwpx" `
  --report ".\page3_lower_plan_preserve_sections_report.json"
```

## Edit Existing Text Safely

For Hancom-facing final files, use slot/paragraph editing through `scripts/hwpxskill/edit_hwpx.py` first because it preserves raw ZIP records for unchanged entries. Use `scripts/yoon-safe/apply_text_map.py` mainly for lightweight text-node edits, drafts, or cases where Hancom compatibility has not been fragile.

```powershell
$py = ".\.venv\Scripts\python.exe"
$skill = "C:\Users\User\.codex\skills\yoon-hwpx-2"
$src = "source.hwpx"

& $py "$skill\scripts\hwpxskill\hwpx_slots.py" $src --output ".\slots.json"
# Prepare values.json with keys from slots.json.
& $py "$skill\scripts\hwpxskill\edit_hwpx.py" $src --output ".\edited.hwpx" --slot-json ".\values.json"
& $py "$skill\scripts\hwpxskill\finalize_hwpx.py" ".\edited.hwpx" --strip-linesegarray --layout
& $py "$skill\scripts\yoon-safe\validate_hwpx.py" ".\edited.hwpx" --expect-no-linesegarray
```

## Hancom Damage Warning Recovery

If XML/ZIP validation passes but Hancom reports damage:

1. Stop editing the same output.
2. Read `references/yoon-07-hancom-damage-recovery.md`.
3. Rebuild from the original or a `preserve-sections` source, not from a previously repackaged output.
4. Use `scripts/hwpxskill/edit_hwpx.py` with `--slot-json` or `--paragraph-json`.
5. Use `scripts/hwpxskill/finalize_hwpx.py --strip-linesegarray --layout`.
6. Leave preview files untouched unless preview refresh is explicitly required.
7. Validate and save text/content comparison logs next to the final HWPX.

## Validation Checklist

Before final response:

- Confirm output path and file size.
- Save analysis/report JSON next to the HWPX output.
- Validate first ZIP entry is `mimetype`.
- Validate required entries and XML well-formedness.
- Validate `hp:linesegarray` count is `0` after edits or moved content.
- Extract output text and confirm only intended content remains or changed.
- Confirm output was produced from a raw ZIP-preserving path when Hancom compatibility matters.
- Confirm preview files were not rewritten casually.
- Keep fallback outputs clearly labeled, such as `단일섹션` and `구조유지`.
