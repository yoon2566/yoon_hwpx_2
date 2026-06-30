# yoon-hwpx-2

AI-friendly Codex skill for safe Korean HWPX work.

This repository is meant to help an AI agent quickly understand how to work with
Hangul `.hwpx` files without damaging the original form.

## What This Skill Is For

Use `yoon-hwpx-2` when a task involves:

- Korean Hangul `.hwpx` files
- preserving an original document form
- splitting a page or section from an HWPX
- editing text nodes or table cells
- removing stale `hp:linesegarray` layout caches
- validating HWPX ZIP/XML structure
- troubleshooting Hancom damage, tamper, or security warnings

Do not use it to directly create or edit legacy binary `.hwp` files.

## Main Rule For AI Agents

Do not rebuild a lookalike document.

Start from the user's original `.hwpx`, preserve the ZIP/XML package structure as
much as possible, and only change the intended text or section content.

Always keep the original file unchanged.

## Source Of Truth

The actual Codex skill entrypoint is:

```text
SKILL.md
```

Read `SKILL.md` before doing any task. It contains the operational workflow and
the validation checklist. This README is only a fast orientation document.

## Included Tooling

```text
scripts/hwpxskill/
```

Full workflow tools for HWPX analysis, safe editing, validation, page guarding,
content guarding, namespace cleanup, and text extraction.

```text
scripts/yoon-safe/
```

Lightweight safe-edit tools for text-map extraction, text-map application,
`hp:linesegarray` removal, and compact HWPX validation.

```text
scripts/extract_page3.py
```

Reusable section-child extraction utility. It was created from a real workflow
where the visible third page was stored as top-level children `12-23` inside
`Contents/section1.xml`.

## Standard Workflow

1. Create or use the workspace `.venv`.
2. Install required Python packages into `.venv` only.
3. Validate the source HWPX.
4. Extract text and inspect section structure.
5. Modify or split only the intended content.
6. Remove `hp:linesegarray` after edits or content movement.
7. Validate the output with both validators when possible.
8. Save the output HWPX and JSON logs together.

## Minimal Commands

```powershell
$py = ".\.venv\Scripts\python.exe"
$skill = "C:\Users\User\.codex\skills\yoon-hwpx-2"
$src = "source.hwpx"

& $py "$skill\scripts\hwpxskill\validate.py" $src
& $py "$skill\scripts\yoon-safe\validate_hwpx.py" $src
& $py "$skill\scripts\hwpxskill\text_extract.py" $src --format markdown
```

Example page/section extraction:

```powershell
& $py "$skill\scripts\extract_page3.py" $src --inspect

& $py "$skill\scripts\extract_page3.py" $src `
  --mode single-section `
  --source-section "Contents/section1.xml" `
  --children "12-23" `
  --output ".\page3.hwpx" `
  --report ".\page3_report.json"

& $py "$skill\scripts\yoon-safe\validate_hwpx.py" ".\page3.hwpx" --expect-no-linesegarray
```

## Output Expectations

For every meaningful HWPX output, keep:

- the output `.hwpx`
- an analysis or extraction report JSON
- a validation JSON/log
- a text extraction file when content verification matters

If the user has a project root folder rule, create a numbered top-level result
folder and put all deliverables there.

## Important Warning

An HWPX can pass generic ZIP/XML checks and still show a warning in Hancom if
old `hp:linesegarray` nodes remain after text or layout changes.

For edited or split outputs, validate with:

```powershell
--expect-no-linesegarray
```

## Recommended Trigger Prompt

```text
Use $yoon-hwpx-2 to safely split, edit, validate, or repair this Korean HWPX document while preserving the original form.
```
