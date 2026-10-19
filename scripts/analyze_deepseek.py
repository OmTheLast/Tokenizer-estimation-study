"""Predeclared descriptive summaries/plots, with source-stratum separation."""
import argparse
import json
import math
import os
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR', str(Path(__file__).resolve().parents[1]/'.cache/matplotlib'))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MaxNLocator, NullLocator
from prepare_published_inputs import ROOT, sha


def stats(values):
    q = np.quantile(values, [.1,.5,.9], method='linear')
    return {'median':float(q[1]), 'p10':float(q[0]), 'p90':float(q[2])}


def ratios(a, b):
    assert [x['id'] for x in a] == [x['id'] for x in b]
    values = [x['token_count']/y['token_count'] for x,y in zip(a,b,strict=True)]
    clean = [v for v,x,y in zip(values,a,b,strict=True) if not x['unknown_tokens'] and not y['unknown_tokens']]
    gm = lambda vs: float(np.exp(np.mean(np.log(vs)))) if vs else None
    return {'n':len(values), 'geometric_mean':gm(values), **stats(values),
            'min':min(values), 'max':max(values), 'unknown_free_n':len(clean),
            'unknown_free_geometric_mean':gm(clean)}


def savefig(fig, out, name):
    for ext in ('png','svg','pdf'):
        path=out/(name+'.'+ext); fig.savefig(path,dpi=170,facecolor='white')
        if ext=='svg': path.write_text('\n'.join(l.rstrip() for l in path.read_text().splitlines())+'\n')
    plt.close(fig)


