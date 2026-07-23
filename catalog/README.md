# External Skills Catalog

외부 스킬의 출처, 분류와 설치 방법을 정리하는 카탈로그입니다.

제3자 소스 코드는 이 저장소에 복사하거나 미러링하지 않습니다. 설치와 업데이트는 upstream 저장소, `npx skills` 또는 호스트의 공식 플러그인을 사용합니다.

## 등록 원칙

외부 스킬은 사용자가 하나씩 선택한 뒤 추가합니다. 각 항목에는 다음 정보를 기록합니다.

- 사용 목적
- upstream 저장소
- 원본 스킬 경로
- upstream 라이선스 링크
- 종류: skill, plugin, command 또는 tool
- 배포 방식: shared, host-specific 또는 host-native
- 호스트별 provider와 공식 설치 명령
- 실제로 필요한 연계 항목
- 소속 profile과 add-on
- 마지막 확인 날짜
- 설치 부작용 또는 신뢰 관련 주의사항

공용 스킬만 `.agents/skills`를 SSOT로 사용합니다. 호스트 전용 기능은 해당 호스트의 전용 위치, 내장 스킬 또는 공식 플러그인으로 설치합니다.

## 등록된 스킬

기계 판독 데이터는 다음 파일에 있습니다.

- [`skills.json`](skills.json): 외부 스킬의 source, delivery, dependency와 provider
- [`profiles.json`](profiles.json): `react` profile, 선택 add-on과 전역 capability
- [`adaptations.json`](adaptations.json): owned skill이 참고한 upstream provenance. 설치기는 이 파일을 읽지 않습니다.

현재 공개 묶음은 다음과 같습니다.

- profile: `react`
- add-on: `view-transitions`, `design-review`, `docs-writing`
- global capability: `discovery`, `skill-authoring`

각 항목의 선정 근거와 제한은 [`초기 외부 스킬 구성 결정`](../research/reports/2026-07-12-initial-skill-selection.md)을 참고하세요.

## 설치 구성

`react` profile은 다음 두 스킬을 기본으로 선택합니다.

- `vercel-composition-patterns`
- `vercel-react-best-practices`

선택 기능은 `--with`로 추가합니다.

| 이름 | 포함 항목 |
| --- | --- |
| `view-transitions` | `vercel-react-view-transitions` |
| `design-review` | `web-design-guidelines` |
| `docs-writing` | `writing-guidelines` |
| `discovery` | `find-skills` |
| `skill-authoring` | host별 `skill-creator` provider |

dependency는 profile이나 `--with`의 편의상 묶음과 별도로 처리합니다.

## Owned adaptation provenance

`adaptations.json`은 owned skill이 참고한 upstream revision과 개념을 기록하는 개발 provenance이며 설치 입력이 아니다. owned adaptation으로 대체된 upstream provider는 active profile과 add-on에서 제거해 같은 실행 환경에 동등한 trigger가 중복되지 않게 한다.

대체된 upstream provider는 immutable provenance로 계속 추적하지만 profile이나 add-on으로 설치하지 않습니다. `domain-modeling`과 `grill-with-docs`는 이번 변경에서 owned replacement 없이 active 설치 대상에서 제외했습니다. owned domain-modeling workflow가 필요하면 별도의 승인된 계획과 eval set으로 다룹니다.

설치 명령과 commit 고정 원격 실행 절차는 [저장소 README](../README.md)를 참고하세요.
