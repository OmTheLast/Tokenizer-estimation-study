import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {Tokenizer} from '@huggingface/tokenizers';
import {root, json, digest, commit, estimator, fixtures} from './localmind_source.mjs';

const lock = await json(process.argv[2]);
assert.equal(lock.localmind_commit, commit);
for (const asset of lock.assets) {
  assert.equal(digest(await readFile(resolve(root, lock.cache_directory, asset.filename))), asset.sha256);
}
const definition = await json(`${lock.cache_directory}/tokenizer.json`);
const config = await json(`${lock.cache_directory}/tokenizer_config.json`);
assert.equal(definition.truncation, null);
assert.equal(definition.padding, null);
assert.ok(!definition.model.dropout);
const tokenizer = new Tokenizer(definition, config);
const rows = fixtures.map(s => {
  const ids = tokenizer.encode(s.text, {add_special_tokens: false}).ids;
  assert.ok(ids.length && ids.every(Number.isSafeInteger));
  return {name: s.name, text: s.text, text_sha256: digest(s.text),
    saved_count: s.actual[lock.model_key], js_count: ids.length, js_ids: ids,
    estimate: estimator.countTokens(s.text, lock.model_key), old_estimate: Math.ceil(s.text.length / 3.5)};
});
const pkg = await json('node_modules/@huggingface/tokenizers/package.json');
process.stdout.write(JSON.stringify({model_key: lock.model_key, localmind_commit: commit,
  node_version: process.version, js_tokenizers_version: pkg.version, rows}, null, 2) + '\n');
