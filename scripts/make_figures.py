import hashlib
import json
import os
from pathlib import Path
os.environ['MPLBACKEND']='Agg'
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'figures'; OUT.mkdir(exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'svg.fonttype':'none'})
models=pd.read_csv(ROOT/'results/all-model-metrics.csv')
primary=models.loc[models['mode'].eq('primary')].copy()
labels={'structural_median':'Structural median','descriptor_local_svd':'Descriptor-local SVD','pca_matched_dimension':'PCA (matched dimension)',
        'all_visible_ridge':'All-visible ridge','family_median':'Family median','degree_preserving_null':'Degree-preserving null',
        'population_mean':'Training mean','direct_neighbor_ridge':'Reaction neighbors','correlation_selected_ridge':'Correlation-selected markers',
        'global_pca_ridge':'PCA (matched dimension)','all_other_metabolites_ridge':'All-metabolite ridge',
        'network_additive_ridge':'Network + expression','network_interaction_ridge':'Network + interactions'}
colors={m:'#88939e' for m in labels}
colors.update(structural_median='#2a78d6',direct_neighbor_ridge='#2a78d6',descriptor_local_svd='#eb6834',pca_matched_dimension='#eb6834',global_pca_ridge='#eb6834',correlation_selected_ridge='#eb6834',all_visible_ridge='#52514e',all_other_metabolites_ridge='#52514e')  # validated pair: biochemical blue, compact-statistical orange
fig,axes=plt.subplots(3,1,figsize=(8.5,9.2),layout='constrained')
for ax,dataset,title in zip(axes,['st002081','st000818','ccle'],['a  ST002081 · 112 participants','b  ST000818 · 15 population groups','c  CCLE · 60 targets, 18 lineages']):
    frame=primary.loc[primary.dataset.eq(dataset)].sort_values('primary_rmse')
    y=np.arange(len(frame))
    ax.barh(y,frame.primary_rmse,color=[colors[m] for m in frame.model],height=.65)
    ax.set_yticks(y,[labels[m] for m in frame.model]); ax.invert_yaxis()
    ax.set_title(title,loc='left',fontweight='bold',fontsize=11)
    ax.set_xlabel('Held-out RMSE (training-SD units; lower is better)')
    ax.xaxis.grid(True,alpha=.18); ax.set_axisbelow(True)
    ax.set_xlim(0,frame.primary_rmse.max()*1.13)
    for i,value in enumerate(frame.primary_rmse): ax.text(value+frame.primary_rmse.max()*.015,i,f'{value:.3f}',va='center',fontsize=9)
for suffix in ['png','pdf','svg']: fig.savefig(OUT/f'figure1-performance.{suffix}',dpi=220)
plt.close(fig)
primary.to_csv(OUT/'figure1-source.csv',index=False)

contrasts=pd.read_csv(ROOT/'results/primary-comparisons.csv')
fig,ax=plt.subplots(figsize=(8.5,4.6),layout='constrained')
yl=[]
for i,row in contrasts.iterrows():
    y=4-i
    label=f'{row.dataset.upper()} vs '+({'pca_matched_dimension':'PCA','descriptor_local_svd':'local SVD','correlation_selected_ridge':'selected markers'}[row.reference])
    yl.append(label)
    ax.plot([row.simultaneous99_lower,row.simultaneous99_upper],[y,y],color='#64717b',lw=1.5)
    ax.plot([row.ci95_lower,row.ci95_upper],[y,y],color='#eb6834',lw=5,solid_capstyle='butt')
    ax.plot(row.improvement,y,'o',color='#eb6834',ms=6)
ax.axvline(0,color='#404040',lw=1,linestyle='--')
ax.set_yticks(range(4,-1,-1),yl)
ax.set_xlabel('Reference RMSE − mechanism RMSE (training-SD units)')
ax.set_ylim(-.7,4.8); ax.set_xlim(-.85,.05)
ax.set_title('All five primary contrasts favor the statistical reference',loc='left',fontsize=12,fontweight='bold')
ax.text(-.83,-.57,'← Reference lower error',fontsize=9)
ax.xaxis.grid(True,alpha=.18)
for suffix in ['png','pdf','svg']: fig.savefig(OUT/f'figure2-comparisons.{suffix}',dpi=220)
plt.close(fig)
contrasts.to_csv(OUT/'figure2-source.csv',index=False)
manifest={'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.iterdir() if p.is_file() and p.name!='manifest.json'}}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
