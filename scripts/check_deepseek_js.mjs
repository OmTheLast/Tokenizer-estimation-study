// Independent JS tokenization; persist hashes/counts, never text or token sequences.
import assert from 'node:assert/strict';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {Tokenizer} from '@huggingface/tokenizers';
const root=fileURLToPath(new URL('../',import.meta.url));
const json=async p=>JSON.parse(await readFile(resolve(root,p),'utf8'));
const hash=x=>createHash('sha256').update(x).digest('hex');
const out=resolve(root,process.argv[2]);
assert.ok(out.startsWith(resolve(root,'results')+'/'));
const plan=await json('config/deepseek-extension-v1.json');
for(const [path,digest] of Object.entries(plan.files_sha256))assert.equal(hash(await readFile(resolve(root,path))),digest);
assert.equal(hash(await readFile(resolve(root,plan.private_corpus))),plan.private_corpus_sha256);
const corpus=await json(plan.private_corpus);assert.equal(corpus.inputs.length,140);
const version=(await json('node_modules/@huggingface/tokenizers/package.json')).version;
assert.equal(version,plan.js_tokenizers_version);
await mkdir(out,{recursive:false});
const all=[];
for(const [name,digest] of Object.entries(plan.tokenizer_locks)){
 assert.equal(hash(await readFile(resolve(root,'config',name))),digest);
 const lock=await json('config/'+name);
 if(!plan.new_models.includes(lock.model_key))continue;
 for(const a of lock.assets)assert.equal(hash(await readFile(resolve(root,lock.cache_directory,a.filename))),a.sha256);
 const raw=await json(lock.cache_directory+'/tokenizer.json');
 const config=await json(lock.cache_directory+'/tokenizer_config.json');
 assert.ok(!raw.truncation && !raw.padding && !raw.model.dropout);
 const tokenizer=new Tokenizer(raw,config);
 const rows=corpus.inputs.map(f=>{
  assert.equal(hash(f.text),f.text_sha256);
  const ids=tokenizer.encode(f.text,{add_special_tokens:false}).ids;
  return {id:f.id,text_sha256:hash(f.text),token_count:ids.length,id_sequence_sha256:hash(ids.join(','))};
 });
 const probes=await json(plan.probes);
 const probeRows=probes.inputs.map(f=>{const ids=tokenizer.encode(f.text,{add_special_tokens:false}).ids;return {id:f.id,text_sha256:hash(f.text),token_count:ids.length,id_sequence_sha256:hash(ids.join(','))};});
 await writeFile(resolve(out,lock.model_key+'-probes.json'),JSON.stringify(probeRows,null,2)+'\n');
 const result={model_key:lock.model_key,status:'encoded',rows};
 await writeFile(resolve(out,lock.model_key+'.json'),JSON.stringify(result,null,2)+'\n');
 all.push({model_key:lock.model_key,status:'encoded',rows:rows.length});
 console.log('JS encoded '+lock.model_key+': '+rows.length);
}
await writeFile(resolve(out,'run.json'),JSON.stringify({node_version:process.version,
 js_tokenizers_version:version,script_sha256:hash(await readFile(fileURLToPath(import.meta.url))),
 plan_sha256:hash(await readFile(resolve(root,'config/deepseek-extension-v1.json'))),results:all},null,2)+'\n');
