// Independent JS encoding of original public fixtures; keep per-profile progress.
import assert from 'node:assert/strict';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {Tokenizer} from '@huggingface/tokenizers';
const root=fileURLToPath(new URL('../',import.meta.url));
const json=async p=>JSON.parse(await readFile(resolve(root,p),'utf8'));
const hash=x=>createHash('sha256').update(x).digest('hex');
const out=resolve(root,process.argv[2]);assert.ok(out.startsWith(resolve(root,'results')+'/'));
const plan=await json('config/text-types-v1.json');assert.equal(hash(await readFile(resolve(root,plan.corpus))),plan.corpus_sha256);
const corpus=await json(plan.corpus);await mkdir(out,{recursive:true});
const all=[];
for(const [name,digest] of Object.entries(plan.tokenizer_locks)){
 assert.equal(hash(await readFile(resolve(root,'config',name))),digest);
 const lock=await json('config/'+name);
 for(const a of lock.assets)assert.equal(hash(await readFile(resolve(root,lock.cache_directory,a.filename))),a.sha256);
 try{
 const raw=await json(lock.cache_directory+'/tokenizer.json');
 const config=await json(lock.cache_directory+'/tokenizer_config.json');
 const tokenizer=new Tokenizer(raw,config);
 const rows=corpus.inputs.map(f=>{const ids=tokenizer.encode(f.text,{add_special_tokens:false}).ids;return {id:f.id,text_sha256:hash(f.text),token_count:ids.length,id_sequence_sha256:hash(ids.join(','))};});
 const result={model_key:lock.model_key,status:'encoded',rows};all.push(result);await writeFile(resolve(out,lock.model_key+'.json'),JSON.stringify(result,null,2)+'\n');console.log('JS encoded '+lock.model_key+': '+rows.length);
 }catch(error){const result={model_key:lock.model_key,status:'failed',error:String(error)};all.push(result);await writeFile(resolve(out,lock.model_key+'.json'),JSON.stringify(result,null,2)+'\n');console.log('JS failure '+lock.model_key+': '+String(error));}
}
await writeFile(resolve(out,'run.json'),JSON.stringify({node_version:process.version,js_tokenizers_version:(await json('node_modules/@huggingface/tokenizers/package.json')).version,script_sha256:hash(await readFile(fileURLToPath(import.meta.url))),results:all.map(({rows,...rest})=>rest)},null,2)+'\n');
