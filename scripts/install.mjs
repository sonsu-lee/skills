import { spawnSync } from 'node:child_process';
import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

import { validateCatalog } from './validate-catalog.mjs';

function readValue(args, index, option) {
  const value = args[index + 1];
  if (!value || value.startsWith('--')) {
    throw new Error(`${option} requires a value`);
  }
  return value;
}

export function parseArgs(args) {
  const options = {
    profile: undefined,
    with: [],
    hosts: [],
    dryRun: false,
  };

  for (let index = 0; index < args.length; index += 1) {
    const option = args[index];

    if (option === '--profile') {
      if (options.profile) {
        throw new Error('--profile can only be used once');
      }
      options.profile = readValue(args, index, option);
      index += 1;
    } else if (option === '--with') {
      options.with.push(readValue(args, index, option));
      index += 1;
    } else if (option === '--host') {
      options.hosts.push(readValue(args, index, option));
      index += 1;
    } else if (option === '--dry-run') {
      options.dryRun = true;
    } else {
      throw new Error(`unknown option: ${option}`);
    }
  }

  if (!options.profile) {
    throw new Error('--profile is required');
  }
  if (options.hosts.length === 0) {
    throw new Error('--host is required');
  }

  return options;
}

export function resolveSelection(catalog, selection) {
  const profile = catalog.profiles.profiles[selection.profile];
  if (!profile) {
    throw new Error(`unknown profile: ${selection.profile}`);
  }

  const selected = [...profile.skills];
  for (const name of selection.with) {
    const addon = catalog.profiles.addons[name];
    const capability = catalog.profiles.capabilities[name];
    if (addon && capability) {
      throw new Error(`ambiguous --with group: ${name}`);
    }
    const group = addon ?? capability;
    if (!group) {
      throw new Error(`unknown --with group: ${name}`);
    }
    selected.push(...group.skills);
  }

  const skills = new Map(
    catalog.skills.skills.map((skill) => [skill.id, skill]),
  );
  const resolved = [];
  const visited = new Set();
  const visiting = [];

  function visit(id, parent) {
    const skill = skills.get(id);
    if (!skill) {
      if (parent) {
        throw new Error(`${parent} depends on unknown skill: ${id}`);
      }
      throw new Error(`selection references unknown skill: ${id}`);
    }
    if (visiting.includes(id)) {
      const start = visiting.indexOf(id);
      throw new Error(
        `dependency cycle: ${[...visiting.slice(start), id].join(' -> ')}`,
      );
    }
    if (visited.has(id)) return;

    visiting.push(id);
    for (const dependency of skill.dependencies ?? []) {
      visit(dependency, id);
    }
    visiting.pop();
    visited.add(id);
    resolved.push(id);
  }

  for (const id of selected) {
    visit(id);
  }

  return resolved;
}

export function buildPlan(catalog, selectedIds, requestedHosts) {
  const skills = new Map(
    catalog.skills.skills.map((skill) => [skill.id, skill]),
  );
  const hosts = [...new Set(requestedHosts)];
  const plan = [];
  let lastBatch;

  function addCommand(skill, targetHosts) {
    const key = `${skill.source.repository}\0${targetHosts.join('\0')}`;
    if (!lastBatch || lastBatch.key !== key) {
      const step = {
        type: 'command',
        skillIds: [],
        command: 'npx',
        args: [],
      };
      plan.push(step);
      lastBatch = { key, step, repository: skill.source.repository, targetHosts };
    }

    lastBatch.step.skillIds.push(skill.id);
    const skillNames = lastBatch.step.skillIds.map(
      (id) => skills.get(id).source.skill,
    );
    lastBatch.step.args = [
      '--yes',
      'skills',
      'add',
      lastBatch.repository,
      '--skill',
      ...skillNames,
      '--agent',
      ...lastBatch.targetHosts,
      '--yes',
    ];
  }

  function addStep(step) {
    plan.push(step);
    lastBatch = undefined;
  }

  for (const id of selectedIds) {
    const skill = skills.get(id);
    if (!skill) {
      throw new Error(`selected skill is missing from catalog: ${id}`);
    }

    if (skill.delivery === 'shared') {
      addCommand(skill, hosts);
    } else if (skill.delivery === 'host-specific') {
      const targetHosts = hosts.filter((host) => skill.hosts.includes(host));
      if (targetHosts.length === 0) {
        addStep({
          type: 'skip',
          skillId: id,
          reason: 'not available for requested hosts',
        });
      } else {
        addCommand(skill, targetHosts);
      }
    } else if (skill.delivery === 'host-native') {
      for (const host of hosts) {
        const provider = skill.providers[host];
        if (!provider) {
          addStep({
            type: 'skip',
            skillId: id,
            host,
            reason: 'no host-native provider',
          });
        } else if (provider.type === 'builtin') {
          addStep({
            type: 'builtin',
            skillId: id,
            host,
            name: provider.name,
          });
        } else {
          addStep({
            type: 'manual',
            skillId: id,
            host,
            name: provider.name,
            instruction:
              provider.install ?? `Install ${provider.name} for ${host}`,
          });
        }
      }
    } else {
      throw new Error(`unsupported delivery for ${id}: ${skill.delivery}`);
    }
  }

  return plan;
}

function quoteArgument(argument) {
  if (/^[A-Za-z0-9_@%+=:,./-]+$/.test(argument)) return argument;
  return `'${argument.replaceAll("'", "'\\''")}'`;
}

function formatStep(step) {
  if (step.type === 'command') {
    return `$ ${[step.command, ...step.args].map(quoteArgument).join(' ')}`;
  }
  if (step.type === 'builtin') {
    return `builtin ${step.host}: ${step.name} (${step.skillId})`;
  }
  if (step.type === 'manual') {
    return `manual ${step.host}: ${step.instruction} (${step.skillId})`;
  }
  const host = step.host ? ` for ${step.host}` : '';
  return `skip ${step.skillId}${host}: ${step.reason}`;
}

export function executePlan(
  plan,
  { dryRun = false, run = spawnSync, write = console.log } = {},
) {
  for (const step of plan) {
    write(formatStep(step));
    if (dryRun || step.type !== 'command') continue;

    const result = run(step.command, step.args, { stdio: 'inherit' });
    if (result.error) throw result.error;
    if (result.status !== 0) {
      throw new Error(`command failed with exit code ${result.status}`);
    }
  }
}

export async function loadCatalog() {
  const [skills, profiles] = await Promise.all([
    readFile(new URL('../catalog/skills.json', import.meta.url), 'utf8').then(
      JSON.parse,
    ),
    readFile(new URL('../catalog/profiles.json', import.meta.url), 'utf8').then(
      JSON.parse,
    ),
  ]);
  return { skills, profiles };
}

export async function runCli(args) {
  const options = parseArgs(args);
  const catalog = await loadCatalog();
  const errors = validateCatalog(catalog);
  if (errors.length > 0) {
    throw new Error(`catalog validation failed:\n- ${errors.join('\n- ')}`);
  }

  const selectedIds = resolveSelection(catalog, options);
  const plan = buildPlan(catalog, selectedIds, options.hosts);
  if (options.dryRun) {
    console.log('Dry run; no commands will be executed.');
  }
  executePlan(plan, { dryRun: options.dryRun });
}

if (
  process.argv[1] &&
  import.meta.url === pathToFileURL(resolve(process.argv[1])).href
) {
  try {
    await runCli(process.argv.slice(2));
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}