def main(base, out):
    plan=json.loads((ROOT/'config/deepseek-extension-v1.json').read_text())
    inputs=json.loads((ROOT/plan['input_manifest']).read_text())['inputs']
    rows=json.loads((base/'run-01/measurements.json').read_text())
    table={(r['model_key'],r['id']):r for r in rows}
    assert len(table)==len(rows)==1120
    models,labels=plan['models'],plan['labels']; ref=plan['reference_tokenizer']
    originals=[f for f in inputs if f['role']=='original']
    cats=['prose','code','json','html','mixed']
    titles=['English documentation','Code','JSON','HTML','Mixed-script documentation']
    groups=[]
    def add(scope,key,rr):
        if rr: groups.append({'scope':scope,'key':key,'input_ids':sorted(r['id'] for r in rr)})
    for cat in cats:
        rr=[f for f in originals if f['category']==cat];add('category',cat,rr)
        for lo,hi in plan['length_bands']:
            add('category_length',f'{cat}/{lo}-{hi}',[r for r in rr if lo<=r['characters']<=hi])
    for s in sorted({r['stratum'] for r in originals}):add('stratum',s,[r for r in originals if r['stratum']==s])
    jsonstrata=sorted({r['stratum'] for r in originals if r['category']=='json'})
    for form in ('json_compact','json_pretty'):
        for s in ['all']+jsonstrata:add('json_variant',form+'/'+s,[r for r in inputs if r['format']==form and (s=='all' or r['stratum']==s)])
    get=lambda m,g:[table[m,i] for i in g['input_ids']]
    cells,pairs,format_pairs,per_input,per_json=[],[],[],[],[]
    for g in groups:
        for m in models:
            rr=get(m,g);n=len(rr);counts=[r['token_count'] for r in rr]
            cells.append({'model_key':m,'scope':g['scope'],'key':g['key'],'n':n,
                **{k+'_count':v for k,v in stats(counts).items()},
                'median_tokens_per_100_codepoints':float(np.median([100*r['token_count']/r['characters'] for r in rr])),
                'unknown_inputs':sum(r['unknown_tokens']>0 for r in rr),
                'unknown_input_rate':sum(r['unknown_tokens']>0 for r in rr)/n,
                'normalization_changed_inputs':sum(r['normalization_changed'] for r in rr),
                'normalization_change_rate':sum(r['normalization_changed'] for r in rr)/n,
                'decode_mismatches':sum(not r['decode_exact'] for r in rr),
                'decode_mismatch_rate':sum(not r['decode_exact'] for r in rr)/n})
        if g['scope']!='json_variant':
            for a in models:
                for b in models:pairs.append({'numerator':a,'denominator':b,'scope':g['scope'],'key':g['key'],**ratios(get(a,g),get(b,g))})
    for f in originals:
        for a in models:
            for b in models:
                x,y=table[a,f['id']],table[b,f['id']]
                per_input.append({'input_id':f['id'],'category':f['category'],'stratum':f['stratum'],
                    'numerator':a,'denominator':b,'ratio':x['token_count']/y['token_count'],
                    'unknown_free':not x['unknown_tokens'] and not y['unknown_tokens']})
    for m in models:
        for s in ['all']+jsonstrata:
            ids=sorted(f['sample_id'] for f in originals if f['category']=='json' and (s=='all' or f['stratum']==s))
            # Align paired variants by underlying sample ID, not their different format IDs.
            a=[{**table[m,i+'/json_pretty'],'id':i} for i in ids]
            b=[{**table[m,i+'/json_compact'],'id':i} for i in ids]
            format_pairs.append({'model_key':m,'stratum':s,**ratios(a,b)})
        for f in [x for x in originals if x['category']=='json']:
            a,b=table[m,f['sample_id']+'/json_pretty'],table[m,f['sample_id']+'/json_compact']
            per_json.append({'model_key':m,'sample_id':f['sample_id'],'stratum':f['stratum'],
                             'ratio':a['token_count']/b['token_count'],
                             'unknown_free':not a['unknown_tokens'] and not b['unknown_tokens']})
    out.mkdir(parents=True,exist_ok=False)
    save=lambda name,obj:(out/name).write_text(json.dumps(obj,indent=2)+'\n')
    save('summary.json',{'groups':groups,'cells':cells,'tokenizer_ratios':pairs,'pretty_compact_ratios':format_pairs})
    save('per-input-ratios.json',per_input); save('per-json-ratios.json',per_json)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'svg.fonttype':'none'})
    fig,axes=plt.subplots(3,2,figsize=(16,13));fig.subplots_adjust(top=.9,bottom=.11,hspace=.65,wspace=.30)
    short={'english_cpython':'CPython','english_node':'Node.js','python':'Python','javascript':'JavaScript',
           'npm_package':'npm','vscode_extension':'VS Code','mdn_dom':'MDN DOM','mdn_learning':'MDN learning',
           'hindi_english':'Hindi–English','tamil_english':'Tamil–English'}
    for ax,cat,title in zip(axes.flat,cats,titles):
        strata=sorted({r['stratum'] for r in originals if r['category']==cat})
        for k,s in enumerate(strata):
            for j,m in enumerate(models[1:]):
                rr=[r for r in per_input if r['category']==cat and r['stratum']==s and r['numerator']==m and r['denominator']==ref]
                jitter=np.linspace(-.12,.12,len(rr))+(k-.5)*.20
                ax.scatter(j+jitter,[r['ratio'] for r in rr],s=23,color=['#2876A8','#DB8430'][k],alpha=.75,label=short[s] if j==0 else None)
        ax.axhline(1,color='#555',linewidth=.8);ax.set_yscale('log',base=2)
        lo,hi=ax.get_ylim()
        ticks=([.25,.5,1,2,4,8] if hi/lo>3 else MaxNLocator(nbins=4).tick_values(lo,hi))
        ax.set_yticks([v for v in ticks if lo<=v<=hi])
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v,pos:f'{v:.2g}×'))
        ax.yaxis.set_minor_locator(NullLocator())
        ax.set_xticks(range(len(models)-1),labels[1:],rotation=30,ha='right');ax.set_title(title+' (20 texts)')
        ax.set_ylabel('Token count ÷ Qwen count');ax.grid(axis='y',alpha=.2)
        ax.legend(fontsize=8,loc='best')
    axes.flat[-1].axis('off')
    axes.flat[-1].text(.02,.9,'Each dot compares the SAME input.\n1 = equal counts; 2 = twice as many.\nColors show source or language.\nQwen is the reference, not a quality standard.\n\nPanels use logarithmic axes with different ranges.\nSeven BPE profiles + one Unigram profile;\nDeepSeek V3/R1 share their BPE core.\nThis does not isolate an algorithm effect.',va='top',linespacing=1.8)
    fig.suptitle('Relative token counts vary across our text groups',fontsize=18)
    fig.text(.07,.025,'100 published technical inputs; shared projects/templates, automatic translations. MiniCPM*: HF JSON, not verified GGUF parity.',fontsize=10)
    savefig(fig,out,'01-count-ratios')
    fig,ax=plt.subplots(figsize=(13,6));fig.subplots_adjust(bottom=.25,top=.84)
    for k,s in enumerate(jsonstrata):
        for j,m in enumerate(models):
            rr=[r for r in per_json if r['stratum']==s and r['model_key']==m]
            ax.scatter(j+np.linspace(-.1,.1,len(rr))+(k-.5)*.22,[r['ratio'] for r in rr],color=['#2876A8','#DB8430'][k],s=32,alpha=.8,label=short[s] if j==0 else None)
    ax.axhline(1,color='#555',linewidth=.8);ax.set_xticks(range(len(models)),labels,rotation=25,ha='right')
    ax.set_ylabel('Pretty JSON tokens ÷ compact JSON tokens');ax.grid(axis='y',alpha=.2);ax.legend()
    fig.suptitle('Same JSON data: what does indentation cost?',fontsize=17)
    fig.text(.08,.05,'20 files per profile. Identical values/order/scalar spelling; only serialization whitespace differs. Variants are paired inputs.',fontsize=10)
    savefig(fig,out,'02-json-formatting')
    lookup={(r['model_key'],r['scope'],r['key']):r for r in cells}
    fig,axes=plt.subplots(1,2,figsize=(15,7));fig.subplots_adjust(left=.15,right=.97,bottom=.27,top=.8,wspace=.4)
    for ax,field,title in zip(axes,['decode_mismatches','unknown_inputs'],['Original not reconstructed exactly','Inputs containing unknown IDs']):
        values=np.array([[lookup[m,'category',cat][field] for cat in cats] for m in models])
        ax.imshow(values,vmin=0,vmax=20,cmap='YlOrRd',aspect='auto');ax.set_title(title)
        ax.set_xticks(range(5),['Prose','Code','JSON','HTML','Mixed'],rotation=25,ha='right');ax.set_yticks(range(len(models)),labels)
        for i in range(len(models)):
            for j in range(5):ax.text(j,i,f'{values[i,j]}/20',ha='center',va='center',color='white' if values[i,j]>12 else 'black')
    fig.suptitle('Fewer tokens do not guarantee exact text preservation',fontsize=18)
    fig.text(.08,.13,'Each cell shows affected inputs out of 20. Exact-string differences can be whitespace-only; this is not a meaning test.',fontsize=11)
    fig.text(.08,.06,'Original samples only. JSON variants and separate source/language summaries are retained in the numeric evidence.',fontsize=10)
    savefig(fig,out,'03-reconstruction')
    save('analysis-manifest.json',{'script_sha256':sha(Path(__file__)),'measurements_sha256':sha(base/'run-01/measurements.json'),
        'groups':len(groups),'summary_cells':len(cells),'pair_summaries':len(pairs),'json_pair_summaries':len(format_pairs),
        'numpy_version':np.__version__,'matplotlib_version':matplotlib.__version__,'visual_review':'pending'})
    print(json.dumps({'cells':len(cells),'ratios':len(pairs),'json_pairs':format_pairs},indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--base',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();main(a.base,a.output)
