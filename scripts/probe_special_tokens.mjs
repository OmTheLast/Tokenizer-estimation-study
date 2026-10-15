// Diagnostic only: compare documented option, defaults and fixture-comment spelling.
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {Tokenizer} from '@huggingface/tokenizers';
import {root, json, digest, commit, fixtures} from './localmind_source.mjs';

const lock = await json(process.argv[2]);
assert.equal(lock.localmind_commit, commit);
for (const asset of lock.assets) {
  assert.equal(digest(await readFile(resolve(root, lock.cache_directory, asset.filename))), asset.sha256);
}
const tokenizer = new Tokenizer(await json(`${lock.cache_directory}/tokenizer.json`), await json(`${lock.cache_directory}/tokenizer_config.json`));
const rows = fixtures.map(s => ({name: s.name, text: s.text, saved_count: s.actual[lock.model_key],
  false_ids: tokenizer.encode(s.text, {add_special_tokens: false}).ids,
  true_ids: tokenizer.encode(s.text, {add_special_tokens: true}).ids,
  default_ids: tokenizer.encode(s.text).ids,
  // Deliberately use the unrecognized camelCase spelling to test the hypothesis.
  camel_false_ids: tokenizer.encode(s.text, {addSpecialTokens: false}).ids,
}));
const first = rows[0];
const prefix = first.true_ids.length > first.false_ids.length ? first.true_ids.slice(0, first.true_ids.length - first.false_ids.length) : [];
process.stdout.write(JSON.stringify({model_key: lock.model_key, rows,
  candidate_prefix: prefix.map(id => ({id, token: tokenizer.id_to_token(id)}))}, null, 2) + '\n');
