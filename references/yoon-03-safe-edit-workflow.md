# Safe Edit Workflow

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

## 5. 검증

```powershell
.\.venv\Scripts\python.exe .\scripts\validate_hwpx.py .\output\result.hwpx --expect-no-linesegarray
```
