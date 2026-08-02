# Product Docs

제품 지식을 한 문서에 섞지 않고, 서로 연결된 세 종류의 정본 문서로 관리하는 Codex 플러그인이다.

- `create-prd`: 문제, 제품 결과, 범위, 동작, 규칙, 성공 기준을 합의해 PRD로 만든다.
- `maintain-domain-docs`: 용어, 개념, 역할, 상태, 전이, 비즈니스 규칙을 근거와 함께 유지한다.
- `record-decision`: 중요한 제품·정책·아키텍처 결정을 선택지, 근거, 결과, 재검토 조건과 함께 남긴다.

세 스킬은 `references/document-contract.md`의 저장 및 상호 연결 규칙을 공유한다. PRD가 다른 두 문서의 내용을 소유하지는 않는다. 도메인 지식이나 장기 보존할 결정이 발견되면 승격 후보를 제시하고, 사용자가 승인한 뒤 해당 스킬로 정본을 만든다.

## 사용 예

```text
$product-docs:create-prd로 이 아이디어를 full 깊이로 인터뷰하고 PRD를 작성해줘.
$product-docs:maintain-domain-docs로 반복되는 정산 용어와 상태 전이를 정본으로 정리해줘.
$product-docs:record-decision으로 수동 검토를 선택한 실제 근거와 재검토 조건을 남겨줘.
```

한 작업에서 세 문서를 모두 요청해도 PRD → 승인된 promotion candidate → companion skill 순서로 처리한다. 쓰기 요청, 의미 승인, 문서 소유권은 각각 별도로 확인한다.

## 기본 저장 구조

저장소에 기존 규칙이 있으면 그것을 우선한다. 규칙이 없을 때만 다음 경로를 사용한다.

```text
docs/
├── product/prds/
├── domain/
└── decisions/
```

OpenWiki 같은 파생 위키는 이후 이 정본들을 읽어 탐색 문서를 만들 수 있다. 생성된 위키를 정본으로 간주하거나 `openwiki/` 아래에 제품 결정을 직접 기록하지 않는다. `visibility`와 `publication`은 정책 힌트일 뿐 OpenWiki 접근 제어가 아니다. 연결할 때는 `.openwikiignore` 또는 별도 staging/export projection으로 비공개 입력을 먼저 제외하고 결과를 검증해야 한다.

## 검증

플러그인과 각 스킬은 구조 검증 자산과 27개의 공개 회귀 케이스, 1개의 교차 스킬 통합 케이스를 포함한다. 이 케이스는 개발 계약이며 비공개 holdout이 아니다. 실제 모델 비교는 `evals/protocol.md`에 따라 `evals/`를 제외한 runtime snapshot에서 실행하고, release holdout과 runtime canary는 플러그인 밖에서 관리해야 한다.

이 저장소에는 plugin·skill schema validator가 읽을 구조와 JSONL 평가 계약이 포함돼 있다. 링크, cross-document ID, 평가 분포까지 한 명령으로 검사하는 전용 static runner와 모델 호출·파일 tree/hash oracle·반복 신뢰성 runner는 포함하지 않는다. 외부 검증기가 확인해야 할 범위는 `evals/protocol.md`와 각 rubric에 명시했다. 연구 근거와 적용 한계는 `references/research-basis.md`에 정리되어 있다.
