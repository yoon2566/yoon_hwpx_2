# linesegarray Warning

`hp:linesegarray`는 HWPX section XML에 들어 있는 줄 배치 관련 레이아웃 캐시입니다.

본문 텍스트를 바꿨는데 기존 `hp:linesegarray`가 남아 있으면, 한글 프로그램이 문서를 손상 또는 변조 가능 문서로 판단할 수 있습니다. ZIP 구조와 XML 문법이 정상이어도 이 문제가 생길 수 있습니다.

따라서 이 키트는 텍스트 노드를 바꾼 뒤 기본값으로 `hp:linesegarray`를 제거합니다. 이후 한글 프로그램은 문서를 열 때 줄 배치를 다시 계산할 수 있습니다.

중요한 점:

- `linesegarray` 제거는 표 구조 삭제가 아니다.
- 본문 텍스트와 표 셀 구조는 유지한다.
- 제거 후에도 XML well-formed 검증을 실행해야 한다.
