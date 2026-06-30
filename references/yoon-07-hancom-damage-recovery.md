# Hancom Damage Recovery

Use this when an HWPX passes ZIP/XML validation but Hancom reports that the document is damaged, modified, or unsafe.

## Why This Happens

Hancom checks more than generic ZIP and XML validity. A file can pass these checks:

- first ZIP entry is `mimetype`
- required entries exist
- XML is well-formed
- `hp:linesegarray` count is `0`

and still trigger a Hancom warning when the package was repacked in a way Hancom dislikes.

Common causes:

- generic `ZipFile` rewriting changed local or central ZIP header details
- a preview cache such as `Preview/PrvText.txt` was rewritten unnecessarily
- a single-section split removed section/package structure that Hancom expected
- an edited output was edited again instead of rebuilding from the original
- stale `hp:linesegarray` remained after text length or layout changed

## Recovery Rule

Do not keep patching the warning file. Rebuild from the closest clean source.

Preferred source order:

1. original user-provided HWPX
2. preserve-sections extraction output
3. single-section extraction output only when the preserve-sections file is unavailable

## Safe Recovery Workflow

```powershell
$py = ".\.venv\Scripts\python.exe"
$skill = "C:\Users\User\.codex\skills\yoon-hwpx-2"
$src = "source-or-preserve-sections.hwpx"
$out = "result.hwpx"

& $py "$skill\scripts\hwpxskill\hwpx_slots.py" $src --output ".\slots.json"
# Prepare values.json, paragraphs.json, or cells from the slots.
& $py "$skill\scripts\hwpxskill\edit_hwpx.py" $src `
  --output ".\edited.hwpx" `
  --paragraph-json ".\paragraphs.json" `
  --allow-over-budget

& $py "$skill\scripts\hwpxskill\finalize_hwpx.py" ".\edited.hwpx" `
  --strip-linesegarray `
  --layout `
  --output $out `
  --json ".\finalize.json"

& $py "$skill\scripts\yoon-safe\validate_hwpx.py" $out --expect-no-linesegarray |
  Out-File ".\validate.json" -Encoding UTF8

& $py "$skill\scripts\hwpxskill\text_extract.py" $out --format markdown |
  Out-File ".\text.md" -Encoding UTF8
```

## Preview Cache Policy

Leave these files untouched unless the user explicitly asks for refreshed previews:

- `Preview/PrvText.txt`
- `Preview/PrvImage.png`

Stale preview text is usually less risky than rewriting preview entries with a generic ZIP writer. If preview refresh is required, use a raw ZIP-preserving writer and validate again.

## Section Split Policy

When splitting a page or section:

- Create a `single-section` output for compact use.
- Also create a `preserve-sections` fallback when Hancom compatibility matters.
- If Hancom warns on the single-section output, use the preserve-sections file as the edit base.

## Validation Notes

Always save these next to the final HWPX:

- structural validation JSON
- extracted text markdown
- content required/forbidden check JSON when relevant
- source-vs-output comparison when the user asked to preserve existing content

State clearly when validation is structural only and Hancom GUI opening was not performed.
