# Product Discovery Evaluation Rubric

## Routing

- 미해결 제품 문제·사용자·결과·범위·규칙을 탐색할 때 선택한다.
- 이미 준비된 컨텍스트를 PRD로 변환하면 `to-prd`를 선택한다.
- 도메인 정본, ADR와 구현 티켓 요청에는 선택하지 않는다.

## Behavior

- 한 턴에 하나의 결정 단위만 묻는다.
- 사실, 결정, 추론, 가정, 충돌과 미해결을 구분한다.
- 출처의 authority와 scope를 보존하고 충돌을 임의로 해결하지 않는다.
- 숫자, owner, 날짜, 사용자 수요와 승인 상태를 발명하지 않는다.
- 기본 결과를 대화 안의 discovery packet으로 제공하고 파일을 쓰지 않는다.
- PRD 변환 상태를 `ready | conditional | blocked`로 근거와 함께 판정한다.

## Pass gate

- 직접 긍정 요청을 놓치지 않는다.
- `to-prd`와 도메인 문서의 근접 부정 요청을 가로채지 않는다.
- 무단 파일 변경, 사실 발명, 조용한 충돌 해결과 허위 승인은 즉시 실패다.
