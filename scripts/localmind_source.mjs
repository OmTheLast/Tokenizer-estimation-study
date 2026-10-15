// Shared access to the hash-checked, unchanged upstream estimator and fixtures.
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { resolve } from 'node:path';

export const root = fileURLToPath(new URL('../', import.meta.url));
export const json = async path => JSON.parse(await readFile(resolve(root, path), 'utf8'));
export const digest = value => createHash('sha256').update(value).digest('hex');
const upstream = resolve(root, 'external/LocalMind');
const baseline = await json('results/2026-10-04-localmind-baseline/run.json');
export const commit = execFileSync('git', ['rev-parse', 'HEAD'], {cwd: upstream, encoding: 'utf8'}).trim();
assert.equal(commit, baseline.source_commit);
for (const [name, expected] of Object.entries(baseline.sha256)) {
  assert.equal(digest(await readFile(resolve(upstream, name))), expected, `Changed source: ${name}`);
}
const source = await readFile(resolve(upstream, 'index.html'), 'utf8');
const start = source.indexOf('// TOKEN-COUNT-START');
const end = source.indexOf('// TOKEN-COUNT-END', start);
assert.ok(start >= 0 && end > start);
export const estimator = new Function(`${source.slice(start, end)}\nreturn {countTokens, tokenClassIndex, TOKEN_CLASSES, TOKEN_WEIGHTS, TOKEN_PROFILE_BY_MODEL};`)();
export const {TOKEN_FIXTURES: fixtures} = await import(pathToFileURL(resolve(upstream, 'scripts/token-fixtures.mjs')));
assert.equal(fixtures.length, 38);
assert.equal(new Set(fixtures.map(s => s.name)).size, 38);
