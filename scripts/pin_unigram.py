"""Pin XLM-R tokenizer assets; preserve legacy JSON and record runtime serialization."""
import argparse, hashlib, json, subprocess
from pathlib import Path
import tokenizers
from tokenizers import Tokenizer
ROOT=Path(__file__).resolve().parents[1]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main(revision):
    assert len(revision)==40 and all(c in '0123456789abcdef' for c in revision)
    repo='FacebookAI/xlm-roberta-base';cache=ROOT/'.cache/tokenizers/xlm-roberta-base'/revision;cache.mkdir(parents=True,exist_ok=True)
    assets=[]
    for name in ['tokenizer.json','tokenizer_config.json','README.md']:
        p=cache/name;url=f'https://huggingface.co/{repo}/resolve/{revision}/{name}'
        if not p.exists():
            partial=p.with_suffix(p.suffix+'.download');subprocess.run(['curl','--fail','--silent','--show-error','--location','--retry','2','--max-time','120','--output',str(partial),url],check=True);partial.replace(p)
        assets.append({'filename':name,'url':url,'sha256':sha(p),'bytes':p.stat().st_size})
    native=Tokenizer.from_file(str(cache/'tokenizer.json'));assert type(native.model).__name__=='Unigram'
    canonical=cache/'tokenizer-runtime.json';canonical.write_text(native.to_str()+'\n');parsed=json.loads(canonical.read_text());assert parsed['model']['type']=='Unigram'
    d={'model_key':'xlm-roberta-base','repository':repo,'revision':revision,'cache_directory':str(cache.relative_to(ROOT)),'add_special_tokens':False,'assets':assets,'runtime_model_type':'Unigram','base_vocab_entries':native.get_vocab_size(False),'effective_vocab_entries':native.get_vocab_size(True),'source_schema_note':'Original legacy JSON has no model.type field; tokenizers runtime loads it as Unigram. Original bytes preserved.','derived_asset':{'filename':canonical.name,'sha256':sha(canonical),'bytes':canonical.stat().st_size,'method':'Tokenizer.from_file(original).to_str() plus newline','tokenizers_version':tokenizers.__version__,'purpose':'Explicit modern model/type fields for JS compatibility; all original-vs-derived Python ID sequences must agree.'},'selection_reason':'Multilingual non-BPE profile selected before workload counts. Encoder tokenizer; not an algorithm-isolated or chat-model comparison.','licence_note':'Pinned model card labels MIT; downloaded assets stay ignored, not redistributed.'}
    out=ROOT/'config/xlm-roberta-base-tokenizer.lock.json'
    if out.exists(): assert json.loads(out.read_text())==d,'Existing lock differs'
    else: out.write_text(json.dumps(d,indent=2)+'\n')
    print(json.dumps({'revision':revision,'algorithm':d['runtime_model_type'],'base_vocab_entries':d['base_vocab_entries'],'original_files_verified':len(assets),'derived_sha256':sha(canonical)},indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--revision',required=True);main(p.parse_args().revision)
