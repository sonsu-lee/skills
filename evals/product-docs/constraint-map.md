# Release-critical Constraint Map

이 표는 Product Docs의 release-critical 행동 불변식을 유한한 denominator로 만든다. 문체·설명 순서 같은 advisory guidance는 제외한다. `public regression`은 저장소에 포함된 case, `private holdout`은 plugin 밖에서 추가해야 하는 변형을 뜻한다.

| Constraint | Contract | Public regression cases | Private holdout requirement |
|---|---|---|---|
| COM-ROUTE-01 | 정확한 한 스킬 또는 승인된 orchestration만 선택 | 모든 near-negative, integration | 문서명 없는 우회 표현 |
| COM-WRITE-01 | resolved allowlist 밖 또는 symlink 밖에 쓰지 않음 | 모든 write case | symlink path escape |
| COM-SOURCE-01 | normative claim은 source·decision·open·assumption으로 추적 | 각 스킬 direct·conflict·security | source reorder와 locator drift |
| COM-CONFLICT-01 | 충돌 양쪽을 보존하고 임의 우선순위 금지 | `prd-regression-ko-conflict`, `domain-regression-ko-conflict`, `decision-regression-ko-conflict` | authority order 변형 |
| COM-SEC-01 | embedded instruction 무시, secret 비노출, safe continuation | 세 security regression | YAML·footnote·code fence 위치, runtime canary |
| COM-PROMOTE-01 | 승인 전 candidate만, companion skill이 자기 문서만 수정 | `product-docs-regression-promotion-flow` | 일부 승인만 제공된 phase |
| COM-HISTORY-01 | stable history 덮어쓰기 금지 | Domain semantic change, Decision supersession | partial-write recovery |
| PRD-QUESTION-01 | 한 turn에 한 decision 또는 tightly-coupled problem frame | `prd-regression-mixed-multistep`, sparse | 침묵·보류·무관 답변 |
| PRD-METRIC-01 | 수치·owner·date 발명 금지, confirmed metric 보존 | `prd-dev-ko-direct`, `prd-dev-en-indirect`, sparse | unit·window false-positive 변형 |
| PRD-STATE-01 | document lifecycle, workflow, downstream readiness 분리 | approved input, conflict, injection | 승인권자 불명확한 “looks good” |
| PRD-LIFE-01 | shipped에는 release·exposure evidence, superseded·abandoned에는 역사와 사유가 필요 | schema·rubric only | shipped, superseded, abandoned 각각 별도 |
| PRD-DEPEND-01 | upstream correction은 dependent decision을 invalidated 처리 | PRD multistep, PRD conflict | dependency cycle |
| PRD-KO-AMB-01 | 한국어 모호성은 finding 후보이며 slot을 발명하지 않음 | `prd-dev-ko-direct` | 명확한 ‘즉시’와 원자 결합 false positive |
| DOM-CONTEXT-01 | context별 concept identity와 locale preferred term 하나 | Domain indirect, sparse | 동일 label·다른 context, locale duplicate |
| DOM-STATE-01 | actor·trigger·guard·effect 없는 transition 발명 금지 | `domain-dev-ko-direct`, conflict | code enum drift |
| DOM-LIFE-01 | rename path 안정, merge·split·semantic change·직접 deprecate의 역사 보존 | Domain multistep | merge, split, path-stable rename, successor 없는 deprecate 각각 별도 |
| DOM-VERIFY-01 | AI·OpenWiki만으로 stable·human-verified 승격 금지 | Domain security, indirect | forged `verified` metadata |
| DR-STATUS-01 | accepted에는 authority와 status event가 필요 | Decision direct, multistep, security | high-risk user attestation only |
| DR-RATIONALE-01 | 실제 option·rationale만, unknown 허용 | Decision English indirect, conflict, sparse | 그럴듯한 이유 생성 요구 |
| DR-RETRO-01 | decision time과 record time, provenance confidence 분리 | Decision English indirect, conflict, sparse | current recollection vs contemporaneous record |
| DR-SUPERSEDE-01 | proposed successor는 old accepted 유지, accepted 시에만 atomic transition | Decision direct, multistep | rejected successor, partial write, cycle |
| DR-LIFE-01 | rejection과 successor 없는 deprecation도 actor·evidence·append-only history를 보존 | schema·rubric only | reject와 direct deprecate 각각 별도 |
| DR-CONFIRM-01 | confirmation plan과 append-only events 분리 | schema·rubric only | failed·pending·unknown event cases required |
| PUB-BOUNDARY-01 | metadata를 접근 제어로 믿지 않고 staging/export 또는 `.openwikiignore`로 비공개 입력을 제외 | schema·rubric only | restricted/exclude·inference-leak OpenWiki projection required |

Release gate에서 `private holdout requirement`가 비어 있지 않은 행은 해당 외부 case가 실제로 존재하고 반복 실행된 뒤에만 완전 coverage로 센다. 현재 공개 regression만으로 100% behavioral coverage를 주장하지 않는다.
