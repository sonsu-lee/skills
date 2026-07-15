# Personal skills

This repository distributes three owned portable Agent Skills and a managed Codex plugin bundle. It also stores installation metadata for third-party skills. Choose one owned-skill channel for each Codex environment, or use the profile CLI for external catalog entries.

## Repository layout

Use these paths to find owned skills, evaluations, external metadata, installer scripts, and design documentation:

- `skills/`: portable skills authored in this repository.
- `evals/`: trigger and output cases for owned skills, plus shared portable fixtures.
- `catalog/`: third-party skill classifications and installation metadata, without copied source.
- `scripts/`: profile resolution and thin wrappers around `npx skills` and official host installation commands.
- `docs/DESIGN.md`: the current design and working agreements.

The external catalog contains only reviewed third-party entries and installation groups. It does not include upstream source code.

### Owned skills

The repository maintains these three portable skills:

| Skill | Purpose |
| --- | --- |
| `to-commit` | Organize changes into focused English Conventional Commits |
| `to-pr` | Publish a completed branch with a concise English title and body |
| `to-skill` | Author, revise, normalize, and prepare Agent Skills for hosts |

Use `to-skill` to author new skills, revise existing skills, normalize copies across hosts, and prepare Codex and Claude Code integrations.

## Choose an installation channel

Choose the channel that matches what you want to install:

| Channel | Installs | Use it when |
| --- | --- | --- |
| Skills CLI | One or more owned skills from `skills/` | You need a selective project-local installation |
| Codex `sonsu-skills` plugin | All three owned skills as one managed bundle | You want Codex to manage the complete bundle |
| Profile CLI | Third-party entries from `catalog/` | You need the reviewed profile and optional external add-ons |

Directly installed owned skills and an enabled `sonsu-skills` plugin are mutually exclusive in the same Codex environment. The profile CLI currently installs only third-party catalog entries, not owned skills or the plugin.

## Install selected owned skills directly

List the owned skills before selecting them:

```bash
npx skills add sonsu-lee/skills --list
```

Install one owned skill for Codex:

```bash
npx skills add sonsu-lee/skills \
  --skill to-commit \
  --agent codex
```

Repeat `--skill` to install more than one:

```bash
npx skills add sonsu-lee/skills \
  --skill to-commit \
  --skill to-pr \
  --agent codex
```

Run these commands from the target project. The project's `.agents/skills` directory is canonical, and host-specific paths use symlinks by default.

## Install the managed Codex plugin

Use the plugin to install all owned skills as one Codex-managed bundle. This channel does not support individual skill selection. Before installing it, remove direct owned-skill installations from the same Codex environment. The plugin does not automatically detect or remove directly installed skills.

Add the repository marketplace and install the bundle:

```bash
codex plugin marketplace add sonsu-lee/skills
codex plugin add sonsu-skills@sonsu-skills
```

The enabled plugin exposes these namespaced runtime skills:

- `sonsu-skills:to-commit`
- `sonsu-skills:to-pr`
- `sonsu-skills:to-skill`

The plugin exposes no entries from `catalog/`. Start a new Codex task after installation so Codex loads the plugin.

### Update the managed Codex plugin

Refresh the marketplace snapshot, then install the bundle again:

```bash
codex plugin marketplace upgrade sonsu-skills
codex plugin add sonsu-skills@sonsu-skills
```

Start a new Codex task after updating the plugin.

### Remove the managed Codex plugin

Remove the installed bundle from the current Codex environment:

```bash
codex plugin remove sonsu-skills@sonsu-skills
```

## Install external catalog entries

The profile CLI currently installs only third-party entries from `catalog/`. It does not install owned skills from `skills/` or the `sonsu-skills` plugin.

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

### Available profile selections

The profile CLI supports these selections:

| Type | Name | Purpose |
| --- | --- | --- |
| profile | `react` | React component design and performance guidance |
| add-on | `view-transitions` | React and Next.js View Transition implementation |
| add-on | `design-review` | UI, UX, and accessibility review |
| add-on | `docs-writing` | Documentation and prose review |
| add-on | `alignment` | Plan, design, and domain-model alignment |
| capability | `discovery` | Third-party skill discovery |
| capability | `skill-authoring` | Host-native skill authoring tools |

Use `--profile` exactly once. Repeat `--with` and `--host` as needed. The installer includes declared dependencies automatically and installs each entry once.

## External catalog installation behavior

This repository does not copy or mirror third-party projects. The installer uses upstream repositories, `npx skills`, or official host plugins and follows these rules:

- **Shared skills**: The installer uses `npx skills`.
- **Canonical path**: The target project's `.agents/skills` directory stores the source files. Agent-specific paths use symlinks by default.
- **Host-specific entries**: The installer installs each entry only for its supported hosts.
- **Host-native features**: The installer reports built-in features as already available.
- **Manual plugin commands**: The installer prints commands that cannot run in a shell.
- **Missing Claude Code directory**: The installer warns and skips `claude-code` when the project has no `.claude/` directory.
- **No available hosts**: If the installer skips every requested host, it exits before running an external command.

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

## Verify repository changes

Run these checks before committing repository changes:

```bash
npm test
npm run test:e2e
npm run validate
npm run test:plugin
```

See [`docs/DESIGN.md`](docs/DESIGN.md) for repository boundaries and installation design. See [`catalog/README.md`](catalog/README.md) for catalog registration rules.
