"""Scientific figures from frozen numeric pilot outputs; no new experiments."""
import argparse
import hashlib
import json
import os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.cache/matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import pyarrow.parquet as pq

DIAGNOSTICS=ROOT/'results/2026-10-15-pilot-diagnostics/run-02/diagnostics.json'
MEASUREMENTS=ROOT/'results/2026-10-15-phase1-pilot/run-02/ground-truth.parquet'
ORDER=['qwen35-4b','bonsai-ternary-4b','lfm2-1.2b','gemma4-e2b','minicpm5-2b-gguf']
LABELS=['Qwen','Bonsai','LFM','Gemma','MiniCPM*']
COLORS={'Indian':'#007f86','CJK':'#c85a17','Other':'#7472a6'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def savefig(fig,out,name):
    for ext in ['png','svg','pdf']:
        fig.savefig(out/(name+'.'+ext),dpi=180,facecolor='white')
    plt.close(fig)
def main(out):
    plan=json.loads((ROOT/'config/pilot-diagnostics-v1.json').read_text())
    assert sha(MEASUREMENTS)==plan['input_sha256']
    diagnostics=json.loads(DIAGNOSTICS.read_text());rows=pq.read_table(MEASUREMENTS).to_pylist()
    modelstats={c['model_key']:c for c in diagnostics['tokenizers']}
    cells={(c['model_key'],c['language']):c for c in diagnostics['cells']}
    langs=[l['code'] for l in json.loads((ROOT/'config/phase1-pilot.json').read_text())['languages']]
    langlabels=[l['label'].replace('Chinese (Simplified)','Chinese\n(simplified)').replace('Chinese (Traditional)','Chinese\n(traditional)') for l in json.loads((ROOT/'config/phase1-pilot.json').read_text())['languages']]
    assert len(rows)==9000 and len(cells)==90
    data={'summary':{},'undercount_matrices':{},'scatter':{}}
    for model in ORDER:
        rr=[r for r in rows if r['model_key']==model];assert len(rr)==1800
        data['summary'][model]={}
        for method,field in [('localmind','estimate'),('legacy_utf16_div_3_5','old_estimate')]:
            abs_errors=np.array([100*abs(r[field]-r['token_count'])/r['token_count'] for r in rr])
            vals={'median_absolute_percent_error':float(np.median(abs_errors)),'p95_absolute_percent_error':float(np.quantile(abs_errors,.95,method='linear'))}
            for k,v in vals.items():assert np.isclose(v,modelstats[model]['estimators'][method][k])
            data['summary'][model][method]=vals
        data['scatter'][model]={g:[[r['token_count'],r['estimate']] for r in rr if r['group']==g] for g in COLORS}
    for method,field in [('localmind','estimate'),('legacy_utf16_div_3_5','old_estimate')]:
        matrix=[]
        for model in ORDER:
            values=[]
            for lang in langs:
                rr=[r for r in rows if r['model_key']==model and r['language']==lang];assert len(rr)==100
                rate=100*sum(5*r[field]<4*r['token_count'] for r in rr)/len(rr)
                assert np.isclose(rate,100*cells[model,lang]['estimators'][method]['under_by_more_than_20_percent_fraction'])
                values.append(rate)
            matrix.append(values)
        data['undercount_matrices'][method]=matrix
    out.mkdir(parents=True,exist_ok=False)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none'})
    fig,axes=plt.subplots(1,2,figsize=(13,5.8));fig.subplots_adjust(left=.10,right=.98,bottom=.19,top=.76,wspace=.31)
    for ax,metric,title in zip(axes,['median_absolute_percent_error','p95_absolute_percent_error'],['Typical error (median)','Large-error level (95th percentile)']):
        for method,offset,color,label in [('legacy_utf16_div_3_5',-.18,'#9bafc2','Old rule: UTF-16 units / 3.5'),('localmind',.18,'#007f86','LocalMind: script + tokenizer weights')]:
            values=[data['summary'][m][method][metric] for m in ORDER];y=np.arange(5)+offset
            ax.barh(y,values,height=.32,color=color,label=label)
            for yy,value in zip(y,values):ax.text(value+1,yy,f'{value:.1f}%',va='center',fontsize=10)
        ax.set(yticks=range(5),yticklabels=LABELS,xlim=(0,103),xlabel='Absolute prediction error (%)',title=title)
        ax.invert_yaxis();ax.grid(axis='x',alpha=.18);ax.set_axisbelow(True)
    fig.suptitle('Two estimation methods on the same texts',fontsize=19,y=.97)
    handles,labels=axes[0].get_legend_handles_labels();fig.legend(handles,labels,loc='upper center',bbox_to_anchor=(.5,.90),ncol=2,frameon=False)
    fig.text(.10,.10,'1,800 texts per tokenizer • 18 language varieties • FLORES+ dev pilot',fontsize=10)
    fig.text(.10,.055,'Smaller is better. Absolute error combines under- and overestimation; the 95th percentile is not a maximum.',fontsize=10)
    fig.text(.10,.015,'*MiniCPM: HF JSON tokenizer. Neither fitting nor a browser benchmark. Same 100 aligned sentence IDs across languages.',fontsize=9)
    savefig(fig,out,'01-error-comparison')
    fig,axes=plt.subplots(2,1,figsize=(18,9.2));fig.subplots_adjust(left=.08,right=.91,top=.88,bottom=.22,hspace=.32)
    im=None
    for ax,method,title in zip(axes,['legacy_utf16_div_3_5','localmind'],['Old rule: UTF-16 units / 3.5','LocalMind: script + tokenizer weights']):
        matrix=np.array(data['undercount_matrices'][method]);im=ax.imshow(matrix,aspect='auto',vmin=0,vmax=100,cmap='YlOrRd')
        ax.set(yticks=range(5),yticklabels=LABELS,xticks=range(18),title=title)
        ax.set_xticklabels(langlabels,rotation=45,ha='right',fontsize=10)
        if ax is axes[0]:ax.set_xticklabels([])
        for i in range(5):
            for j in range(18):ax.text(j,i,f'{matrix[i,j]:.0f}',ha='center',va='center',fontsize=10,color='white' if matrix[i,j]>=65 else '#161616')
    cax=fig.add_axes([.93,.26,.015,.58]);fig.colorbar(im,cax=cax,label='Samples undercounted by more than 20% (%)')
    fig.suptitle('Where does each method seriously undercount?',fontsize=20,y=.965)
    fig.text(.08,.105,'Each cell contains 100 texts: a value of 99 means 99 out of 100 had predicted count less than 80% of actual count.',fontsize=11)
    fig.text(.08,.06,'Same color scale for both methods. Darker = more frequent undercounts. The 20% cutoff is descriptive, not a safety guarantee.',fontsize=10)
    fig.text(.08,.025,'FLORES+ dev pilot • Related translations, not 9,000 independent examples • *MiniCPM uses its HF JSON tokenizer.',fontsize=10)
    savefig(fig,out,'02-undercount-by-language')
    fig,axes=plt.subplots(2,3,figsize=(15,9));fig.subplots_adjust(left=.065,right=.98,top=.88,bottom=.13,wspace=.32,hspace=.38)
    for ax,model,label in zip(axes.flat,ORDER,LABELS):
        allpoints=[p for pairs in data['scatter'][model].values() for p in pairs];limit=max(max(p) for p in allpoints)*1.04
        for group,color in COLORS.items():
            points=np.array(data['scatter'][model][group]);ax.scatter(points[:,0],points[:,1],s=9,color=color,alpha=.35,edgecolors='none',rasterized=True)
        ax.plot([0,limit],[0,limit],color='#343434',ls='--',lw=1.2)
        ax.set(xlim=(0,limit),ylim=(0,limit),xlabel='Actual content tokens',ylabel='Predicted tokens',title=label);ax.set_aspect('equal',adjustable='box');ax.grid(alpha=.15)
    last=axes.flat[-1];last.axis('off');handles=[Line2D([0],[0],marker='o',ls='',color=color,label=group) for group,color in COLORS.items()]
    last.legend(handles=handles,loc='upper left',frameon=False,title='Language groups')
    last.text(0,.45,'One dot = one measured text.\nOn dashed line = exact prediction.\nBelow line = underestimated.\nAbove line = overestimated.\n\nAxes differ between tokenizers.\nDots overlap; use tables for exact counts.',transform=last.transAxes,fontsize=12,va='top',linespacing=1.5)
    fig.suptitle('LocalMind predictions versus actual tokenizer counts',fontsize=19,y=.965)
    fig.text(.065,.055,'All 1,800 texts per tokenizer are included. Color shows the existing language groups, not a cause of error.',fontsize=11)
    fig.text(.065,.02,'FLORES+ dev pilot • Content tokens only • No fitting or browser measurement • *MiniCPM: HF JSON tokenizer.',fontsize=10)
    savefig(fig,out,'03-predicted-versus-actual')
    (out/'plot-data.json').write_text(json.dumps({'model_order':ORDER,'language_order':langs,**data},indent=2)+'\n')
    validation={'inputs':{str(DIAGNOSTICS.relative_to(ROOT)):sha(DIAGNOSTICS),str(MEASUREMENTS.relative_to(ROOT)):sha(MEASUREMENTS)},'script_sha256':sha(Path(__file__)),'numpy_version':np.__version__,'matplotlib_version':matplotlib.__version__,'rows':9000,'summary_values_recomputed_and_checked':20,'heatmap_values_recomputed_and_checked':180,'scatter_points':sum(len(p) for m in data['scatter'].values() for p in m.values()),'no_new_data_or_fitting':True,'output_formats':['png','svg','pdf'],'visual_inspection':'pending'}
    (out/'validation.json').write_text(json.dumps(validation,indent=2)+'\n')
    print('Generated 3 figures in PNG/SVG/PDF; checked 20 summaries, 180 heatmap values and 9000 scatter points.')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);args=p.parse_args();out=(ROOT/args.output).resolve()
    if not out.is_relative_to(ROOT/'results'):p.error('Output must be inside results/')
    main(out)
