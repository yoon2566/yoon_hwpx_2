# Safe Edit Workflow

## Hancom-facing default

When the final file must open in Hancom, prefer the raw ZIP-preserving workflow:

1. Extract slots with `scripts/hwpxskill/hwpx_slots.py`.
2. Prepare `values.json`, `paragraphs.json`, or cell targets.
3. Apply edits with `scripts/hwpxskill/edit_hwpx.py`.
4. Finalize with `scripts/hwpxskill/finalize_hwpx.py --strip-linesegarray --layout`.
5. Validate with `scripts/yoon-safe/validate_hwpx.py --expect-no-linesegarray`.

This path preserves unchanged package entries, `header.xml`, `content.hpf`, `BinData`, and raw ZIP metadata better than generic ZIP rewriting.

Use `scripts/yoon-safe/apply_text_map.py` for lightweight text-node edits, drafts, or controlled cases. If Hancom has already shown a damage warning, rebuild with the raw ZIP-preserving workflow instead of continuing from that output.

## 1. 분석

```powershell
.\.venv\Scripts\python.exe .\scripts\analyze_hwpx.py .\input\template.hwpx --json .\work\analysis.json
```

## 2. 텍스트 맵 추출

```powershell
.\.venv\Scripts\python.exe .\scripts\extract_text_map.py .\input\template.hwpx --output .\work\text-map.json
```

## 3. 바꿀 텍스트 지정

`text-map.json`의 `replacements`에 바꿀 노드만 적습니다.

```json
{
  "replacements": [
    {
      "section": "Contents/section0.xml",
      "index": 0,
      "text": "새 제목"
    }
  ]
}
```

## 4. 적용

```powershell
.\.venv\Scripts\python.exe .\scripts\apply_text_map.py --source .\input\template.hwpx --map .\work\text-map.json --output .\output\result.hwpx
```

For a Hancom-facing final, prefer:

```powershell
.\.venv\Scripts\python.exe .\scripts\hwpx_slots.py .\input\template.hwpx --output .\work\slots.json
.\.venv\Scripts\python.exe .\scripts\edit_hwpx.py .\input\template.hwpx --output .\work\edited.hwpx --slot-json .\work\values.json --allow-over-budget
.\.venv\Scripts\python.exe .\scripts\finalize_hwpx.py .\work\edited.hwpx --strip-linesegarray --layout --output .\output\result.hwpx --json .\output\finalize.json
```

## 5. 검증

```powershell
.\.venv\Scripts\python.exe .\scripts\validate_hwpx.py .\output\result.hwpx --expect-no-linesegarray
```

Also extract text and compare intended sections when the user asked to preserve existing lesson content:

```powershell
.\.venv\Scripts\python.exe .\scripts\text_extract.py .\output\result.hwpx --format markdown > .\output\result_text.md
```
