# Phase 1 foundation validation (historical)

이 문서는 `develop-change` 활성화 전 foundation snapshot의 재현 절차다. 활성 `SKILL.md`가 존재하는 `0.6.0` 이후 branch에서는 조기 발견 실패 조건이 의도적으로 맞지 않으므로 현재 상태 검증에 사용하지 않는다. 활성 상태는 `python3 skills/develop-change/scripts/validate_orchestration.py --activation active`로 확인한다.

이 검증은 네 가지를 확인한다.

1. routing, gate, frontier, authorization 계약의 valid/invalid 사례가 예상한 `FND-*` 규칙과 일치하는가
2. `develop-skill`의 한국어 메타데이터, scaffold, strict validation과 설치 가능한 스킬 검증이 유지되는가
3. 공통 계약을 포함한 leaf 하나가 격리된 Codex 환경에서 실제로 발견되는가
4. 검사 전후 active plugin, 설정, hook, catalog와 Codex 실행 파일이 바뀌지 않았는가

## 실행

저장소 루트에서 현재 설치 경로를 명시해 실행한다.

```bash
python3 skills/develop-change/scripts/validate_foundation.py \
  --active-plugin-root /path/to/installed/plugin \
  --active-config ~/.codex/config.toml \
  --active-hook ~/.codex/hooks.json \
  --active-telemetry ~/.codex/telemetry \
  --active-rollout ~/.codex/rollout \
  --output evals/manifests/phase1/reports/phase1-contract-foundation.json
```

존재하지 않는 telemetry·rollout 경로도 생략하지 않는다. `absent` 상태 자체를 전후 비교에 포함한다.

## 판정

| exit | status | 뜻 |
| --- | --- | --- |
| 0 | `pass` | semantic cases, 실제 격리 설치와 active-state 불변 검사가 모두 통과했다 |
| 1 | `fail` | 규칙 위반, fixture drift 또는 active-state 변화가 발견됐다 |
| 2 | `conditional` | 필요한 CLI 관측이나 sandbox fence를 완성하지 못했다 |

`conditional`은 pass가 아니다.

## 무엇을 격리하나

- 별도 `CODEX_HOME`, SQLite, XDG와 temporary root를 사용한다.
- local marketplace에 fixture plugin만 설치한다.
- installed inventory와 `debug prompt-input`의 model-visible skill catalog를 전후 비교한다.
- candidate repo를 직접·symlink·hardlink·fallback으로 읽는 경로를 거절한다.
- `develop-change/SKILL.md`가 조기에 발견되거나 active hook·telemetry·rollout 상태가 달라지면 실패한다.

세부 fixture 목록과 expected rule ID는 `foundation-cases.json`과 `leaf-only-install-cases.json`이 소유한다. 경로·description 원문은 report에 저장하지 않고 content-free digest만 남긴다.

## 이 검증이 보장하지 않는 것

- fixture receipt는 실제 authorization이 아니다.
- plugin inventory는 내부 selector state 전체가 아니다.
- pass는 hook, telemetry, rollout 또는 runtime skill 활성화 승인이 아니다.
- synthetic cases는 실제 성능이나 운영 안정성 증거가 아니다.
