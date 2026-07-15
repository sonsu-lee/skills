# Portable skill 작성 근거

마지막 확인: 2026-07-13

이 문서는 작성 규칙을 반복하지 않고, 규칙을 갱신하거나 tradeoff를 판단할 때 확인할 근거만 기록한다.

## 공식 계약

- Agent Skills specification을 portable 형식 계약으로 사용한다.
- OpenAI와 Anthropic 기술 문서에서 같은 원칙을 확인하고 제품 확장은 공통 계약에서 제외한다.
- `name`, `description`, progressive disclosure와 직접 reference 규칙은 공식 계약에 근거한다.

## 연구가 추가하는 판단

- SkillsBench는 작고 응집된 skill이 도움이 될 수 있지만 일부 과제에서는 성능을 낮춘다고 보고한다.
- SWE-Skills-Bench는 공개 SWE skill 다수가 의미 있는 이득 없이 token 비용이나 오류를 늘릴 수 있다고 보고한다.
- ecosystem 분석은 intent 중복이 흔하므로 새 skill 전에 기존 책임을 확인해야 한다는 근거를 제공한다.
- semantic supply-chain 연구는 description과 외부 skill 파일을 routing·보안 표면으로 검토해야 한다는 근거를 제공한다.
- 위 연구는 최신 preprint와 특정 model·harness 결과를 포함하므로 보편적 보장으로 사용하지 않는다.

## 주요 출처

- [Agent Skills specification](https://agentskills.io/specification)
- [Agent Skills best practices](https://agentskills.io/skill-creation/best-practices)
- [Agent Skills description optimization](https://agentskills.io/skill-creation/optimizing-descriptions)
- [Agent Skills evaluation](https://agentskills.io/skill-creation/evaluating-skills)
- [OpenAI Build skills](https://developers.openai.com/codex/skills)
- [Anthropic Agent Skills best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- [SkillsBench v4](https://arxiv.org/abs/2602.12670)
- [SWE-Skills-Bench](https://arxiv.org/abs/2603.15401)
- [Agent Skills ecosystem analysis](https://arxiv.org/abs/2602.08004)
- [SKILL.md semantic supply-chain attacks](https://arxiv.org/abs/2605.11418)
