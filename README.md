# Personal Skills

This repository stores portable Agent Skills authored here and installation configurations for third-party skills and host plugins.

## Repository layout

- `skills/`: portable skills authored in this repository.
- `evals/`: trigger and output cases for owned skills, plus shared portable fixtures.
- `catalog/`: third-party skill classifications and installation metadata, without copied source.
- `scripts/`: profile resolution and thin wrappers around `npx skills` and official host installation commands.
- `docs/DESIGN.md`: the current design and working agreements.

The external catalog contains only reviewed profiles and add-ons. It does not include upstream source code.

### Owned skills

| Skill | Purpose |
| --- | --- |
| `to-commit` | Organize changes into focused English Conventional Commits |
| `to-pr` | Publish a completed branch with a concise English title and body |
| `to-skill` | Author, revise, normalize, and prepare Agent Skills for hosts |

Use `to-skill` to author new skills, revise existing skills, normalize copies across hosts, and prepare Codex and Claude Code integrations.

## Install a profile

Validate the catalog and preview the generated commands before installation.

```bash
npm run validate
npm run skills:install -- --profile react --host codex --dry-run
```

Remove `--dry-run` after reviewing the plan.

```bash
npm run skills:install -- --profile react --host codex
```

Select multiple optional groups and hosts in one command.

```bash
npm run skills:install -- \
  --profile react \
  --with alignment \
  --with skill-authoring \
  --host codex \
  --host claude-code
```

### Available selections

| Type | Name | Purpose |
| --- | --- | --- |
| profile | `react` | React component design and performance guidance |
| add-on | `view-transitions` | React and Next.js View Transition implementation |
| add-on | `design-review` | UI, UX, and accessibility review |
| add-on | `docs-writing` | Documentation and prose review |
| add-on | `alignment` | Plan, design, and domain-model alignment |
| capability | `discovery` | Third-party skill discovery |
| capability | `skill-authoring` | Host-native skill authoring tools |

Use `--profile` exactly once. Repeat `--with` and `--host` as needed. Declared dependencies are included automatically, and duplicate selections are installed once.

## Installation behavior

Third-party projects are not copied or mirrored into this repository. Installation uses upstream repositories, `npx skills`, or official host plugins.

- `shared` skills are installed through `npx skills`.
- The target project's `.agents/skills` directory is the canonical location; agent-specific paths use symlinks by default.
- `host-specific` entries are installed only for their supported hosts.
- `host-native` built-in features are reported as already available.
- Plugin commands that cannot run in a shell are printed as manual steps instead of being executed.
- When `claude-code` is requested without a `.claude/` directory, the installer warns and skips that host.
- If every requested host is skipped, the installer exits with an error before running an external command.

## Run a pinned version from another repository

Do not pipe a remote script directly into a shell. Fetch a reviewed full commit SHA into a temporary directory, then start with a dry run.

```bash
SKILLS_REF=7e852c3c8483efe19b60c90c567cf4a03940f24b
SKILLS_TMP="$(mktemp -d)"
SKILLS_REPOSITORY="$SKILLS_TMP/repository"

git init -q "$SKILLS_REPOSITORY"
git -C "$SKILLS_REPOSITORY" remote add origin \
  https://github.com/sonsu-lee/skills
git -C "$SKILLS_REPOSITORY" fetch --depth 1 origin "$SKILLS_REF"
git -C "$SKILLS_REPOSITORY" checkout -q --detach FETCH_HEAD
test "$(git -C "$SKILLS_REPOSITORY" rev-parse HEAD)" = "$SKILLS_REF"
git -C "$SKILLS_REPOSITORY" show --stat --oneline HEAD

SKILLS_REPOSITORY="$(cd "$SKILLS_REPOSITORY" && pwd -P)"

node "$SKILLS_REPOSITORY/scripts/install.mjs" \
  --profile react \
  --host codex \
  --dry-run
```

Review `scripts/install.mjs`, `scripts/validate-catalog.mjs`, `catalog/skills.json`, and `catalog/profiles.json`. Inspect the generated commands before removing `--dry-run`. The current working directory becomes the target project for installation.

```bash
node "$SKILLS_REPOSITORY/scripts/install.mjs" \
  --profile react \
  --host codex
```

Remove the temporary checkout and shell variables after installation, or when you decide not to continue.

```bash
rm -rf -- "$SKILLS_TMP"
unset SKILLS_REF SKILLS_TMP SKILLS_REPOSITORY
```

Before using a new commit, review its full SHA and diff, then update only `SKILLS_REF`.

## Verification

```bash
npm test
npm run test:e2e
npm run validate
```

See [`docs/DESIGN.md`](docs/DESIGN.md) for repository boundaries and installation design. See [`catalog/README.md`](catalog/README.md) for catalog registration rules.
