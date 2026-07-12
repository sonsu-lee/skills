import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const DELIVERIES = new Set(['shared', 'host-specific', 'host-native']);

export function validateCatalog({ skills, profiles }) {
  const errors = [];
  const ids = new Set();
  const skillsById = new Map();

  if (skills.schemaVersion !== 1) {
    errors.push(`unsupported skills schema version: ${skills.schemaVersion}`);
  }
  if (profiles.schemaVersion !== 1) {
    errors.push(`unsupported profiles schema version: ${profiles.schemaVersion}`);
  }

  for (const skill of skills.skills) {
    if (ids.has(skill.id)) {
      errors.push(`duplicate skill id: ${skill.id}`);
    }
    if (!DELIVERIES.has(skill.delivery)) {
      errors.push(`${skill.id} has unsupported delivery: ${skill.delivery}`);
    }
    if (
      ['shared', 'host-specific'].includes(skill.delivery) &&
      (!skill.source?.repository || !skill.source?.skill)
    ) {
      errors.push(
        `${skill.delivery} skill ${skill.id} requires source.repository and source.skill`,
      );
    }
    if (
      skill.delivery === 'host-specific' &&
      (!Array.isArray(skill.hosts) || skill.hosts.length === 0)
    ) {
      errors.push(`host-specific skill ${skill.id} requires hosts`);
    }
    if (
      skill.delivery === 'host-native' &&
      (!skill.providers || Object.keys(skill.providers).length === 0)
    ) {
      errors.push(`host-native capability ${skill.id} requires providers`);
    }
    ids.add(skill.id);
    skillsById.set(skill.id, skill);
  }

  for (const skill of skills.skills) {
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
    for (const dependency of skillsById.get(id)?.dependencies ?? []) {
      if (skillsById.has(dependency)) visit(dependency);
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
    ['profile', profiles.profiles],
    ['add-on', profiles.addons],
    ['capability', profiles.capabilities],
  ];

  for (const [groupType, entries] of groups) {
    for (const [name, entry] of Object.entries(entries)) {
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
    readFile('catalog/skills.json', 'utf8').then(JSON.parse),
    readFile('catalog/profiles.json', 'utf8').then(JSON.parse),
  ]);
  const errors = validateCatalog({ skills, profiles });

  if (errors.length > 0) {
    for (const error of errors) console.error(error);
    process.exitCode = 1;
  } else {
    console.log('Catalog is valid.');
  }
}
