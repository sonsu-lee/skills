# develop-change 오케스트레이션 설계

상태: 구현 전 계약. `develop-change/SKILL.md`가 추가되기 전까지 런타임에서는 발견되지 않는다.

## 목표

`develop-change`는 하나의 변경 요청을 이해부터 검증·전달까지 이어 주는 얇은 제어 계층이다. 구현 지식을 자체적으로 모두 보유하지 않고, 저장소 규칙과 Codex의 기본 구현 능력을 사용하면서 필요한 전문 스킬만 현재 단계에 결합한다.

다음 두 평면을 분리한다.

| 평면 | 책임 | 예시 |
| --- | --- | --- |
| 제어 평면 | route, profile, gate, 권한, 단계 전환, handoff | `design → change → verify → deliver` |
| 지식 평면 | 특정 기술·프레임워크·도구의 구현 규칙 | TypeScript, DB/ORM, React, 테스트, 보안 |

제어 평면은 이 저장소가 소유한다. 지식 평면은 프로젝트 규칙, 사용자가 만든 스킬, 설치된 공식·외부 스킬과 공식 문서를 필요할 때 선택해 사용한다.

## 해피 패스

```text
$develop-change로 목표와 종료 지점 요청
→ 저장소 지침·현재 상태 확인
→ route와 direct/bounded/architectural profile 결정
→ 현재 decision frontier의 blocker 해결
→ 적용 가능한 스킬 후보 수집
→ 경합·호환성·구체성 판정
→ 필요한 전문 스킬만 현재 단계에 결합
→ 승인된 범위에서 기본 구현 능력으로 변경
→ test/typecheck/lint/build/시각 확인
→ 요청된 경우 git-workflow로 branch/commit/push/Draft PR
→ compact handoff로 완료 상태와 다음 행동 기록
```

작고 명확한 변경은 중간 단계를 건너뛸 수 있다. 단계를 건너뛰어도 권한 확인과 검증은 생략하지 않는다.

## 구성 요소

```text
사용자 요청
└─ develop-change
   ├─ routing + profile
   ├─ gate + decision frontier
   ├─ authorization
   ├─ skill resolver
   │  ├─ 사용자가 명시한 스킬
   │  ├─ 저장소에 포함된 스킬
   │  ├─ 설치되어 있고 호환되는 스킬
   │  ├─ 공식 문서·검증 가능한 원문
   │  └─ Codex 기본 구현 능력
   ├─ verification
   └─ compact handoff
```

시각 구조는 [develop-change-workflow.drawio](./develop-change-workflow.drawio)에 유지한다.

## 스킬 선택과 경합

스킬 선택은 [skill-resolution-contract.md](../../skills/develop-change/references/skill-resolution-contract.md)를 따른다.

1. 시스템·개발자 지침과 저장소의 `AGENTS.md` 같은 프로젝트 규칙을 먼저 고정한다.
2. 사용자가 특정 스킬을 명시했으면 존재·설치·호환성을 확인하고 우선 후보로 둔다.
3. 현재 route에 실제로 필요한 스킬만 후보로 둔다.
4. 책임이 보완적이면 함께 사용한다.
5. 책임이 겹치면 더 구체적이고 현재 환경과 호환되며 근거를 추적할 수 있는 하나를 선택한다.
6. 프로젝트 규칙과 스킬이 충돌하면 프로젝트 규칙이 우선한다.
7. 결과를 바꾸는 경합을 안전하게 해소할 수 없으면 진행하지 않고 blocker로 남긴다.

스킬을 찾지 못했다는 이유로 임의 설치하지 않는다. 사용자가 설치·탐색을 요청한 경우에만 해당 워크플로를 사용하고, 그렇지 않으면 공식 문서나 기본 구현 능력으로 진행하면서 한계를 공개한다.

## 구현 지식 확장점

아래 항목은 앞으로 사용자가 만든 구현 스킬이나 검증된 공식 스킬을 결합하기 위한 자리다. 현재 실제 스킬이 없으면 `planned capability`로만 기록하며 선택된 스킬처럼 표현하지 않는다.

| capability | 담당할 내용 | 현재 처리 |
| --- | --- | --- |
| TypeScript·JavaScript | 타입 설계, 비동기 흐름, 오류 처리, 패키지 경계 | 프로젝트 규칙과 기본 구현 능력 |
| 프런트엔드·프레임워크 | 컴포넌트 구조, 상태, 접근성, 렌더링 | 프로젝트 규칙과 설치 스킬 |
| DB·ORM | 트랜잭션, migration, 인덱스, N+1, rollback | 프로젝트 규칙과 공식 문서 |
| 테스트·품질 | 테스트 계층, fixture, 회귀, 정적 검사 | 저장소 명령과 도구별 지침 |
| 보안·운영 | 신뢰 경계, 비밀정보, rollout, 관측성 | 별도 전문 검토와 명시 권한 |

## 호출과 권한

첫 활성 버전은 `$develop-change` 명시 호출만 허용한다. 일반 구현 요청, `git-workflow`의 자동 호출, 호스트 자체 개발 워크플로와 경합할 수 있으므로 실제 사용 증적이 쌓이기 전에는 implicit invocation을 켜지 않는다.

명시 호출은 오케스트레이션과 필요한 companion skill 적용에 대한 선택일 뿐 다음 권한을 만들지 않는다.

- 파일 또는 영속 문서 쓰기
- stage, commit, push, PR 생성
- 외부 시스템 쓰기
- rebase, merge, history rewrite

각 효과는 사용자의 현재 요청과 [authorization-contract.md](../../skills/develop-change/references/authorization-contract.md)에서 별도로 확인한다.

## 스택 전달 계획

변경은 아래 순서의 선형 스택으로 전달한다.

1. 오케스트레이션·스킬 해석·handoff 계약과 구조도
2. 계약 검증기와 경합 평가 케이스
3. `develop-change` 스킬 활성화와 플러그인 `0.6.0`
4. 활성 상태 통합 검증 증적

각 PR은 바로 아래 PR만 base로 두며, activation 이전 PR은 공개 스킬 카탈로그를 바꾸지 않는다.
