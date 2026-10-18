"""Measure frozen original text-type fixtures; atomic per-profile progress."""
import argparse,hashlib,json,os,platform
from pathlib import Path
import tokenizers
from tokenizers import Tokenizer
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def string_sha(s):return hashlib.sha256(s.encode()).hexdigest()
def save(p,d):
    t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');os.replace(t,p)
def main(out):
    plan_path=ROOT/'config/text-types-v1.json';plan=json.loads(plan_path.read_text())
    for field in ['corpus','builder','protocol']:assert sha(ROOT/plan[field])==plan[field+'_sha256']
    assert tokenizers.__version__=='0.23.2'
    corpus=json.loads((ROOT/plan['corpus']).read_text());assert len(corpus['inputs'])==188
    locks={}
    for name,digest in plan['tokenizer_locks'].items():
        p=ROOT/'config'/name;assert sha(p)==digest;d=json.loads(p.read_text());locks[d['model_key']]=d
    out.mkdir(parents=True,exist_ok=True)
    signature={'plan_sha256':sha(plan_path),'script_sha256':sha(Path(__file__)),'corpus_sha256':plan['corpus_sha256'],'tokenizers_version':tokenizers.__version__,'python_version':platform.python_version()}
    manifest=out/'input-manifest.json'
    if manifest.exists():assert json.loads(manifest.read_text())==signature,'Changed resume inputs'
    else:save(manifest,signature)
    all_rows=[];all_snapshots=[];inventory=[]
    for model in plan['models']:
        lock=locks[model];cache=ROOT/lock['cache_directory']
        for a in lock['assets']:assert sha(cache/a['filename'])==a['sha256']
        native=Tokenizer.from_file(str(cache/'tokenizer.json'));config=json.loads(native.to_str())
        assert not config.get('truncation') and not config.get('padding') and not config['model'].get('dropout')
        native.no_truncation();native.no_padding();derived=None
        if 'derived_asset' in lock:
            p=cache/lock['derived_asset']['filename'];assert sha(p)==lock['derived_asset']['sha256'];derived=Tokenizer.from_file(str(p))
        unk=config['model'].get('unk_id')
        if unk is None and config['model'].get('unk_token') is not None:unk=native.token_to_id(config['model']['unk_token'])
        inventory.append({'model_key':model,'algorithm':type(native.model).__name__,'revision':lock['revision'],'base_vocab_entries':native.get_vocab_size(False),'effective_vocab_entries':native.get_vocab_size(True),'unknown_id':unk,'normalizer_type':None if config['normalizer'] is None else config['normalizer']['type'],'pre_tokenizer':config['pre_tokenizer'],'decoder':config['decoder'],'derived_asset':lock.get('derived_asset')})
        shard=out/(model+'.json')
        if shard.exists():
            loaded=json.loads(shard.read_text());assert loaded['signature']==signature and loaded['model_key']==model
            assert len(loaded['rows'])==188 and loaded['rows_sha256']==string_sha(json.dumps(loaded['rows'],sort_keys=True,ensure_ascii=False))
            all_rows.extend(loaded['rows']);all_snapshots.extend(loaded['snapshots']);print('Resumed',model,flush=True);continue
        rows=[];snapshots=[]
        for f in corpus['inputs']:
            text=f['text'];assert string_sha(text)==f['text_sha256']
            enc=native.encode(text,add_special_tokens=False);special=native.encode(text,add_special_tokens=True)
            if derived is not None:assert derived.encode(text,add_special_tokens=False).ids==enc.ids
            normalized=native.normalizer.normalize_str(text) if native.normalizer else text
            decoded=native.decode(enc.ids,skip_special_tokens=False)
            row={k:v for k,v in f.items() if k!='text'}
            row.update(model_key=model,algorithm=type(native.model).__name__,tokenizer_revision=lock['revision'],token_count=len(enc.ids),with_special_count=len(special.ids),special_delta=len(special.ids)-len(enc.ids),unknown_tokens=sum(i==unk for i in enc.ids) if unk is not None else 0,characters=len(text),utf8_bytes=len(text.encode()),normalized_characters=len(normalized),normalization_changed=normalized!=text,decode_exact=decoded==text,decoded_sha256=string_sha(decoded),id_sequence_sha256=string_sha(','.join(map(str,enc.ids))))
            assert row['token_count']>0;rows.append(row)
            if f['role']=='probe' or (f['scenario']=='s01' and f['format'] in ['prose','json_compact']):
                snapshots.append({'model_key':model,'input_id':f['id'],'original':text,'normalized':normalized,'decoded':decoded,'tokens':enc.tokens,'ids':enc.ids,'unknown_tokens':row['unknown_tokens']})
        save(shard,{'signature':signature,'model_key':model,'rows':rows,'rows_sha256':string_sha(json.dumps(rows,sort_keys=True,ensure_ascii=False)),'snapshots':snapshots})
        all_rows.extend(rows);all_snapshots.extend(snapshots)
        print(f"Measured {model}: 188 inputs; {sum(r['unknown_tokens']>0 for r in rows)} contain unknown tokens; {sum(not r['decode_exact'] for r in rows)} decode mismatches (including probes).",flush=True)
    assert len(all_rows)==1128 and len({(r['model_key'],r['id']) for r in all_rows})==1128
    save(out/'measurements.json',all_rows);save(out/'token-examples.json',all_snapshots);save(out/'inventory.json',inventory)
    save(out/'measurement-validation.json',{'rows':1128,'primary_rows':sum(r['role']=='primary' for r in all_rows),'probe_rows':sum(r['role']=='probe' for r in all_rows),'all_sources_and_hashes_verified':True,'unigram_original_vs_derived_id_parity':188,'no_truncation_or_padding':True,'fitting':False,'flores_access':False})
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);args=p.parse_args();out=(ROOT/args.output).resolve();assert out.is_relative_to(ROOT/'results');main(out)
