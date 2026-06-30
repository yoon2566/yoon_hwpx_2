# Troubleshooting

## 검증은 통과했는데 한글에서 경고가 뜬다

`hp:linesegarray`가 남아 있는지 먼저 확인하세요.

```powershell
.\.venv\Scripts\python.exe .\scripts\validate_hwpx.py .\output\result.hwpx --expect-no-linesegarray
```

## 텍스트 노드 인덱스를 모르겠다

먼저 텍스트 맵을 추출하세요.

```powershell
.\.venv\Scripts\python.exe .\scripts\extract_text_map.py .\input\template.hwpx --output .\work\text-map.json
```

## 한글 출력이 깨진다

PowerShell에서 UTF-8 환경 변수를 설정하세요.

```powershell
$env:PYTHONUTF8='1'
$env:PYTHONIOENCODING='utf-8'
```
