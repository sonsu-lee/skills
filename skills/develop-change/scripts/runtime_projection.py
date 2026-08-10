#!/usr/bin/env python3
"""Create content-free digests of active runtime and CLI discovery state.

Installed plugins and model-visible skills are intentionally separate
observations: ``plugin list --json`` is only the installed-plugin inventory,
while ``debug prompt-input`` exposes the effective ``skills_instructions``
catalog used to build a prompt.  Neither projection emits raw descriptions or
claims to expose unobservable internal selector state.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
from pathlib import Path
from typing import Iterable, Mapping, Sequence

SCHEMA_VERSION = "phase1-runtime-projection-v2"
PLUGIN_INVENTORY_SCHEMA_VERSION = "phase1-installed-plugin-inventory-v1"
EFFECTIVE_CATALOG_SCHEMA_VERSION = "phase1-effective-skill-catalog-v3"
CODEX_EXECUTABLE_SCHEMA_VERSION = "phase1-codex-executable-identity-v1"
COMPONENT_ORDER = (
    "active_plugin_root",
    "active_config",
    "active_hook",
    "active_telemetry",
    "active_rollout",
)


class ProjectionError(ValueError):
    """Raised when an explicit projection input cannot be snapshotted."""


def canonical_bytes(value: object) -> bytes:
    """Encode the closed JSON projection domain deterministically."""
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def query_installed_plugin_inventory(
    codex_executable: str,
    *,
    environment: Mapping[str, str] | None = None,
    command_prefix: Sequence[str] = (),
    cwd: str | os.PathLike[str] | None = None,
) -> list[dict[str, object]]:
    """Return a closed, sorted projection of the CLI's installed inventory."""
    try:
        completed = subprocess.run(
            [*command_prefix, codex_executable, "plugin", "list", "--json"],
            check=True,
            capture_output=True,
            text=True,
            env=dict(environment) if environment is not None else None,
            cwd=cwd,
            timeout=30,
        )
        payload = json.loads(completed.stdout)
    except OSError as exc:
        raise ProjectionError(
            "FND-PROJECTION-002: codex plugin inventory command is unavailable"
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise ProjectionError(
            "FND-PROJECTION-002: codex plugin inventory command timed out"
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise ProjectionError(
            "FND-PROJECTION-002: codex plugin inventory command failed"
        ) from exc
    except json.JSONDecodeError as exc:
        raise ProjectionError(
            "FND-PROJECTION-002: codex plugin inventory returned invalid JSON"
        ) from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("installed"), list):
        raise ProjectionError(
            "FND-PROJECTION-002: codex plugin inventory has an invalid envelope"
        )
    records: list[dict[str, object]] = []
    seen: set[str] = set()
    for raw in payload["installed"]:
        if not isinstance(raw, dict):
            raise ProjectionError(
                "FND-PROJECTION-002: installed plugin record is not an object"
            )
        required_strings = ("pluginId", "name", "marketplaceName", "version")
        if any(not isinstance(raw.get(key), str) or not raw[key] for key in required_strings):
            raise ProjectionError(
                "FND-PROJECTION-002: installed plugin identity is incomplete"
            )
        if not isinstance(raw.get("installed"), bool) or not isinstance(raw.get("enabled"), bool):
            raise ProjectionError(
                "FND-PROJECTION-002: installed plugin state is not boolean"
            )
        plugin_id = str(raw["pluginId"])
        if plugin_id in seen:
            raise ProjectionError(
                "FND-PROJECTION-002: installed plugin inventory has a duplicate plugin ID"
            )
        seen.add(plugin_id)
        source = raw.get("source")
        marketplace_source = raw.get("marketplaceSource")
        if not isinstance(source, dict) or not isinstance(marketplace_source, dict):
            raise ProjectionError(
                "FND-PROJECTION-002: installed plugin source binding is incomplete"
            )
        record = {
            "plugin_id": plugin_id,
            "name": raw["name"],
            "marketplace_name": raw["marketplaceName"],
            "version": raw["version"],
            "installed": raw["installed"],
            "enabled": raw["enabled"],
            "install_policy": raw.get("installPolicy"),
            "auth_policy": raw.get("authPolicy"),
            "source_digest": sha256_bytes(canonical_bytes(source)),
            "marketplace_source_digest": sha256_bytes(
                canonical_bytes(marketplace_source)
            ),
        }
        records.append(record)
    return sorted(records, key=lambda item: str(item["plugin_id"]))


def snapshot_installed_plugin_inventory(
    records: Sequence[dict[str, object]],
) -> dict[str, object]:
    """Digest the installed inventory without returning raw paths or sources."""
    ordered = sorted(
        (dict(record) for record in records),
        key=lambda item: (str(item.get("plugin_id")), canonical_bytes(item)),
    )
    payload = {
        "schema_version": PLUGIN_INVENTORY_SCHEMA_VERSION,
        "coverage": "installed_plugins_only",
        "selector_catalog_coverage": "not_observed",
        "records": ordered,
    }
    return {
        "schema_version": PLUGIN_INVENTORY_SCHEMA_VERSION,
        "coverage": "installed_plugins_only",
        "selector_catalog_coverage": "not_observed",
        "plugin_count": len(ordered),
        "inventory_digest": sha256_bytes(
            b"codex-installed-plugin-inventory-v1\n" + canonical_bytes(payload)
        ),
    }


def query_effective_skill_catalog(
    codex_executable: str,
    *,
    environment: Mapping[str, str] | None = None,
    command_prefix: Sequence[str] = (),
    cwd: str | os.PathLike[str] | None = None,
    locator_root: Path | None = None,
) -> list[dict[str, str]]:
    """Read and content-free-project model-visible skill behavior metadata."""
    try:
        completed = subprocess.run(
            [
                *command_prefix,
                codex_executable,
                "debug",
                "prompt-input",
                "phase1-foundation-catalog-probe",
            ],
            check=True,
            capture_output=True,
            text=True,
            env=dict(environment) if environment is not None else None,
            cwd=cwd,
            timeout=30,
        )
        payload = json.loads(completed.stdout)
    except OSError as exc:
        raise ProjectionError(
            "FND-PROJECTION-003: effective catalog command is unavailable"
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise ProjectionError(
            "FND-PROJECTION-003: effective catalog command timed out"
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise ProjectionError(
            "FND-PROJECTION-003: effective catalog command failed"
        ) from exc
    except json.JSONDecodeError as exc:
        raise ProjectionError(
            "FND-PROJECTION-003: effective catalog command returned invalid JSON"
        ) from exc
    if not isinstance(payload, list):
        raise ProjectionError(
            "FND-PROJECTION-003: effective catalog has an invalid prompt envelope"
        )
    skill_blocks: list[str] = []
    for item in payload:
        if not isinstance(item, dict) or not isinstance(item.get("content"), list):
            continue
        for block in item["content"]:
            if not isinstance(block, dict) or not isinstance(block.get("text"), str):
                continue
            text = block["text"]
            if "<skills_instructions>" in text:
                skill_blocks.append(text)
    if len(skill_blocks) != 1:
        raise ProjectionError(
            "FND-PROJECTION-003: expected one model-visible skills block"
        )
    matches = re.findall(
        r"<skills_instructions>\s*(.*?)\s*</skills_instructions>",
        skill_blocks[0],
        flags=re.DOTALL,
    )
    if len(matches) != 1:
        raise ProjectionError(
            "FND-PROJECTION-003: model-visible skills block is malformed"
        )
    available_sections = re.findall(
        r"^### Available skills[ \t]*\n(.*?)(?=^### |\Z)",
        matches[0],
        flags=re.DOTALL | re.MULTILINE,
    )
    if len(available_sections) != 1:
        raise ProjectionError(
            "FND-PROJECTION-003: expected one closed available-skills section"
        )
    bound_root = locator_root.resolve() if locator_root is not None else None
    records: list[dict[str, str]] = []
    seen: set[str] = set()
    for line in available_sections[0].splitlines():
        if not line.strip():
            continue
        if not line.startswith("- ") or " (file: " not in line:
            raise ProjectionError(
                "FND-PROJECTION-003: available skill entry is malformed"
            )
        body, raw_locator = line[2:].rsplit(" (file: ", 1)
        if not raw_locator.endswith(")"):
            raise ProjectionError(
                "FND-PROJECTION-003: effective skill locator is malformed"
            )
        if ": " not in body:
            raise ProjectionError(
                "FND-PROJECTION-003: effective skill name/description is malformed"
            )
        skill_id, description = body.split(": ", 1)
        locator = Path(raw_locator[:-1])
        if (
            not skill_id
            or not description
            or not locator.is_absolute()
            or locator.name != "SKILL.md"
        ):
            raise ProjectionError(
                "FND-PROJECTION-003: effective skill identity is malformed"
            )
        if skill_id in seen:
            raise ProjectionError(
                "FND-PROJECTION-003: effective catalog has a duplicate skill ID"
            )
        seen.add(skill_id)
        declared_locator = locator
        resolved_locator = locator.resolve()
        if not resolved_locator.is_file():
            raise ProjectionError(
                "FND-PROJECTION-003: effective skill source locator is not a file"
            )
        locator_scope = "absolute"
        normalized_locator = str(resolved_locator)
        declared_locator_scope = "absolute"
        normalized_declared_locator = str(declared_locator)
        if bound_root is not None:
            try:
                normalized_locator = resolved_locator.relative_to(bound_root).as_posix()
                locator_scope = "bound_root_relative"
            except ValueError:
                pass
            try:
                normalized_declared_locator = declared_locator.relative_to(
                    bound_root
                ).as_posix()
                declared_locator_scope = "bound_root_relative"
            except ValueError:
                pass
        metadata = resolved_locator.parent / "agents" / "openai.yaml"
        metadata_source_locator = ""
        metadata_source_scope = "absent"
        declared_metadata_source_locator = ""
        declared_metadata_source_scope = "absent"
        if metadata.exists() and not metadata.is_file():
            policy_state = "unobserved"
            metadata_state = "invalid"
            metadata_digest = sha256_bytes(b"invalid-metadata-source")
        elif not metadata.exists():
            policy_state = "absent_default"
            metadata_state = "absent"
            metadata_digest = sha256_bytes(b"openai-yaml-absent-v1")
        else:
            try:
                declared_metadata = metadata
                declared_metadata_source_locator = str(declared_metadata)
                declared_metadata_source_scope = "absolute"
                if bound_root is not None:
                    try:
                        declared_metadata_source_locator = (
                            declared_metadata.relative_to(bound_root).as_posix()
                        )
                        declared_metadata_source_scope = "bound_root_relative"
                    except ValueError:
                        pass
                resolved_metadata = metadata.resolve()
                metadata_source_locator = str(resolved_metadata)
                metadata_source_scope = "absolute"
                if bound_root is not None:
                    try:
                        metadata_source_locator = resolved_metadata.relative_to(
                            bound_root
                        ).as_posix()
                        metadata_source_scope = "bound_root_relative"
                    except ValueError:
                        pass
                metadata_bytes = resolved_metadata.read_bytes()
                metadata_digest = sha256_bytes(metadata_bytes)
                metadata_state = "present"
                import yaml  # type: ignore[import-not-found]

                document = yaml.safe_load(metadata_bytes.decode("utf-8"))
                if document is None:
                    document = {}
                if not isinstance(document, dict):
                    raise ValueError("metadata root is not an object")
                policy = document.get("policy")
                if policy is None:
                    policy_state = "absent_default"
                elif not isinstance(policy, dict):
                    raise ValueError("metadata policy is not an object")
                else:
                    allow_implicit = policy.get("allow_implicit_invocation")
                    if allow_implicit is None:
                        policy_state = "absent_default"
                    elif allow_implicit is True:
                        policy_state = "explicit_true"
                    elif allow_implicit is False:
                        policy_state = "explicit_false"
                    else:
                        raise ValueError("implicit invocation policy is not boolean")
            except Exception:
                policy_state = "unobserved"
                metadata_state = "unobserved"
                metadata_digest = sha256_bytes(b"openai-yaml-unobserved-v1")
        records.append(
            {
                "skill_id": skill_id,
                "description_digest": sha256_bytes(description.encode("utf-8")),
                "declared_source_locator": normalized_declared_locator,
                "declared_source_scope": declared_locator_scope,
                "source_locator": normalized_locator,
                "source_scope": locator_scope,
                "metadata_state": metadata_state,
                "metadata_digest": metadata_digest,
                "declared_metadata_source_locator": (
                    declared_metadata_source_locator
                ),
                "declared_metadata_source_scope": declared_metadata_source_scope,
                "metadata_source_locator": metadata_source_locator,
                "metadata_source_scope": metadata_source_scope,
                "implicit_invocation_policy": policy_state,
            }
        )
    if not records:
        raise ProjectionError("FND-PROJECTION-003: effective skill catalog is empty")
    return sorted(records, key=lambda item: item["skill_id"])


def snapshot_effective_skill_catalog(
    records: Sequence[dict[str, str]],
) -> dict[str, object]:
    """Digest exact model-visible identities and locators without descriptions."""
    ordered = sorted(
        (dict(record) for record in records),
        key=lambda item: (item.get("skill_id", ""), canonical_bytes(item)),
    )
    projection = [
        {
            "skill_id": item["skill_id"],
            "description_digest": item["description_digest"],
            "declared_source_scope": item["declared_source_scope"],
            "declared_source_locator_digest": sha256_bytes(
                item["declared_source_locator"].encode("utf-8")
            ),
            "source_scope": item["source_scope"],
            "source_locator_digest": sha256_bytes(
                item["source_locator"].encode("utf-8")
            ),
            "metadata_state": item["metadata_state"],
            "metadata_digest": item["metadata_digest"],
            "declared_metadata_source_scope": item[
                "declared_metadata_source_scope"
            ],
            "declared_metadata_source_locator_digest": sha256_bytes(
                item["declared_metadata_source_locator"].encode("utf-8")
            ),
            "metadata_source_scope": item["metadata_source_scope"],
            "metadata_source_locator_digest": sha256_bytes(
                item["metadata_source_locator"].encode("utf-8")
            ),
            "implicit_invocation_policy": item["implicit_invocation_policy"],
        }
        for item in ordered
    ]
    policy_observation_status = (
        "complete"
        if all(item["implicit_invocation_policy"] != "unobserved" for item in ordered)
        else "incomplete"
    )
    payload = {
        "schema_version": EFFECTIVE_CATALOG_SCHEMA_VERSION,
        "coverage": "model_visible_skills_instructions",
        "policy_observation_status": policy_observation_status,
        "records": projection,
    }
    return {
        "schema_version": EFFECTIVE_CATALOG_SCHEMA_VERSION,
        "coverage": "model_visible_skills_instructions",
        "policy_observation_status": policy_observation_status,
        "skill_count": len(projection),
        "catalog_digest": sha256_bytes(
            b"codex-effective-skill-catalog-v3\n" + canonical_bytes(payload)
        ),
    }


def snapshot_codex_executable_identity(codex_executable: str) -> dict[str, object]:
    """Bind validation evidence to one executable path, byte digest, and version."""
    resolved = shutil.which(codex_executable)
    if resolved is None:
        raise ProjectionError("FND-PROJECTION-004: codex executable is unavailable")
    path = Path(resolved).resolve()
    if not path.is_file():
        raise ProjectionError("FND-PROJECTION-004: codex executable is not a file")
    try:
        completed = subprocess.run(
            [str(path), "--version"],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise ProjectionError("FND-PROJECTION-004: codex version probe failed") from exc
    version = completed.stdout.strip()
    if not version or "\n" in version:
        raise ProjectionError("FND-PROJECTION-004: codex version output is malformed")
    return {
        "schema_version": CODEX_EXECUTABLE_SCHEMA_VERSION,
        "version": version,
        "path_digest": sha256_bytes(str(path).encode("utf-8")),
        "executable_digest": _file_digest(path),
    }


def _active_cli_observation_guards(
    active_codex_root: Path,
) -> tuple[list[str], str, list[str], str]:
    """Return installed-inventory and effective-catalog sandbox prefixes."""
    sandbox = shutil.which("sandbox-exec")
    if not sandbox:
        return (
            [],
            "unfenced_active_inventory_read",
            [],
            "unfenced_active_effective_catalog_read",
        )
    agents_root = Path.home() / ".agents"
    inventory_clauses = " ".join(
        f"(deny file-write* (subpath {json.dumps(str(path))}))"
        for path in (active_codex_root, agents_root)
    )
    inventory_profile = (
        f"(version 1) (allow default) (deny network*) {inventory_clauses}"
    )
    root = active_codex_root.resolve()
    root_filter = (
        f"(deny file-write* (require-all (subpath {json.dumps(str(root))}) "
        f"(require-not (subpath {json.dumps(str(root / 'tmp'))})) "
        f"(require-not (subpath {json.dumps(str(root / '.tmp'))})) "
        f"(require-not (literal {json.dumps(str(root / 'installation_id'))}))))"
    )
    agents_filter = (
        f"(deny file-write* (subpath {json.dumps(str(agents_root.resolve()))}))"
    )
    catalog_profile = f"(version 1) (allow default) {root_filter} {agents_filter}"
    return (
        [sandbox, "-p", inventory_profile],
        "sandboxed_read_only_active_inventory",
        [sandbox, "-p", catalog_profile],
        "sandboxed_minimal_active_effective_catalog",
    )


def _active_observer_state(active_codex_root: Path) -> dict[str, object]:
    installation_id = active_codex_root / "installation_id"
    if not installation_id.exists():
        return {"state": "absent", "digest": sha256_bytes(b"absent")}
    if not installation_id.is_file() or installation_id.is_symlink():
        raise ProjectionError(
            "FND-PROJECTION-003: active installation identity is not a regular file"
        )
    info = installation_id.stat()
    return {
        "state": "present",
        "digest": _file_digest(installation_id),
        "size": info.st_size,
        "mode": stat.S_IMODE(info.st_mode),
        "device": info.st_dev,
        "inode": info.st_ino,
        "mtime_ns": info.st_mtime_ns,
        "ctime_ns": info.st_ctime_ns,
    }


def _file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _entry_record(root: Path, path: Path) -> dict[str, object]:
    info = path.lstat()
    relative = "." if path == root else path.relative_to(root).as_posix()
    path_token = sha256_bytes(relative.encode("utf-8"))
    mode = stat.S_IMODE(info.st_mode)
    if stat.S_ISREG(info.st_mode):
        return {
            "path_token": path_token,
            "kind": "file",
            "mode": mode,
            "size": info.st_size,
            "content_digest": _file_digest(path),
        }
    if stat.S_ISDIR(info.st_mode):
        return {"path_token": path_token, "kind": "directory", "mode": mode}
    if stat.S_ISLNK(info.st_mode):
        target = os.readlink(path)
        return {
            "path_token": path_token,
            "kind": "symlink",
            "mode": mode,
            "target_digest": sha256_bytes(target.encode("utf-8")),
        }
    return {"path_token": path_token, "kind": "other", "mode": mode}


def _input_record(raw_path: str) -> dict[str, object]:
    path = Path(raw_path).expanduser()
    absolute = path.absolute()
    path_fingerprint = sha256_bytes(str(absolute).encode("utf-8"))
    if not path.exists() and not path.is_symlink():
        payload = {"path_fingerprint": path_fingerprint, "kind": "absent"}
        return {
            "entry_count": 0,
            "digest": sha256_bytes(
                b"codex-runtime-projection-input-v1\n" + canonical_bytes(payload)
            ),
        }
    entries = [_entry_record(absolute, absolute)]
    if absolute.is_dir() and not absolute.is_symlink():
        descendants = sorted(
            absolute.rglob("*"), key=lambda item: item.relative_to(absolute).as_posix()
        )
        entries.extend(_entry_record(absolute, item) for item in descendants)
    payload = {
        "path_fingerprint": path_fingerprint,
        "kind": "present",
        "entries": entries,
    }
    return {
        "entry_count": len(entries),
        "digest": sha256_bytes(
            b"codex-runtime-projection-input-v1\n" + canonical_bytes(payload)
        ),
    }


def snapshot_projection(
    *,
    active_plugin_roots: Sequence[str],
    active_configs: Sequence[str],
    active_hooks: Sequence[str],
    active_telemetry: Sequence[str],
    active_rollout: Sequence[str],
    installed_plugin_inventory: Mapping[str, object] | None = None,
    effective_skill_catalog: Mapping[str, object] | None = None,
    codex_executable_identity: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Snapshot explicit runtime components without returning paths or contents."""
    raw_components = {
        "active_plugin_root": active_plugin_roots,
        "active_config": active_configs,
        "active_hook": active_hooks,
        "active_telemetry": active_telemetry,
        "active_rollout": active_rollout,
    }
    components: list[dict[str, object]] = []
    for kind in COMPONENT_ORDER:
        paths = raw_components[kind]
        if not paths:
            raise ProjectionError(
                f"FND-PROJECTION-001: at least one explicit {kind} input is required"
            )
        inputs = sorted((_input_record(path) for path in paths), key=lambda item: item["digest"])
        payload = {"kind": kind, "inputs": inputs}
        components.append(
            {
                "kind": kind,
                "input_count": len(inputs),
                "entry_count": sum(int(item["entry_count"]) for item in inputs),
                "digest": sha256_bytes(
                    b"codex-runtime-projection-component-v1\n" + canonical_bytes(payload)
                ),
            }
        )
    projection_payload: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "components": components,
    }
    if installed_plugin_inventory is not None:
        if installed_plugin_inventory.get("coverage") != "installed_plugins_only":
            raise ProjectionError(
                "FND-PROJECTION-002: runtime projection received the wrong inventory scope"
            )
        projection_payload["installed_plugin_inventory"] = {
            "schema_version": installed_plugin_inventory.get("schema_version"),
            "coverage": installed_plugin_inventory.get("coverage"),
            "selector_catalog_coverage": installed_plugin_inventory.get(
                "selector_catalog_coverage"
            ),
            "plugin_count": installed_plugin_inventory.get("plugin_count"),
            "inventory_digest": installed_plugin_inventory.get("inventory_digest"),
        }
    if effective_skill_catalog is not None:
        if effective_skill_catalog.get("coverage") != "model_visible_skills_instructions":
            raise ProjectionError(
                "FND-PROJECTION-003: runtime projection received the wrong catalog scope"
            )
        projection_payload["effective_skill_catalog"] = {
            "schema_version": effective_skill_catalog.get("schema_version"),
            "coverage": effective_skill_catalog.get("coverage"),
            "policy_observation_status": effective_skill_catalog.get(
                "policy_observation_status"
            ),
            "skill_count": effective_skill_catalog.get("skill_count"),
            "catalog_digest": effective_skill_catalog.get("catalog_digest"),
        }
    if codex_executable_identity is not None:
        projection_payload["codex_executable_identity"] = dict(
            codex_executable_identity
        )
    return {
        **projection_payload,
        "binding_status": "unverified_explicit_inputs",
        "projection_digest": sha256_bytes(
            b"codex-runtime-projection-v1\n" + canonical_bytes(projection_payload)
        ),
    }


def _paths(values: Iterable[str] | None) -> list[str]:
    return list(values or [])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--active-plugin-root", action="append")
    parser.add_argument("--active-config", action="append")
    parser.add_argument("--active-hook", action="append")
    parser.add_argument("--active-telemetry", action="append")
    parser.add_argument("--active-rollout", action="append")
    parser.add_argument("--codex-executable", default="codex")
    args = parser.parse_args()
    try:
        active_configs = _paths(args.active_config)
        if len(active_configs) == 1:
            active_codex_root = Path(active_configs[0]).expanduser().absolute().parent
            (
                inventory_prefix,
                inventory_observer,
                catalog_prefix,
                catalog_observer,
            ) = _active_cli_observation_guards(active_codex_root)
            active_environment = dict(os.environ)
            active_environment["CODEX_HOME"] = str(active_codex_root)
        else:
            active_codex_root = Path(
                os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))
            ).expanduser().absolute()
            inventory_prefix = []
            catalog_prefix = []
            inventory_observer = "unfenced_active_inventory_read"
            catalog_observer = "unfenced_active_effective_catalog_read"
            active_environment = dict(os.environ)
        before_observer_state = _active_observer_state(active_codex_root)
        executable_identity = snapshot_codex_executable_identity(
            args.codex_executable
        )
        inventory_records = query_installed_plugin_inventory(
            args.codex_executable,
            environment=active_environment,
            command_prefix=inventory_prefix,
            cwd=Path.cwd(),
        )
        inventory = snapshot_installed_plugin_inventory(inventory_records)
        catalog_records = query_effective_skill_catalog(
            args.codex_executable,
            environment=active_environment,
            command_prefix=catalog_prefix,
            cwd=Path.cwd(),
        )
        catalog = snapshot_effective_skill_catalog(catalog_records)
        after_observer_state = _active_observer_state(active_codex_root)
        projection = snapshot_projection(
            active_plugin_roots=_paths(args.active_plugin_root),
            active_configs=_paths(args.active_config),
            active_hooks=_paths(args.active_hook),
            active_telemetry=_paths(args.active_telemetry),
            active_rollout=_paths(args.active_rollout),
            installed_plugin_inventory=inventory,
            effective_skill_catalog=catalog,
            codex_executable_identity=executable_identity,
        )
    except ProjectionError as exc:
        parser.error(str(exc))
    observation_status = (
        "pass"
        if (
            inventory_observer == "sandboxed_read_only_active_inventory"
            and catalog_observer == "sandboxed_minimal_active_effective_catalog"
            and catalog["policy_observation_status"] == "complete"
            and before_observer_state == after_observer_state
        )
        else "conditional"
    )
    projection["cli_observation"] = {
        "status": observation_status,
        "installed_inventory_observer": inventory_observer,
        "effective_catalog_observer": catalog_observer,
        "policy_observation_status": catalog["policy_observation_status"],
        "writable_non_temp_observer_state_equal": (
            before_observer_state == after_observer_state
        ),
    }
    print(json.dumps(projection, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if observation_status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
