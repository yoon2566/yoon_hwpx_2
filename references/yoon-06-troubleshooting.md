# Troubleshooting

## 검증은 통과했는데 한글에서 경고가 뜬다

`hp:linesegarray`가 남아 있는지 먼저 확인하세요.

```powershell
.\.venv\Scripts\python.exe .\scripts\validate_hwpx.py .\output\result.hwpx --expect-no-linesegarray
```

`hp:linesegarray`가 0인데도 한글이 "손상" 또는 "변조" 경고를 표시하면, 일반 ZIP 재작성이나 미리보기 캐시 수정 때문에 Hancom이 내부 패키지 차이를 민감하게 본 것일 수 있습니다.

이 경우:

1. 경고가 난 결과물을 계속 편집하지 마세요.
2. 원본 또는 `preserve-sections` 대체본에서 다시 시작하세요.
3. `scripts/hwpxskill/edit_hwpx.py`의 `--slot-json` 또는 `--paragraph-json`을 사용하세요.
4. `scripts/hwpxskill/finalize_hwpx.py --strip-linesegarray --layout`으로 마무리하세요.
5. `Preview/PrvText.txt`와 `Preview/PrvImage.png`는 건드리지 마세요.
6. `validate_hwpx.py --expect-no-linesegarray`, `text_extract.py`, 필요한 content 비교 로그를 남기세요.

자세한 절차는 `references/yoon-07-hancom-damage-recovery.md`를 읽으세요.

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
