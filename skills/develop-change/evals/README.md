# Contract foundation fixtures

`foundation-cases.json`은 `phase1-foundation-draft-v1`의 route/profile, gate, decision frontier와 per-task authorization 조합을 검증한다. `base_fixture`에 JSON Pointer mutation을 적용하며 invalid case는 stable `FND-*` rule ID를 최소 하나 이상 기대한다.

`leaf-only-install-cases.json`은 disposable `CODEX_HOME`·`CODEX_SQLITE_HOME`·XDG root와 local marketplace에 `research` leaf 및 공통 계약 reference만 복사한다. Catalog에 고정된 design baseline ID, `foundation-contract.schema.json` digest와 세 Markdown digest를 source와 CLI가 실제 설치한 cache 양쪽에서 검증한다. 정상 case는 격리된 `codex plugin marketplace add`·`plugin add`·`plugin list --json`을 실행해 installed inventory에서 exact plugin을 관측하고, `codex debug prompt-input`의 model-visible `<skills_instructions>` projection에서 exact fixture `research` identity/source locator가 존재하며 `develop-change`와 active-source fallback은 없음을 확인한다. Active catalog는 prompt에 선언된 locator와 terminal resolved locator를 모두 content-free digest에 결박한다. 각 `SKILL.md` source와 sibling `agents/openai.yaml` target, source root 아래에서 directory symlink를 따라 도달 가능한 모든 descendant symlink target과 regular-file inode를 candidate repo의 동일한 reachable graph/inode closure와 비교한다. Candidate direct·file symlink·hardlink·fallback-directory·metadata-symlink locator, nested reference/script symlink와 asset hardlink, 외부 directory-symlink 아래 nested symlink·hardlink, candidate를 중간 hop으로 지나는 source/metadata/descendant chain, candidate-side linked subtree hardlink, symlink cycle 및 symlink 해석 뒤 `..`가 candidate로 되돌아가는 chain fixture를 모두 구조화된 `FND-PROJECTION-001`로 거절한다. Symlink·hardlink·fallback, 계약/schema drift, 조기 `develop-change/SKILL.md` 발견과 active runtime projection drift는 거절한다.

`plugin list --json`이 제공하는 것은 trusted **installed-plugin inventory**이지 Codex selector의 전체 effective skill catalog가 아니다. 이 inventory의 한계는 `coverage: installed_plugins_only`, `selector_catalog_coverage: not_observed`로 보존한다. 별도 `debug prompt-input` 관측은 실제 prompt에 보이는 exact skill ID·description, declared/resolved source locator와 source sibling `agents/openai.yaml` declared/resolved locator·전체 metadata digest 및 `policy.allow_implicit_invocation`의 `explicit_true / explicit_false / absent_default` 상태를 content-free projection으로 만든다. Raw description이나 locator는 출력하지 않고 내부 selector state도 관측했다고 주장하지 않는다. YAML/policy를 신뢰성 있게 읽을 수 없거나 CLI marketplace/add/list 또는 prompt-input 경로가 없거나 격리 probe를 완료할 수 없으면 structural checks만 실행한 결과는 `conditional`이며 slice-pass가 아니다. Description-only·policy-only drift도 별도 negative fixture로 거절한다.

저장소 루트에서 다음처럼 실행한다. 존재하지 않는 hook·telemetry·rollout 경로도 explicit `absent` input으로 digest에 포함된다.

```bash
python3 skills/develop-change/scripts/validate_foundation.py \
  --active-plugin-root /path/to/installed/plugin \
  --active-config ~/.codex/config.toml \
  --active-hook ~/.codex/hooks.json \
  --active-telemetry ~/.codex/telemetry \
  --active-rollout ~/.codex/rollout \
  --output evals/manifests/phase1/reports/phase1-contract-foundation.json
```

Active binding은 exact `~/.codex/config.toml`과 `~/.codex/hooks.json`이다. Telemetry·rollout도 같은 root의 exact 경로를 사용하고 absent 상태는 해당 exact path의 content-free projection으로 기록한다.

Validator는 probe 직전과 직후에 active filesystem projection, `codex plugin list --json`의 전체 normalized installed set, `debug prompt-input`의 model-visible skill behavior projection을 다시 읽는다. 또한 사용한 Codex executable의 resolved path digest, byte digest와 `--version`을 전후에 결박한다. macOS에서 inventory 조회는 active `~/.codex`·`~/.agents` write와 network를 모두 막는다. Prompt-input 조회는 resolved active root 전체에 create/write deny를 적용하되 exact `installation_id`, `.tmp`, `tmp`만 예외로 남기고 `.agents` write도 별도로 차단한다. 따라서 이전에 없던 top-level state 생성도 거절한다. `installation_id`는 CLI가 writable open을 요구하지만 별도 content-free digest와 inode/device/mode/size/mtime/ctime projection으로 전후 동일성을 확인하며, source/config/plugin/session/DB/cache write는 허용하지 않는다. Prompt assembly에 필요한 read-network는 허용한다. 해당 fence를 제공할 수 없거나 metadata policy observation이 불완전한 환경의 결과는 `conditional`이다. Plugin ID·marketplace·name·version·installed/enabled·policy와 source-binding digest를 정렬해 비교하므로 target plugin 또는 unrelated installed plugin의 추가·제거·enable/version drift도 실패한다. Raw description·path·source·inventory JSON은 보고하지 않는다.

같은 실행은 `develop-skill` 자체의 strict metadata 검증, 대표 한국어 scaffold→strict validator 흐름, malformed YAML·semantic shadow regression, 그리고 저장소의 기존 skill 전체에 대한 default compatibility 검증도 수행한다. 이 항목 중 하나라도 실패하면 foundation report는 `pass`가 될 수 없다.

격리 probe는 active root를 install source나 fallback으로 쓰지 않는다. 별도 Codex/SQLite/XDG/TMP root와 local marketplace를 만들고, 지원되는 macOS에서는 child CLI의 active `~/.codex`·`~/.agents` 접근과 network도 sandbox로 차단한다. CLI는 격리 root 내부에 metadata를 쓸 수 있으므로 단순 read-only 명령으로 간주하지 않는다.

출력은 content-free runtime/inventory/effective-catalog digest, Codex executable identity, bundle digest와 case별 expected/observed rule ID만 가진다. Exit 0은 실제 isolated CLI plugin discovery와 model-visible catalog 관측까지 통과한 `pass`, exit 2는 structural-only 또는 unfenced observation의 `conditional`, exit 1은 `fail`이다. Fixture receipt·fingerprint와 synthetic 결과는 실제 authorization, runtime activation, 내부 selector state 관측 또는 성능 증거가 아니다.
