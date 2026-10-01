"""Locked adaptive human compact-comparator benchmark; workspace inputs only."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import re
import resource
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

for _key in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:
    os.environ[_key] = '1'
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.linear_model import Ridge
from genotype_gated_metabolism.analysis.pathway_scores import (
    eligible_lipid_families, disjoint_family_masks, structural_descriptor_incidence,
    degree_preserving_descriptor_null, lipid_family,
)
from genotype_gated_metabolism.datasets.mwtab import load_mwtab
from genotype_gated_metabolism.datasets.metabolomics_workbench import MetabolomicsWorkbenchClient
from genotype_gated_metabolism.pipelines.pathway_score_st000818_replication import _annotate_groups
from genotype_gated_metabolism.ml.validation import GroupedValidationSpec, repeated_balanced_group_splits

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT/'work/release'
FROZEN = ROOT/'inputs/central-package/reproducible-release'
ALPHAS = (0.1,1.,10.,100.)
MODELS = ('structural_median','descriptor_local_svd','pca_matched_dimension',
          'all_visible_ridge','family_median','degree_preserving_null','population_mean')

def sha(path):
    with Path(path).open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()

def preflight():
    records=json.loads((ROOT/'receipts/m0-input-recovery.json').read_text())['files']
    for r in records:
        if sha(r['copy']) != r['sha256']: raise RuntimeError('Input checksum mismatch: '+r['copy'])

def load_data(dataset, mode):
    if dataset == 'st002081':
        d=load_mwtab(WORK/'data/raw/st002081/ST002081_AN003790.txt')
        metadata=d.sample_metadata
        groups=metadata['additional_RandomID'].astype(str)
        keep=groups.ne('NA')
        matrix=d.blocks['metabolomics'].loc[groups.index[keep]]
        groups=groups.loc[matrix.index]
        archived=pd.read_csv(FROZEN/'artifacts/pathway-score-st002081/feature-families.csv')['feature']
        seeds={'mask':20260830,'outer':20260831,'null':20260840}
    else:
        client=MetabolomicsWorkbenchClient(cache_dir=WORK/'data/raw/public-intervention-registry/workbench-cache')
        factors=client.factors('ST000818')
        groups=_annotate_groups(factors,'Categorization').dropna()
        m=client.measurements('ST000818')
        m=m.loc[m['analysis_id'].eq('AN001299')]
        matrix=m.pivot_table(index='local_sample_id',columns='metabolite_name',values='value',aggfunc='mean')
        shared=matrix.index.astype(str).intersection(groups.index)
        matrix=matrix.loc[shared]; groups=groups.loc[shared].astype(str)
        archived=pd.read_csv(FROZEN/'artifacts/pathway-score-st000818-replication/eligible-features.csv')['feature']
        seeds={'mask':20261100,'outer':20261110,'null':20261200}
    features=matrix.columns if mode=='missingness' else pd.Index(archived)
    families=eligible_lipid_families(features,minimum_family_features=5)
    matrix=matrix.loc[:,families.index].astype(float)
    return matrix, groups, families, seeds

def resolution_incidence(features):
    original=structural_descriptor_incidence(features,minimum_features=5,maximum_feature_fraction=.9)
    resolved=original.copy()
    changes=[]
    for feature in features:
        family=lipid_family(str(feature))
        pairs=re.findall(r'\d+:\d+',str(feature))
        if family not in {'LPC','LPE','CE'} and len(pairs)==1 and 'FA' not in str(feature):
            columns=[c for c in resolved if c.startswith(('acyl:','chain_carbon:','chain_unsaturation:')) and resolved.loc[feature,c]]
            resolved.loc[feature,columns]=False
            changes.extend({'feature':feature,'removed_descriptor':c} for c in columns)
    counts=resolved.sum(axis=0)
    return resolved.loc[:,counts.ge(5)&counts.le(.9*len(resolved))],changes

def standardize(train,test):
    finite=np.isfinite(train)
    n=finite.sum(axis=0)
    mean=np.divide(np.where(finite,train,0).sum(axis=0),n,out=np.zeros(train.shape[1]),where=n>0)
    a=np.where(finite,train,mean); b=np.where(np.isfinite(test),test,mean)
    scale=a.std(axis=0,ddof=0); scale=np.where(scale>1e-12,scale,1.)
    return (a-mean)/scale,(b-mean)/scale,mean,scale

def memberships_score(a,b,membership,svd=False):
    aa=[]; bb=[]; learned=0
    for column in membership.columns:
        use=membership[column].to_numpy(dtype=bool)
        if not use.any(): continue
        x=a[:,use]; z=b[:,use]
        if svd:
            transform=PCA(n_components=1,svd_solver='full')
            aa.append(transform.fit_transform(x)[:,0]); bb.append(transform.transform(z)[:,0])
            learned+=x.shape[1]
        else:
            aa.append(np.median(x,axis=1)); bb.append(np.median(z,axis=1))
    if not aa: raise ValueError('Empty representation')
    return np.column_stack(aa),np.column_stack(bb),learned

def representations(train,test,visible,incidence,families,seed):
    # The availability rule sees only this training partition.
    use=np.isfinite(train).mean(axis=0)>=.8
    visible=list(np.asarray(visible)[use]); train=train[:,use]; test=test[:,use]
    if not visible: raise ValueError('No training-eligible visible inputs')
    a,b,_,_=standardize(train,test)
    member=incidence.loc[visible]
    member=member.loc[:,member.sum(axis=0).ge(2)]
    null=degree_preserving_descriptor_null(member,swaps_per_edge=10,seed=seed)
    assert np.array_equal(member.sum(axis=0),null.sum(axis=0))
    assert np.array_equal(member.sum(axis=1),null.sum(axis=1))
    fm=pd.get_dummies(families.loc[visible],dtype=bool)
    values={
        'structural_median':memberships_score(a,b,member),
        'descriptor_local_svd':memberships_score(a,b,member,True),
        'degree_preserving_null':memberships_score(a,b,null),
        'family_median':memberships_score(a,b,fm),
        'all_visible_ridge':(a,b,0),
    }
    pc=PCA(n_components=None,svd_solver='full').fit(a)
    tolerance=pc.singular_values_[0]*max(a.shape)*np.finfo(float).eps
    rank=int((pc.singular_values_>tolerance).sum())
    dimension=min(member.shape[1],rank)
    if dimension==0: raise ValueError('PCA has zero training rank')
    values['pca_matched_dimension']=(pc.transform(a)[:,:dimension],pc.transform(b)[:,:dimension],dimension*a.shape[1])
    out={}
    for key,(x,z,learned) in values.items():
        x,z,_,_=standardize(x,z)
        out[key]=(x,z,{'measured_inputs':len(visible),'representation_dimension':x.shape[1],
                      'pca_training_rank':rank if key=='pca_matched_dimension' else None,
                      'pca_rank_capped':dimension<member.shape[1] if key=='pca_matched_dimension' else False,
                      'transform_loadings':learned,'visible_schema_sha256':hashlib.sha256('\n'.join(visible).encode()).hexdigest()})
    return out

def group_losses(truth,pred,groups):
    finite=np.isfinite(truth)
    valid=finite.sum(axis=1)
    errors=np.where(finite,(truth-pred)**2,0).sum(axis=1)
    rows=np.divide(errors,valid,out=np.full(len(errors),np.nan),where=valid>0)
    return pd.Series(rows).groupby(np.asarray(groups)).mean().dropna()

def group_loss(truth,pred,groups):
    return group_losses(truth,pred,groups).mean()

def complete_training_targets(train_y):
    return np.isfinite(train_y).all(axis=0)&(np.nanstd(train_y,axis=0)>1e-12)

def summarize_group_losses(frame):
    samples=frame.groupby(['sample_id','group_id','model'],as_index=False)['mse'].mean()
    return samples.groupby(['group_id','model'],as_index=False)['mse'].mean()

def ridge(a,b,y,alpha):
    model=Ridge(alpha=alpha,solver='cholesky').fit(a,y)
    return model.predict(b)

def paired_inference(group,reference,challenger):
    table=group.pivot(index='group_id',columns='model',values='mse')[[reference,challenger]].dropna()
    x=table.to_numpy(); rng=np.random.default_rng(20260921)
    ix=rng.integers(0,len(x),size=(10000,len(x)))
    d=np.sqrt(x[ix,0].mean(axis=1))-np.sqrt(x[ix,1].mean(axis=1))
    rng=np.random.default_rng(20260922); signs=rng.choice([-1,1],size=(10000,len(x)))
    delta=x[:,0]-x[:,1]; p=(1+(np.abs((signs*delta).mean(axis=1))>=abs(delta.mean())).sum())/10001
    return {'reference':reference,'challenger':challenger,'biological_groups':len(x),
            'rmse_improvement':float(np.sqrt(x[:,0].mean())-np.sqrt(x[:,1].mean())),
            'ci95_lower':float(np.quantile(d,.025)),'ci95_upper':float(np.quantile(d,.975)),
            'simultaneous99_lower':float(np.quantile(d,.005)),'simultaneous99_upper':float(np.quantile(d,.995)),
            'sign_flip_p_two_sided':float(p),'draws':10000}

def run(dataset,mode,output,max_outer=0):
    start=time.monotonic(); preflight(); code_hash=sha(__file__)
    if sha(ROOT/'readiness/m2-benchmark-lock-v1.md')!='b0bb3f38101a4d469eef9cc4cf4479433e0a57536df6edf15a74f2194f9def4f':
        raise RuntimeError('Protocol lock changed')
    output.mkdir(parents=True,exist_ok=True)
    if (output/'manifest.json').exists(): raise RuntimeError('Output already completed; choose fresh directory')
    private=ROOT/'work/m2-human'/output.name
    private.mkdir(parents=True,exist_ok=True)
    values,groups,families,seeds=load_data(dataset,mode)
    masks=disjoint_family_masks(families,masks=5,seed=seeds['mask'])
    if mode=='resolution': incidence,changes=resolution_incidence(families.index)
    else:
        incidence=structural_descriptor_incidence(families.index,minimum_features=5,maximum_feature_fraction=.9); changes=[]
    masks.to_csv(output/'feature-masks.csv',index=False)
    pd.DataFrame(changes,columns=['feature','removed_descriptor']).to_csv(output/'resolution-changes.csv',index=False)
    splits=repeated_balanced_group_splits(groups,GroupedValidationSpec(outer_folds=5,repeats=1,seed=seeds['outer']))
    rows=[]; tuning=[]; budgets=[]; exclusions=[]; split_records=[]; processed=0
    for mask in sorted(masks['mask'].unique()):
        hidden=sorted(masks.loc[masks['mask'].eq(mask),'feature'])
        visible=sorted(set(values.columns)-set(hidden))
        assert not set(hidden)&set(visible)
        for train,test,repeat,fold in splits:
            if max_outer and processed>=max_outer: break
            processed+=1; tick=time.monotonic()
            x=values.loc[:,visible].to_numpy(); y_full=values.loc[:,hidden].to_numpy()
            target_keep=complete_training_targets(y_full[train])
            exclusions.append({'mask':int(mask),'fold':fold,'targets_total':len(hidden),'targets_retained':int(target_keep.sum()),
                               'targets_dropped':';'.join(np.asarray(hidden)[~target_keep])})
            if not target_keep.any(): raise ValueError('No target complete in training')
            y=y_full[:,target_keep]; outer_group=groups.iloc[train]
            inner=repeated_balanced_group_splits(outer_group,GroupedValidationSpec(outer_folds=3,repeats=1,seed=20260921+fold))
            scores={m:{alpha:[] for alpha in ALPHAS} for m in MODELS if m!='population_mean'}
            for it,iv,_,inner_fold in inner:
                tr=train[it]; va=train[iv]
                inner_keep=complete_training_targets(y_full[tr])
                if not inner_keep.any(): raise ValueError('No inner-training eligible targets')
                yt,_,mean,scale=standardize(y_full[tr][:,inner_keep],y_full[va][:,inner_keep])
                yv=(y_full[va][:,inner_keep]-mean)/scale
                reps=representations(x[tr],x[va],visible,incidence,families,seeds['null']+int(mask))
                for model,(a,b,budget) in reps.items():
                    for alpha in ALPHAS:
                        loss=group_losses(yv,ridge(a,b,yt,alpha),groups.iloc[va])
                        scores[model][alpha].extend(loss.tolist())
                        tuning.append({'mask':int(mask),'fold':fold,'inner_fold':inner_fold,'model':model,'alpha':alpha,
                                       'group_mse':loss.mean(),'validation_groups':len(loss),'training_targets':int(inner_keep.sum())})
            selected={m:min(ALPHAS,key=lambda alpha:(np.mean(s[alpha]),alpha)) for m,s in scores.items()}
            yt,_,mean,scale=standardize(y[train],y[test]); truth=(y[test]-mean)/scale
            reps=representations(x[train],x[test],visible,incidence,families,seeds['null']+int(mask))
            predictions={'population_mean':np.zeros_like(truth)}
            for model,(a,b,budget) in reps.items():
                predictions[model]=ridge(a,b,yt,selected[model])
                budgets.append({'mask':int(mask),'fold':fold,'model':model,'alpha':selected[model],
                                'targets':truth.shape[1],'ridge_coefficients':a.shape[1]*truth.shape[1],**budget})
            fold_identity=hashlib.sha256('\n'.join(sorted(map(str,groups.iloc[test].unique()))).encode()).hexdigest()
            split_records.append({'mask':int(mask),'fold':fold,'train_rows':len(train),'test_rows':len(test),
                                  'train_groups':groups.iloc[train].nunique(),'test_groups':groups.iloc[test].nunique(),
                                  'test_group_sha256':fold_identity,'seconds':time.monotonic()-tick})
            for model,pred in predictions.items():
                finite=np.isfinite(truth); count=finite.sum(axis=1)
                sq=np.where(finite,(truth-pred)**2,0).sum(axis=1)
                energy=np.where(finite,truth**2,0).sum(axis=1)
                for j,index in enumerate(test):
                    rows.append({'sample_id':str(values.index[index]),'group_id':str(groups.iloc[index]),'mask':int(mask),'fold':fold,
                                 'model':model,'targets_observed':int(count[j]),'sse':sq[j],'energy':energy[j],
                                 'mse':sq[j]/count[j] if count[j] else np.nan})
            (output/'progress.json').write_text(json.dumps({'pid':os.getpid(),'dataset':dataset,'mode':mode,
                    'completed_outer':processed,'total_outer':25,'elapsed_seconds':time.monotonic()-start})+'\n')
            print(json.dumps({'dataset':dataset,'mode':mode,'mask':int(mask),'fold':fold,'seconds':round(time.monotonic()-tick,2)}),flush=True)
        if max_outer and processed>=max_outer: break
    frame=pd.DataFrame(rows)
    assert not frame.duplicated(['sample_id','mask','model']).any()
    frame.to_csv(private/'sample-losses.csv',index=False)
    group=summarize_group_losses(frame)
    group.to_csv(private/'group-losses.csv',index=False)
    metrics=[]
    for model,g in group.groupby('model'):
        f=frame.loc[frame['model'].eq(model)]
        metrics.append({'model':model,'groups':len(g),'equal_group_rmse':np.sqrt(g['mse'].mean()),
                        'row_weighted_rmse':np.sqrt(f['sse'].sum()/f['targets_observed'].sum()),
                        'skill_vs_training_mean':1-f['sse'].sum()/f['energy'].sum(),
                        'evaluated_pairs':int(f['targets_observed'].sum())})
    pd.DataFrame(metrics).to_csv(output/'model-metrics.csv',index=False)
    comparisons=[paired_inference(group,m,'structural_median') for m in MODELS if m!='structural_median']
    pd.DataFrame(comparisons).to_csv(output/'paired-comparisons.csv',index=False)
    pd.DataFrame(tuning).to_csv(output/'tuning-grid.csv',index=False)
    pd.DataFrame(budgets).to_csv(output/'budget-grid.csv',index=False)
    pd.DataFrame(exclusions).to_csv(output/'exclusions.csv',index=False)
    pd.DataFrame(split_records).to_csv(output/'split-summary.csv',index=False)
    # Actual group assignments stay local and ignored, while hashes are exportable.
    pd.DataFrame([{'sample_id':str(values.index[i]),'group_id':str(groups.iloc[i]),'fold':fold}
                  for _,test,_,fold in splits for i in test]).to_csv(private/'split-ledger.csv',index=False)
    if sha(__file__)!=code_hash: raise RuntimeError('Implementation changed during run')
    manifest={'completed_at':datetime.now(timezone.utc).isoformat(),'pid':os.getpid(),'dataset':dataset,'mode':mode,
              'adaptive':True,'pilot':bool(max_outer),'completed_outer':processed,'samples':len(values),'groups':groups.nunique(),
              'features':values.shape[1],'descriptors':incidence.shape[1],'elapsed_seconds':time.monotonic()-start,
              'code_sha256':code_hash,'protocol_sha256':sha(ROOT/'readiness/m2-benchmark-lock-v1.md'),
              'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
              'resolution_amendment_sha256':sha(ROOT/'readiness/m2-amendment-resolution-v1.md'),
              'input_receipt_sha256':sha(ROOT/'receipts/m0-input-recovery.json'),'command':sys.argv,
              'private_losses':str(private),'output_sha256':{p.name:sha(p) for p in output.glob('*.csv')}}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--dataset',choices=['st002081','st000818'],required=True)
    parser.add_argument('--mode',choices=['primary','missingness','resolution'],default='primary')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--max-outer',type=int,default=0)
    args=parser.parse_args()
    print(json.dumps(run(args.dataset,args.mode,args.output,args.max_outer),indent=2))
