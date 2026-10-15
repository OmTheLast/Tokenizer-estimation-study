// Execute the pinned, unchanged LocalMind estimator and a fresh JS tokenizer.
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { resolve } from 'node:path';
import { Tokenizer } from '@huggingface/tokenizers';

const root = fileURLToPath(new URL('../', import.meta.url));
const json = async (path) => JSON.parse(await readFile(resolve(root, path), 'utf8'));
const lock = await json('config/qwen-tokenizer.lock.json');
const baseline = await json('results/2026-10-04-localmind-baseline/run.json');
const upstream = resolve(root, 'external/LocalMind');
const commit = execFileSync('git', ['rev-parse', 'HEAD'], { cwd: upstream, encoding: 'utf8' }).trim();
assert.equal(commit, lock.localmind_commit, 'Wrong LocalMind commit');
const digest = (value) => createHash('sha256').update(value).digest('hex');
for (const [name, expected] of Object.entries(baseline.sha256)) {
  assert.equal(digest(await readFile(resolve(upstream, name))), expected, `Changed upstream file: ${name}`);
}
for (const asset of lock.assets) {
  assert.equal(digest(await readFile(resolve(root, lock.cache_directory, asset.filename))), asset.sha256);
}
const source = await readFile(resolve(upstream, 'index.html'), 'utf8');
const start = source.indexOf('// TOKEN-COUNT-START');
const end = source.indexOf('// TOKEN-COUNT-END', start);
assert.ok(start >= 0 && end > start);
// Source is hash-checked above, and this declaration block was inspected.
const { countTokens } = new Function(`${source.slice(start, end)}\nreturn { countTokens };`)();
const { TOKEN_FIXTURES } = await import(pathToFileURL(resolve(upstream, 'scripts/token-fixtures.mjs')));
assert.equal(TOKEN_FIXTURES.length, 38);
assert.equal(new Set(TOKEN_FIXTURES.map(s => s.name)).size, 38);

const tokenizerJson = await json(`${lock.cache_directory}/tokenizer.json`);
const tokenizerConfig = await json(`${lock.cache_directory}/tokenizer_config.json`);
assert.equal(tokenizerJson.truncation, null, 'Unexpected truncation');
assert.equal(tokenizerJson.padding, null, 'Unexpected padding');
assert.ok(!tokenizerJson.model.dropout, 'Unexpected stochastic tokenization');
const tokenizer = new Tokenizer(tokenizerJson, tokenizerConfig);
const rows = TOKEN_FIXTURES.map(sample => {
  const ids = tokenizer.encode(sample.text, { add_special_tokens: false }).ids;
  assert.ok(ids.length > 0);
  assert.ok(ids.every(Number.isSafeInteger));
  return {
    name: sample.name,
    text: sample.text,
    text_sha256: digest(sample.text),
    utf16_units: sample.text.length,
    code_points: [...sample.text].length,
    utf8_bytes: Buffer.byteLength(sample.text, 'utf8'),
    saved_count: sample.actual[lock.model_key],
    js_count: ids.length,
    js_ids: ids,
    estimate: countTokens(sample.text, lock.model_key),
    old_estimate: Math.ceil(sample.text.length / 3.5),
  };
});
const pkg = await json('node_modules/@huggingface/tokenizers/package.json');
process.stdout.write(JSON.stringify({
  node_version: process.version, js_tokenizers_version: pkg.version,
  localmind_commit: commit, add_special_tokens: false, rows,
}, null, 2) + '\n');
