# Research Basis and Design Limits

이 문서는 Product Docs의 설계 판단을 뒷받침하는 최근 연구와 실무 표준을 기록한다. 2026-08-02에 공개 상태와 판본을 확인했다. 연구 결과를 과장하지 않으며, 특정 데이터셋이나 조직에서 나온 결과를 모든 제품에 자동 일반화하지 않는다. 학계에는 PRD 자체보다 SRS, user story, 시스템 요구사항을 평가한 연구가 많으므로 품질 원리는 차용하되 무거운 시스템 공학 산출물을 그대로 강제하지 않는다.

## 요구사항 품질과 인터뷰

- [ISO/IEC/IEEE 29148:2018](https://www.iso.org/standard/72089.html)은 요구사항 공학의 생명주기, 좋은 요구사항의 특성, 반복적 정제를 위한 기준점이다. 이 플러그인은 단일성, 명확성, 검증 가능성, 추적성을 품질 게이트로 사용한다.
- [Requirements quality research: a harmonized theory, evaluation, and roadmap (2023)](https://doi.org/10.1007/s00766-023-00405-y)은 품질을 문장 규칙 준수만이 아니라 이해·설계·구현·검증 같은 downstream activity를 얼마나 지원하는지로 평가해야 한다고 정리한다. PRD readiness를 Product·Design·Engineering·QA가 정책을 새로 발명하지 않고 일할 수 있는지로 검사한다.
- [IREB Requirements Elicitation Handbook 2.2.0 (2025)](https://cockpit-v1.ireb.org/media/pages/downloads/cpre-requirements-elicitation-handbook/c1f8973c08-1754985576/advanced_level_elicitation_handbook_en_v2.2.0.pdf)은 출처, 목적, 의존성, 기대 품질을 고려하며 새 정보에 따라 도출 계획을 갱신하도록 권한다. 이를 단계형 인터뷰와 결정 의존성에 반영했다.
- [From issue titles to requirements: an empirical study (2026)](https://link.springer.com/article/10.1007/s00766-026-00462-z)는 150개 이슈 제목에서 생성한 900개 결과를 분석해 프롬프트와 모델에 따라 명확성·검증 가능성·단일성의 trade-off가 달라짐을 보였다. 따라서 한 번의 생성 결과를 완성본으로 보지 않는다.
- [Can LLMs Generate User Stories and Assess Their Quality? (IEEE TSE 2026)](https://doi.org/10.1109/TSE.2026.3670612)는 10개 모델의 13,958개 생성 story를 비교해 높은 기준 coverage와 낮은 산출물 다양성이 공존할 수 있음을 보고했다. 첫 초안 이후 사용자·실패·정책 예외를 독립적으로 탐색하고 높은 coverage를 완전성으로 선언하지 않는다.
- [Requirements Elicitation Follow-Up Question Generation (IEEE RE 2025)](https://doi.org/10.1109/RE63999.2025.00021)은 14개 인터뷰와 146개 후속 질문 맥락에서 가이드된 LLM 질문의 가능성을 평가했다. 한 턴에 최근 맥락과 전체 ledger를 사용해 관련 있고 정보 가치가 있는 질문 하나만 묻는 설계 근거다.
- [Exploring the Use of LLMs for Requirements Specification in an IT Consulting Company (IEEE RE 2025)](https://doi.org/10.1109/RE63999.2025.00045)는 실제 산업 사례에서 입력에 없는 암묵지를 모델이 복원하지 못함을 보고했다. 역할, 예외, 수치, 외부 계약을 자연스럽게 채우지 않고 질문 또는 open item으로 둔다.
- [From Elicitation Interviews to Software Requirements (WER 2025)](https://werpapers.dimap.ufrn.br/proceedings/WER2025/wer202511.html)는 두 사례에서 LLM 생성 요구사항의 모호성과 분류 한계를 보고했다. 본 스킬은 원문과 정규화 문장을 분리하고 사람이 승인하도록 한다.
- [Automated Smell Detection and Recommendation in Natural Language Requirements (IEEE TSE 2024)](https://doi.org/10.1109/TSE.2024.3361033)는 금융 도메인 13개 시스템의 2,725개 요구사항에서 규칙 기반 smell 검출과 구조 제안을 평가했으며, 누락된 의미를 자동 재작성하지 않았다. 본 플러그인도 결정적 lint를 먼저 수행하고 의미 공백은 질문으로 남긴다.
- [Leveraging LLMs for the Quality Assurance of Software Requirements (2024)](https://arxiv.org/abs/2408.10886)는 ISO 29148 특성을 활용한 LLM 검토 가능성을 다룬다. 사람과 모델의 판정 일치가 약한 경우가 있어 LLM 검토를 finding 후보로만 사용한다.
- [Can GPT-4 Aid in Detecting Ambiguities, Inconsistencies, and Incompleteness? (2024)](https://doi.org/10.1109/ACCESS.2024.3464242)는 한 대규모 산업 명세에서 zero-shot precision이 모호성 0.39, 불일치 0.43, 불완전성 0.61이었다고 보고했다. 문장 단독 판정을 피하고 glossary, 관련 PRD, 결정 기록, interface를 함께 대조한다.
- [Aligning Language Models to Explicitly Handle Ambiguity (EMNLP 2024)](https://aclanthology.org/2024.emnlp-main.119/)는 일반 QA 데이터셋에서 ambiguity를 명시적으로 다루는 정렬을 평가한 연구다. RE 또는 한국어 요구사항의 직접 증거는 아니며, LLM이 모호성을 자동 해결한다고 가정하지 말아야 한다는 간접 보조 근거로만 사용한다.
- [Supporting High-Level to Low-Level Requirements Coverage Reviewing with LLMs (MSR 2024)](https://doi.org/10.1145/3643991.3644922)는 5개 데이터셋의 인위적 단일 누락 조건에서 높은 recall을 보였지만 완전 판정은 낙관적이었다. 누락 탐색에는 사용하되 “fully covered”를 승인 근거로 삼지 않는다.

## 도메인 지식

- [ISO 704:2022](https://www.iso.org/standard/79077.html)와 [ISO terminology guidance (2026)](https://www.iso.org/home.isoDocumentsDownload.do?t=i1qzS7QixrPMWUY_BEgYcD0JTxWTFpRsxzHXO5TUyCLDPMBBGoP7C_BOJobqPX_R)는 기존 권위 정의 검색, 개념을 구별하는 정의, 순환 회피, term과 note의 분리를 위한 규범 기반을 제공한다. 모든 보편어를 glossary로 만드는 대신 context 특수 의미만 기록한다.
- [W3C SKOS](https://www.w3.org/TR/skos-reference/)는 context와 언어별 preferred label, alternative label, broader·narrower·related 및 mapping 구분의 안정적인 기준이다. 이를 preferred term 하나, alias, context 간 mapping 규칙에 적용한다.
- [Domain-Driven Design: A Systematic Literature Review (2025)](https://doi.org/10.1016/j.jss.2025.112537)는 ubiquitous language, bounded context, domain event, 전문가 협업의 문헌 기반을 정리한다. 포함 연구의 실증 강도가 고르지 않으므로 DDD 구조를 강제하기보다 context와 협업 원칙만 사용한다.
- [Automated domain modeling from user stories (2025)](https://link.springer.com/article/10.1007/s00766-025-00442-9)은 사용자 스토리에서 얻은 도메인 모델을 사람의 보강이 필요한 초기 후보로 본다. 역할, 속성, 구현 요소, 무관한 단어를 개념으로 오인할 수 있어 명시적 분류와 승인 게이트를 둔다.
- [Concept Definition Review (2025)](https://doi.org/10.1016/j.infsof.2024.107648)은 비슷하지만 동일하지 않은 정의가 공존하는 문제를 다룬다. 용어를 자동 병합하지 않고 목적, 범위, 출처, 예시와 반례를 함께 보존한다.
- [Digital requirements engineering with authoritative source connectivity (2024)](https://arxiv.org/abs/2401.16330)은 권위 있는 출처와 연결된 구조적 요구사항 및 용어 일관성의 필요성을 제시한다. 본 플러그인은 가벼운 Markdown을 유지하면서 안정 ID와 출처 링크를 둔다.
- [Docs-as-Code in Practice (EMSE 2023)](https://doi.org/10.1007/s10664-023-10350-7)와 [outdated code reference 연구 (EMSE 2023)](https://doi.org/10.1007/s10664-023-10397-6)는 Git·Markdown·자동 링크 검사와 stale reference 문제가 함께 존재함을 보여 준다. 경로·symbol drift를 자동으로 정본 의미 변경으로 해석하지 않고 `needs-review`로 올린다.
- [CodeWiki (ACL Findings 2026)](https://doi.org/10.18653/v1/2026.findings-acl.288)는 dependency graph, 계층적 합성, cross-reference를 사용한 코드 위키 생성을 평가한다. LLM 평가와 작은 human pilot라는 한계가 있어 generated wiki를 canonical domain truth가 아니라 secondary evidence로만 사용한다.

## 결정 기록

- [Architecture Decision Records in Practice (ECSA 2024)](https://research.chalmers.se/en/publication/542849)는 한 조직의 3개월 action research와 7개 인터뷰에서 ADR이 지식 전달과 협업에 도움을 주며 저장 위치가 중요하다고 보고했다. 단일 사례의 결과이므로 효과를 보장하지 않고, 저장소 가까이에 작고 연결된 기록을 둔다는 설계 근거로만 사용한다.
- [Using LLMs in Generating Design Rationale (2025)](https://arxiv.org/abs/2504.20781)은 100개 설계 문제에서 여러 모델과 프롬프트를 평가했고, 생성 근거의 정밀도가 낮고 일부는 오도 가능함을 보고했다. 모델이 선택지나 근거를 만들어 과거 사실처럼 기록하는 것을 금지한다.
- [Architectural Design Decisions That Incur Technical Debt (2021)](https://doi.org/10.1016/j.infsof.2021.106669)는 의도적으로 수용한 부채와 context 변화로 부채가 된 결정을 구분한다. deliberate debt와 assumption 기반 revisit trigger에 반영했다.
- [Traceability of Architectural Design Decisions and Software Artifacts (2023)](https://doi.org/10.2478/fcds-2023-0018)는 요구사항, 코드, 기술 문서와 결정 사이 trace link 연구를 검토한다. ADR이 rationale를 복제하지 않고 관련 artifact를 연결하는 근거다.
- [Using Architecture Decision Records in Open Source Projects (2023)](https://doi.org/10.1109/ACCESS.2023.3287654)는 921개 GitHub repository의 ADR 사용 양상을 분석했다. repository-local persistence와 template 사용의 실증 관찰로 참고하되 인과 효과로 해석하지 않는다.
- [One Size Fits All? An Empirical Comparison of ADR Templates (2026)](https://arxiv.org/abs/2604.27333)는 33명과 두 시나리오에서 간결한 Nygard 계열과 구조화된 MADR 계열을 비교했다. 작은 학생 표본이라는 한계가 있어 우열을 일반화하지 않고, 관련 없는 섹션을 제거하는 점진적 template의 보조 근거로 사용한다.
- [Architecture Decision Records: Adoption, Impact, and Developer Engagement (ICSA 2026)](https://conf.researchr.org/details/icsa-2026/icsa-2026-papers/34/Architecture-Decision-Records-Adoption-Impact-and-Developer-Engagement-in-Open-Sou)는 대규모 오픈소스 표본에서 ADR 개수와 여러 품질 지표의 상관이 대체로 작음을 보고한다. 기록 수를 성공 지표로 보지 않고 중요한 결정의 provenance와 retrieval을 평가한다.
- [MADR 4.0](https://adr.github.io/madr/)과 [Nygard의 ADR 제안](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)은 한 기록에 한 결정, 맥락·선택·결과, 작은 Markdown 기록, 대체 관계라는 실무 관례를 제공한다. 템플릿과 `write-adr`은 이 범위에 맞춰 아키텍처·기술 결정만 다룬다.

## 질문 설계와 앵커링

- [Pew Research Center의 설문 문항 지침](https://www.pewresearch.org/writing-survey-questions/)은 한 문항에 여러 개념을 묻는 double-barreled 질문과 순서 효과를 경고한다. 이를 “한 턴에 한 결정 단위” 규칙으로 적용한다.
- [GOV.UK Form structure](https://www.gov.uk/service-manual/design/form-structure)는 한 번에 한 가지 질문이 집중과 조건 분기에 유리하다고 설명한다. 반면 순차 질문은 시간이 길어지고 전체 맥락을 잃을 수 있어, phase 요약과 되돌리기를 함께 제공한다.
- [McKenzie et al. (2006)](https://rady.ucsd.edu/_files/faculty-research/mckenzie/McKenzieetal2006PsychSci.pdf)은 기본값이 추천 신호로 해석되어 선택에 영향을 줄 수 있음을 보였다. 도메인 사실에는 추천을 하지 않고, 제품 trade-off의 추천도 자동 선택하지 않으며 명시적 수락을 요구한다.

## 문서 형식과 파생 위키

- [OpenAI의 Agent Skills 가이드](https://learn.chatgpt.com/docs/build-skills)는 trigger description, 한 가지 명확한 사용자 목표, 단계·출력·비추론 경계, 점진적 supporting files를 권장한다. 세 책임을 한 거대 스킬에 합치지 않고 plugin 안의 focused skill로 분리한 근거다.
- [Open Knowledge Format v0.2](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)는 Markdown, YAML metadata, provenance, 검증과 staleness를 위한 가벼운 상호 운용 형식을 제시한다. 공통 계약은 전체 OKF 구현을 주장하지 않고 `type`, sources, standard links 같은 안전한 공통 부분만 사용한다.
- [OpenWiki](https://github.com/langchain-ai/openwiki)는 저장소로부터 `openwiki/` 탐색 문서를 생성하고 사용자 지침과 `.openwikiignore` 입력 경계를 제공한다. 2026-08-02 현재 README는 OKF v0.1 출력을 설명하지만 최신 Google spec은 v0.2이며, Product Docs의 `visibility`·`publication`을 집행한다고 문서화하지 않는다. 따라서 원본 제품 문서는 `docs/`의 정본으로 유지하고, 위키는 명시적으로 필터링한 입력에서 만드는 버전 차이가 있는 파생 뷰로 취급한다.

## Agent Skill 평가

- [SkillsBench (2026)](https://arxiv.org/abs/2602.12670)는 no-skill과 with-skill의 쌍대 실행과 deterministic verifier를 사용하며 focused skill의 구성이 중요함을 보인다. 세 스킬을 별도 평가하고 baseline 대비 회귀를 확인하는 프로토콜에 반영했다.
- [Skill Coverage (2026)](https://arxiv.org/abs/2606.20659)는 최종 성공률만으로 skill의 어느 규칙이 실제 발동했는지 알기 어렵다는 문제를 다룬다. 각 평가 케이스가 구체적인 `must`와 `must_not` assertion을 갖게 했다.
- [τ-bench (2024)](https://arxiv.org/abs/2406.12045)는 다중 턴 정책 준수와 최종 환경 상태, 반복 신뢰성을 평가한다. 승인 상태 변화와 문서 이력은 다중 턴으로, 고위험 holdout은 반복 통과로 본다.
- [AgentDojo (2024)](https://arxiv.org/abs/2406.13352)는 정상 작업 성공과 간접 prompt injection 방어를 함께 측정한다. 공격을 단순 거절하는 데서 끝내지 않고 안전한 문서 작업을 계속해야 security case를 통과한다.
- [OpenAI Evaluation Best Practices](https://developers.openai.com/api/docs/guides/evaluation-best-practices)는 task-specific typical·edge·adversarial data, 명확한 pass/fail, 자동 검증과 사람이 보정한 judge를 권한다. 각 스킬의 한국어·영어·혼합 언어 9개 케이스와 hard gate에 반영했다.

## 적용 한계

- 품질 규칙은 완전성이나 제품 성공을 증명하지 않는다.
- LLM의 lint 결과는 오류 확정이 아니라 검토 후보이다. 반대로 발견하지 못했다고 요구사항이 명확하거나 완전한 것도 아니다.
- 숫자 목표, 시장 사실, 법률·규제 해석, 사용자의 의도, 과거 결정 근거를 모델이 채우지 않는다.
- 고위험 도메인은 해당 분야 책임자와 권위 있는 최신 출처의 확인이 필요하다.
- 최근 요구사항 품질 실험의 다수는 영어 자료를 사용했다. 한국어의 생략 주어, 지시어, `및/또는`, 복합 의무 lint는 semantic-slot 기반 운영 가설이며 한국어 원어민 판정으로 보정해야 한다.
- 평가 케이스는 회귀 방지용 계약이지 실제 조직과 도메인에서의 사용자 검증을 대체하지 않는다.
- 2026년 논문 중 peer review 전 preprint와 공개 직후 논문은 보조 근거로만 사용하며 후속 버전에서 결과와 링크를 다시 확인한다.
