"""Descriptive statistics and graphs for the frozen original text-type experiment."""
import argparse,hashlib,json,math,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.cache/matplotlib'))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ratio_stats(a,b):
    ratios=np.array([x['token_count']/y['token_count'] for x,y in zip(a,b,strict=True)])
    clean=[x['token_count']/y['token_count'] for x,y in zip(a,b,strict=True) if x['unknown_tokens']==0 and y['unknown_tokens']==0]
    q=np.quantile(ratios,[.1,.5,.9],method='linear')
    return {'n':len(ratios),'geometric_mean':float(np.exp(np.mean(np.log(ratios)))),'median':float(q[1]),'p10':float(q[0]),'p90':float(q[2]),'min':float(min(ratios)),'max':float(max(ratios)),'unknown_free_n':len(clean),'unknown_free_geometric_mean':float(np.exp(np.mean(np.log(clean)))) if clean else None}
def savefig(fig,out,name):
    for ext in ['png','svg','pdf']:
        p=out/f'{name}.{ext}';fig.savefig(p,dpi=180,facecolor='white')
        if ext=='svg':p.write_text('\n'.join(s.rstrip() for s in p.read_text().splitlines())+'\n')
    plt.close(fig)
def heat(ax,values,title,xlabels,ylabels,norm,cmap='RdBu_r',percent=False):
    data=values if percent else np.log2(values)
    im=ax.imshow(data,aspect='auto',norm=norm,cmap=cmap)
    ax.set_title(title,pad=12);ax.set_xticks(range(len(xlabels)),xlabels,rotation=30,ha='right');ax.set_yticks(range(len(ylabels)),ylabels)
    for i in range(len(ylabels)):
        for j in range(len(xlabels)):
            value=values[i,j];color='white' if (value>65 if percent else abs(data[i,j])>.65*max(abs(norm.vmin),abs(norm.vmax))) else '#111111'
            ax.text(j,i,f'{value:.0f}' if percent else f'{value:.2f}',ha='center',va='center',fontsize=10,color=color)
    return im

