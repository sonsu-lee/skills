# Orchestration validation

이 검증은 활성화 전후에 같은 계약을 사용해 다음을 확인한다.

- 사용자가 명시한 스킬, 저장소 스킬과 설치 스킬의 우선순위
- 보완 관계의 조합과 동일 책임의 경합 처리
- 프로젝트 규칙 충돌, 비호환 후보와 planned capability의 제외
- 명시 호출과 side effect authorization의 분리
- pass·conditional·blocked gate와 blocker 조합
- direct profile의 confirmed 제한과 스킬 결정 aggregate·호환성 제약
- compact handoff의 완료·검증·비밀정보 경계
- `develop-change`의 inactive/active discovery 상태

저장소 루트에서 실행한다.

```bash
# 활성화 전 계약 PR
python3 skills/develop-change/scripts/validate_orchestration.py --activation inactive

# SKILL.md와 agents/openai.yaml 활성화 이후
python3 skills/develop-change/scripts/validate_orchestration.py --activation active

# 현재 상태를 자동 감지하고 재현 가능한 report 생성
python3 skills/develop-change/scripts/validate_orchestration.py \
  --activation auto \
  --output evals/manifests/phase2/reports/develop-change-orchestration.json

# 저장된 report가 현재 입력에서 다시 생성되는 값과 같은지 확인
python3 skills/develop-change/scripts/validate_orchestration.py \
  --activation active \
  --check-output evals/manifests/phase2/reports/develop-change-orchestration.json
```

`pass`는 정적 계약과 저장소 discovery 경계가 일치한다는 뜻이다. 실제 사용자 작업 성공률, implicit invocation 안정성, 외부 스킬의 신뢰성이나 운영 rollout을 보장하지 않는다.
