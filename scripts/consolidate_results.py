"""Assemble accepted run outputs only; reject pilot or superseded evidence."""
import hashlib
import json
import os
from pathlib import Path
import numpy as np
import pandas as pd
from statsmodels.stats.multitest import multipletests

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results'; OUT.mkdir(exist_ok=True)
records=[]; contrasts=[]; budgets=[]; manifests=[]
for dataset in ['st002081','st000818']:
    for mode in ['primary','missingness','resolution']:
        path=ROOT/f'runs/m2-human-r2-{dataset}-{mode}'
        if not (path/'manifest.json').exists():
            if mode=='primary': raise RuntimeError('Primary result absent')
            continue
        manifest=json.loads((path/'manifest.json').read_text())
        assert not manifest['pilot'] and manifest['completed_outer']==25
        for name,expected in manifest['output_sha256'].items():
            assert hashlib.sha256((path/name).read_bytes()).hexdigest()==expected,(path,name)
        manifests.append({'dataset':dataset,'mode':mode,'manifest':str(path/'manifest.json'),'code_sha256':manifest['code_sha256']})
        frame=pd.read_csv(path/'model-metrics.csv')
        for r in frame.to_dict('records'):
            records.append({'dataset':dataset,'mode':mode,'model':r['model'],'primary_rmse':r['equal_group_rmse'],
                            'groups':r['groups'],'row_weighted_rmse':r['row_weighted_rmse'],
                            'metric':'sqrt(equal biological-group MSE)','source':str(path/'model-metrics.csv')})
        budget=pd.read_csv(path/'budget-grid.csv')
        for model,b in budget.groupby('model'):
            budgets.append({'dataset':dataset,'mode':mode,'model':model,
                            'measured_inputs_min':b.measured_inputs.min(),'measured_inputs_max':b.measured_inputs.max(),
                            'dimension_min':b.representation_dimension.min(),'dimension_max':b.representation_dimension.max(),
                            'learned_loadings_median':b.transform_loadings.median(),'ridge_coefficients_median':b.ridge_coefficients.median()})
        if mode=='primary':
            paired=pd.read_csv(path/'paired-comparisons.csv')
            for reference in ['pca_matched_dimension','descriptor_local_svd']:
                r=paired.set_index('reference').loc[reference]
                contrasts.append({'dataset':dataset,'mechanism':'structural_median','reference':reference,
                                  'improvement':r.rmse_improvement,'ci95_lower':r.ci95_lower,'ci95_upper':r.ci95_upper,
                                  'simultaneous99_lower':r.simultaneous99_lower,'simultaneous99_upper':r.simultaneous99_upper,
                                  'p_raw':r.sign_flip_p_two_sided,'groups':r.biological_groups})
ccle=ROOT/'runs/m2-ccle'
manifest=json.loads((ccle/'manifest.json').read_text()); assert manifest['state']=='COMPLETE' and manifest['targets']==60 and not manifest['pilot']
for name,expected in manifest['outputs_sha256'].items():
    assert hashlib.sha256((ccle/name).read_bytes()).hexdigest()==expected,name
manifests.append({'dataset':'ccle','mode':'primary','manifest':str(ccle/'manifest.json'),'code_sha256':manifest['code_sha256']})
for r in pd.read_csv(ccle/'model-metrics.csv').to_dict('records'):
    records.append({'dataset':'ccle','mode':'primary','model':r['model'],'primary_rmse':r['primary_rmse_sd'],
                    'groups':18,'row_weighted_rmse':r['descriptive_row_weighted_rmse_sd'],
                    'metric':'sqrt(mean fixed-target/equal available-lineage MSE)','source':str(ccle/'model-metrics.csv')})
r=json.loads((ccle/'primary-comparison.json').read_text())
contrasts.append({'dataset':'ccle','mechanism':r['mechanism'],'reference':r['reference'],'improvement':r['rmse_improvement_sd'],
                  'ci95_lower':r['ci95_lower'],'ci95_upper':r['ci95_upper'],'simultaneous99_lower':r['simultaneous99_lower'],
                  'simultaneous99_upper':r['simultaneous99_upper'],'p_raw':r['signflip_p_two_sided_raw'],'groups':r['biological_groups']})
table=pd.DataFrame(contrasts); table['p_holm']=multipletests(table.p_raw,method='holm')[1]
table['direction']=np.where(table.improvement>0,'mechanism_lower_error','reference_lower_error')
table.to_csv(OUT/'primary-comparisons.csv',index=False)
pd.DataFrame(records).to_csv(OUT/'all-model-metrics.csv',index=False)
pd.DataFrame(budgets).to_csv(OUT/'human-information-budgets.csv',index=False)
budget=pd.read_csv(ccle/'budgets.csv')
cols=['raw_metabolites','raw_transcript_genes','expression_signatures','interaction_count','representation_dimension','transform_learned_parameters','selection_candidate_metabolites','coefficient_count']
summary=budget.groupby('model')[cols].agg(['min','median','max']); summary.columns=['_'.join(c) for c in summary.columns]
summary.reset_index().to_csv(OUT/'ccle-information-budgets.csv',index=False)
(OUT/'source-manifests.json').write_text(json.dumps(manifests,indent=2)+'\n')
print(table.to_string(index=False))