def main(source,out):
    planpath=ROOT/'config/text-types-v1.json';plan=json.loads(planpath.read_text());rows=json.loads((source/'measurements.json').read_text());primary=[r for r in rows if r['role']=='primary'];assert len(primary)==1080
    models=plan['models'];labels=plan['labels'];conditions=plan['conditions'];formats=plan['formats'];scenarios=[f's{i:02d}' for i in range(1,13)]
    lookup={(r['model_key'],r['condition'],r['format'],r['scenario']):r for r in primary};assert len(lookup)==1080
    get=lambda m,c,f:[lookup[m,c,f,s] for s in scenarios]
    cells=[];pairs=[];format_ratios=[];pretty=[]
    for m in models:
        for c in conditions:
            for f in formats:
                rr=get(m,c,f);counts=[r['token_count'] for r in rr];q=np.quantile(counts,[.1,.5,.9],method='linear')
                cells.append({'model_key':m,'condition':c,'format':f,'n':12,'median_count':float(q[1]),'p10_count':float(q[0]),'p90_count':float(q[2]),'median_tokens_per_100_codepoints':float(np.median([100*r['token_count']/r['characters'] for r in rr])),'unknown_input_rate':sum(r['unknown_tokens']>0 for r in rr)/12,'normalization_change_rate':sum(r['normalization_changed'] for r in rr)/12,'decode_mismatch_rate':sum(not r['decode_exact'] for r in rr)/12})
                format_ratios.append({'model_key':m,'condition':c,'numerator_format':f,'denominator_format':'prose',**ratio_stats(rr,get(m,c,'prose'))})
            pretty.append({'model_key':m,'condition':c,**ratio_stats(get(m,c,'json_pretty'),get(m,c,'json_compact'))})
    for a in models:
        for b in models:
            for c in conditions:
                for f in formats:pairs.append({'numerator':a,'denominator':b,'condition':c,'format':f,**ratio_stats(get(a,c,f),get(b,c,f))})
    out.mkdir(parents=True,exist_ok=False)
    result={'cells':cells,'tokenizer_ratios':pairs,'format_to_prose_ratios':format_ratios,'pretty_to_compact_json_ratios':pretty}
    (out/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'svg.fonttype':'none'})
    fmtlabels=['Prose','Python literal','Compact JSON','Pretty JSON','HTML'];condlabels=['English','English + Hindi','English + Tamil']
    def panels(matrices,name,title,footnote,percent=False):
        extent=max(float(np.max(np.abs(np.log2(v)))) for v in matrices) if not percent else 100
        norm=plt.Normalize(0,100) if percent else TwoSlopeNorm(vmin=-max(extent,.01),vcenter=0,vmax=max(extent,.01))
        fig,axes=plt.subplots(1,3,figsize=(18,7));fig.subplots_adjust(left=.10,right=.91,bottom=.29,top=.80,wspace=.47)
        for ax,values,label in zip(axes,matrices,condlabels):im=heat(ax,values,label,fmtlabels,labels,norm,'YlOrRd' if percent else 'RdBu_r',percent)
        cax=fig.add_axes([.94,.32,.012,.45]);bar=fig.colorbar(im,cax=cax)
        if percent:bar.set_label('Inputs with decode mismatch (%)')
        else:
            ticks=list(range(math.ceil(-extent),math.floor(extent)+1));bar.set_ticks(ticks,labels=[f'{2**x:g}×' for x in ticks]);bar.set_label('Count ratio; logarithmic color scale')
        fig.suptitle(title,fontsize=20,y=.96)
        fig.text(.10,.17,footnote,fontsize=11)
        fig.text(.10,.105,'12 authored scenario blocks per cell; 180 primary inputs total. Shared templates, not a natural-workload sample.',fontsize=10)
        fig.text(.10,.055,'XLM-R is one Unigram profile; the other five are BPE. No causal algorithm ranking. MiniCPM uses HF JSON.',fontsize=10)
        savefig(fig,out,name)
    ref=plan['reference_tokenizer'];pmap={(r['numerator'],r['denominator'],r['condition'],r['format']):r for r in pairs}
    matrices=[np.array([[pmap[m,ref,c,f]['geometric_mean'] for f in formats] for m in models]) for c in conditions]
    panels(matrices,'01-count-ratios','Same input: token counts relative to Qwen','Geometric mean of paired count ratios. 1 = equal; 2 = twice as many. No unknown tokens occurred in primary inputs.')
    fmap={(r['model_key'],r['condition'],r['numerator_format']):r for r in format_ratios}
    mats=[np.array([[fmap[m,c,f]['geometric_mean'] for f in formats] for m in models]) for c in conditions]
    pm={(r['model_key'],r['condition']):r for r in pretty};mats.append(np.array([[pm[m,c]['geometric_mean'] for c in conditions] for m in models]))
    extent=max(float(np.max(np.abs(np.log2(v)))) for v in mats);norm=TwoSlopeNorm(vmin=-extent,vcenter=0,vmax=extent)
    fig,axes=plt.subplots(2,2,figsize=(14,11));fig.subplots_adjust(left=.16,right=.87,bottom=.20,top=.88,wspace=.5,hspace=.65)
    for i,(ax,values) in enumerate(zip(axes.flat,mats)):
        im=heat(ax,values,condlabels[i]+' — format ÷ prose' if i<3 else 'Pretty JSON ÷ compact JSON',fmtlabels if i<3 else condlabels,labels,norm)
    cax=fig.add_axes([.92,.30,.015,.50]);bar=fig.colorbar(im,cax=cax);ticks=list(range(math.ceil(-extent),math.floor(extent)+1));bar.set_ticks(ticks,labels=[f'{2**x:g}×' for x in ticks]);bar.set_label('Count ratio; logarithmic color scale')
    fig.suptitle('Rendering the same record changes its token count',fontsize=19,y=.97)
    fig.text(.10,.12,'Geometric means, 12 paired records per cell. Prose = 1 in the first three panels; last panel uses compact JSON = 1.',fontsize=10)
    fig.text(.10,.075,'Only pretty/compact JSON isolates whitespace formatting here. Other renderers also change scaffolding and text length.',fontsize=10)
    fig.text(.10,.035,'Original templated fixtures; no browser timing or model-quality test. Low counts can coincide with whitespace normalization.',fontsize=10)
    savefig(fig,out,'02-format-ratios')
    cmap={(r['model_key'],r['condition'],r['format']):r for r in cells}
    matrices=[np.array([[100*cmap[m,c,f]['decode_mismatch_rate'] for f in formats] for m in models]) for c in conditions]
    panels(matrices,'03-reconstruction','Does decoding reproduce the original text exactly?','100 = all 12 inputs changed; 0 = all matched exactly. Whitespace/normalization changes are not automatically semantic loss.',True)
    lines=['# Text types and a Unigram tokenizer: results','', 'Controlled synthetic pilot, 2026-10-18. These results use original project fixtures, not FLORES+.', '',
           '## What we measured','', 'Twelve records × three content conditions × five renderers = 180 primary inputs.',
           'Six tokenizer profiles give 1,080 primary measurements. Eight separate probes add 48 diagnostic measurements.',
           'The same source record is rendered in each format; English structural labels remain in the mixed-language versions.',
           'All examples are authored templates, not sampled natural documents or independently validated translations.', '',
           '## Same text, different tokenizer','', '![Counts relative to Qwen](01-count-ratios.png)','',
           'Each cell is the geometric mean of 12 same-input count ratios. Qwen is a fixed reference, not a quality standard.',
           'All 540 ordered-pair/cell summaries, including self-comparisons, are retained in summary.json.',
           'There were no unknown-token inputs in the primary workload. The unknown-free summaries therefore match it.', '',
           '## Formatting changes counts','', '![Format ratios](02-format-ratios.png)','',
           'Pretty JSON and compact JSON encode identical records; their only text difference is serialization whitespace.',
           'Other comparisons also change scaffolding and length, so they do not isolate a general format effect.', '',
           '| Profile | English pretty/compact | English + Hindi | English + Tamil |', '| --- | ---: | ---: | ---: |']
    for m,label in zip(models,labels):lines.append('| '+label+' | '+' | '.join(f"{pm[m,c]['geometric_mean']:.3f}×" for c in conditions)+' |')
    lines+=['','Ratios are geometric means of 12 per-record ratios, not ratios of total tokens.','',
            '## Exact reconstruction and unknown symbols','', '![Reconstruction](03-reconstruction.png)','',
            'XLM-R changes decoded whitespace in all primary prose, Python-literal, pretty-JSON and HTML inputs.',
            'Compact JSON reconstructs exactly in this fixture set. This is exact-string behavior, not a verdict on meaning.',
            'Its separate emoji/rare-character probes contain unknown IDs; those probes never enter the primary summaries.',
            'The BPE profiles also have normalization differences on some accent probes. Inspect all probe rows rather than assuming universal losslessness.', '',
            'Example from the original indentation probe:', '', '```python', 'def ready():', '    return True', '```','',
            'XLM-R decodes it as `def ready(): return True`. This example shows changed layout; it does not by itself show changed program behavior.', '',
            '## Scope and evidence','',
            '- [All summary cells](summary.json): 90 count/coverage cells, 540 tokenizer ratios, 90 format/prose ratios and 18 pretty/compact ratios.',
            '- [Measurements](../run-01/measurements.json), [token examples](../run-01/token-examples.json) and [profile inventory](../run-01/inventory.json).',
            '- [Original public fixtures](../../../data/fixtures/text-types-v1.json), [frozen plan](../../../config/text-types-v1.json) and [protocol](../../../docs/TEXT_TYPES_V1.md).',
            '- Six profiles: five BPE and one Unigram. Vocabulary, training data, normalization and model purpose differ together.',
            '- XLM-R comes from an encoder model; this is not a chat-model comparison or an isolated algorithm experiment.',
            '- Token counts were measured without truncation or special tokens. Full chat prompts, speed, memory and answer quality were not measured.',
            '- No fitting, model inference, FLORES access or paid service calls.', '',
            '## Reproduction','', 'Use the pinned Python environment and existing cached assets. Pin/acquire the additional profile with:', '',
            '```sh','.venv/bin/python scripts/pin_unigram.py --revision e73636d4f797dec63c3081bb6ed5c7b0bb3f2089',
            '.venv/bin/python scripts/build_text_type_fixtures.py',
            '.venv/bin/python scripts/measure_text_types.py --output results/reproduction-text-types/run-01',
            'node scripts/check_text_types_js.mjs results/reproduction-text-types/js-01',
            '.venv/bin/python scripts/analyze_text_types.py --source results/reproduction-text-types/run-01 --output results/reproduction-text-types/analysis-01',
            '```','', 'The measurement command resumes verified per-profile shards; analysis needs a fresh directory.',
            'Runtime-serialized Unigram JSON is retained locally as a documented compatibility check. JS successfully used the original legacy JSON.',
            'Original-versus-serialized Python ID parity covers all 188 inputs; no source asset bytes were edited.', '']
    (out/'REPORT.md').write_text('\n'.join(lines))
    (out/'analysis-manifest.json').write_text(json.dumps({'plan_sha256':sha(planpath),'measurements_sha256':sha(source/'measurements.json'),'script_sha256':sha(Path(__file__)),'numpy_version':np.__version__,'matplotlib_version':matplotlib.__version__,'summary_groups':738,'visual_review':'pending'},indent=2)+'\n')
    print('Generated 738 summary groups and three figures.')
    print('Pretty/compact ratios:',json.dumps({label:{c:round(pm[m,c]['geometric_mean'],3) for c in conditions} for m,label in zip(models,labels)},indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--output',required=True);a=p.parse_args();source=(ROOT/a.source).resolve();out=(ROOT/a.output).resolve();assert source.is_relative_to(ROOT/'results') and out.is_relative_to(ROOT/'results');main(source,out)
