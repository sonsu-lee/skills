# External skills catalog

This catalog records the source, classification, and installation method for third-party skills.

This catalog does not copy or mirror third-party source code. Use upstream repositories, `npx skills`, or official host plugins to install and update entries.

## Registration rules

Add an external skill only after the user selects it. Record:

- Intended use
- Upstream repository
- Source skill path
- Upstream license link
- Type: skill, plugin, command, or tool
- Delivery: shared, host-specific, or host-native
- Host-specific providers and official installation commands
- Required related entries
- Profiles and add-ons
- Last verification date
- Installation side effects and trust considerations

Only shared skills use `.agents/skills` as the source of truth. Install host-specific capabilities in the host's dedicated location, as built-in features, or through official plugins.

## Registered skills

Machine-readable data lives in:

- [`skills.json`](skills.json): source, delivery, dependencies, and providers for third-party skills
- [`profiles.json`](profiles.json): the `react` profile, optional add-ons, and global capabilities

Published groups:

- Profile: `react`
- Add-on: `view-transitions`, `design-review`, `docs-writing`, `alignment`
- Global capability: `discovery`, `skill-authoring`

See the [`initial third-party skill selection decision`](../research/reports/2026-07-12-initial-skill-selection.md) for the rationale and constraints behind each entry.

## Installation selections

The `react` profile includes:

- `vercel-composition-patterns`
- `vercel-react-best-practices`

Add optional groups with `--with`:

| Name | Included entries |
| --- | --- |
| `view-transitions` | `vercel-react-view-transitions` |
| `design-review` | `web-design-guidelines` |
| `docs-writing` | `writing-guidelines` |
| `alignment` | `grill-me`, `grill-with-docs`, and their declared dependencies |
| `discovery` | `find-skills` |
| `skill-authoring` | Per-host `skill-creator` provider |

The installer orders declared dependencies before each selected entry. For example, `grilling` precedes `grill-me`; `grilling` and `domain-modeling` precede `grill-with-docs`.

See the [repository README](../README.md) for owned-skill, `sonsu-skills` plugin, profile, and commit-pinned remote installation.
