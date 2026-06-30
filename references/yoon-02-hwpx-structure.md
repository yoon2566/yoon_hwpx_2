# HWPX Structure

HWPX는 ZIP 패키지입니다. 안전 편집에서 주로 보는 파일은 다음입니다.

- `mimetype`: ZIP 첫 항목이어야 한다.
- `Contents/header.xml`: 스타일, 글꼴, 문단 속성 등
- `Contents/section0.xml`: 본문 내용
- `Contents/content.hpf`: 패키지 manifest

본문 텍스트는 보통 `Contents/section*.xml` 안의 `hp:t` 요소에 들어 있습니다.

이 키트는 표, 이미지, 스타일 구조를 새로 만들기보다 원본 패키지를 복사하고 `hp:t` 텍스트만 바꾸는 방식을 우선합니다.
