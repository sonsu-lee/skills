# Ticket quality bar

티켓 초안을 완성하거나 이슈 트래커에 게시하기 전에 읽는다.

## 티켓 단위

- 하나의 결과로 설명할 수 있다.
- 독립적으로 검토하거나 완료 상태를 판정할 수 있다.
- source artifact의 요구사항이나 결정에 연결된다.
- 인접 티켓과 scope가 중복되지 않는다.
- 구현 수단만 나열하지 않고 왜 필요한지 설명한다.

## 필수 항목

```text
Title: <observable result>
Context: <why, source locators>
Scope: <included behavior>
Non-goals: <explicit exclusions>
Acceptance criteria: <observable checks>
Verification: <test, review, analysis or operation>
Blocked by: <ticket IDs or none>
Blocks: <ticket IDs or none>
Open questions: <IDs or none>
```

## 분해 검사

- 첫 티켓이 end-to-end 불확실성을 줄이는 얇은 경로인가?
- 조사·결정 티켓의 결과가 후속 구현과 blocking edge로 연결되는가?
- API, schema, migration, UI, 관찰 가능성이 레이어별 고립 작업으로만 나뉘지 않았는가?
- 실패, 복구, migration과 rollout이 관련 있을 때 빠지지 않았는가?
- 하나의 티켓 제목에 독립 목적을 `and`로 숨기지 않았는가?

## 게시 안전성

- tracker와 project의 visibility, 접근 주체와 허용된 공개 범위가 확인됐는가?
- 제목, 본문, 첨부, source locator와 tool argument를 포함한 exact payload를 검사했는가?
- secret, token, runtime canary와 불필요한 개인정보를 제거했는가?
- restricted 원문과 비공개 취약점 세부 정보가 공개 범위를 벗어나면 안전한 맥락·locator와 redaction marker로 대체했는가?
- redaction이나 metadata 변경 뒤의 최종 payload를 다시 보여 주고 새 승인을 받았는가?

## 금지

- 입력에 없는 담당자, 일정, 공수와 우선순위 확정
- acceptance criteria에서 새로운 제품 정책 생성
- 존재하지 않는 source·결정·선행 티켓 참조
- 구현 티켓 안에 unresolved architecture choice 숨기기
- 확인되지 않은 visibility나 공개 범위로 민감한 payload 전송
- 사용자 승인 전 원격 게시
