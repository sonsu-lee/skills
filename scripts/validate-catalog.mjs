import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const DELIVERIES = new Set(['shared', 'host-specific', 'host-native']);
const KINDS = new Set(['skill', 'plugin', 'command', 'tool']);
const PROVIDER_TYPES = new Set(['builtin', 'plugin']);

function isNonEmptyString(value) {
  return typeof value === 'string' && value.trim().length > 0;
}

export function validateCatalog({ skills, profiles }) {
  if (!skills || typeof skills !== 'object' || Array.isArray(skills)) {
    return ['skills must be an object'];
  }
  if (!Array.isArray(skills.skills)) {
    return ['skills.skills must be an array'];
  }
  if (!profiles || typeof profiles !== 'object' || Array.isArray(profiles)) {
    return ['profiles must be an object'];
  }

  const errors = [];
  const ids = new Set();
  const skillsById = new Map();

  if (skills.schemaVersion !== 1) {
    errors.push(`unsupported skills schema version: ${skills.schemaVersion}`);
  }
  if (profiles.schemaVersion !== 1) {
    errors.push(`unsupported profiles schema version: ${profiles.schemaVersion}`);
  }

  for (const [index, skill] of skills.skills.entries()) {
    if (!skill || typeof skill !== 'object' || Array.isArray(skill)) {
      errors.push(`skill at index ${index} must be an object`);
      continue;
    }
    if (typeof skill.id !== 'string' || skill.id.trim().length === 0) {
      errors.push(`skill at index ${index} must have a non-empty string id`);
      continue;
    }
    if (ids.has(skill.id)) {
      errors.push(`duplicate skill id: ${skill.id}`);
    }
    if (!KINDS.has(skill.kind)) {
      errors.push(`${skill.id} has unsupported kind: ${skill.kind}`);
    }
    if (!DELIVERIES.has(skill.delivery)) {
      errors.push(`${skill.id} has unsupported delivery: ${skill.delivery}`);
    }
    if (
      ['shared', 'host-specific'].includes(skill.delivery) &&
      (!isNonEmptyString(skill.source?.repository) ||
        !isNonEmptyString(skill.source?.skill))
    ) {
      errors.push(
        `${skill.delivery} skill ${skill.id} requires source.repository and source.skill`,
      );
    }
    if (
      skill.delivery === 'host-specific' &&
      (!Array.isArray(skill.hosts) ||
        skill.hosts.length === 0 ||
        !skill.hosts.every(isNonEmptyString))
    ) {
      errors.push(`host-specific skill ${skill.id} requires hosts`);
    }
    if (skill.delivery === 'host-native') {
      if (
        !skill.providers ||
        typeof skill.providers !== 'object' ||
        Array.isArray(skill.providers) ||
        Object.keys(skill.providers).length === 0
      ) {
        errors.push(`host-native capability ${skill.id} requires providers`);
      } else {
        for (const [host, provider] of Object.entries(skill.providers)) {
          if (!isNonEmptyString(host)) {
            errors.push(
              `host-native capability ${skill.id} provider host must be a non-empty string`,
            );
            continue;
          }
          if (
            !provider ||
            typeof provider !== 'object' ||
            Array.isArray(provider)
          ) {
            errors.push(
              `host-native capability ${skill.id} provider ${host} must be an object`,
            );
            continue;
          }
          if (!PROVIDER_TYPES.has(provider.type)) {
            errors.push(
              `host-native capability ${skill.id} provider ${host} has unsupported type: ${provider.type}`,
            );
          }
          if (!isNonEmptyString(provider.name)) {
            errors.push(
              `host-native capability ${skill.id} provider ${host} requires a non-empty string name`,
            );
          }
        }
      }
    }
    ids.add(skill.id);
    skillsById.set(skill.id, skill);
  }

  for (const skill of skills.skills) {
    if (
      !skill ||
      typeof skill !== 'object' ||
      Array.isArray(skill) ||
      typeof skill.id !== 'string' ||
      skill.id.trim().length === 0
    ) {
      continue;
    }
    if (
      skill.dependencies !== undefined &&
      !Array.isArray(skill.dependencies)
    ) {
      errors.push(`${skill.id} dependencies must be an array`);
      continue;
    }
    for (const dependency of skill.dependencies ?? []) {
      if (!ids.has(dependency)) {
        errors.push(`${skill.id} depends on unknown skill: ${dependency}`);
      }
    }
  }

  const visited = new Set();
  const visiting = [];

  function visit(id) {
    if (visiting.includes(id)) {
      const cycleStart = visiting.indexOf(id);
      const cycle = [...visiting.slice(cycleStart), id];
      errors.push(`dependency cycle: ${cycle.join(' -> ')}`);
      return;
    }
    if (visited.has(id)) return;

    visiting.push(id);
    const dependencies = skillsById.get(id)?.dependencies;
    if (Array.isArray(dependencies)) {
      for (const dependency of dependencies) {
        if (skillsById.has(dependency)) visit(dependency);
      }
    }
    visiting.pop();
    visited.add(id);
  }

  for (const id of ids) {
    if (!errors.some((error) => error.startsWith('dependency cycle:'))) {
      visit(id);
    }
  }

  const groups = [
    ['profile', 'profiles.profiles', profiles.profiles],
    ['add-on', 'profiles.addons', profiles.addons],
    ['capability', 'profiles.capabilities', profiles.capabilities],
  ];

  for (const [groupType, groupPath, entries] of groups) {
    if (!entries || typeof entries !== 'object' || Array.isArray(entries)) {
      errors.push(`${groupPath} must be an object`);
      continue;
    }

    for (const [name, entry] of Object.entries(entries)) {
      if (!Array.isArray(entry?.skills)) {
        errors.push(`${groupType} ${name} skills must be an array`);
        continue;
      }

      const members = new Set();
      for (const id of entry.skills) {
        if (members.has(id)) {
          errors.push(`${groupType} ${name} contains duplicate skill: ${id}`);
        }
        if (!ids.has(id)) {
          errors.push(`${groupType} ${name} references unknown skill: ${id}`);
        }
        members.add(id);
      }
    }
  }

  return errors;
}

if (
  process.argv[1] &&
  import.meta.url === pathToFileURL(resolve(process.argv[1])).href
) {
  const [skills, profiles] = await Promise.all([
    readFile(new URL('../catalog/skills.json', import.meta.url), 'utf8').then(
      JSON.parse,
    ),
    readFile(new URL('../catalog/profiles.json', import.meta.url), 'utf8').then(
      JSON.parse,
    ),
  ]);
  const errors = validateCatalog({ skills, profiles });

  if (errors.length > 0) {
    for (const error of errors) console.error(error);
    process.exitCode = 1;
  } else {
    console.log('Catalog is valid.');
  }
}
