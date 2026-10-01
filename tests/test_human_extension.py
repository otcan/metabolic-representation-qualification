import importlib.util
from pathlib import Path
import numpy as np
import pandas as pd

spec=importlib.util.spec_from_file_location('human_extension',Path(__file__).parents[1]/'scripts/human_extension.py')
h=importlib.util.module_from_spec(spec); spec.loader.exec_module(h)

def test_heldout_values_do_not_change_fitted_representations():
    rng=np.random.default_rng(41)
    features=[f'PC({14+i%4}:0/{16+i%3}:1)' for i in range(12)]
    # Unique identifiers preserve explicit chain parsing while avoiding duplicate names.
    features=[f'{name};{i}' for i,name in enumerate(features)]
    incidence=h.structural_descriptor_incidence(pd.Index(features),minimum_features=2,maximum_feature_fraction=.95)
    families=pd.Series('PC',index=features)
    train=rng.normal(size=(30,12)); test=rng.normal(size=(9,12))
    a=h.representations(train,test,features,incidence,families,90)
    b=h.representations(train,test*100+1000,features,incidence,families,90)
    for model in a:
        np.testing.assert_array_equal(a[model][0],b[model][0])
        assert a[model][2]==b[model][2]

def test_missing_heldout_truth_is_not_imputed_as_observation():
    truth=np.array([[1.,np.nan],[3.,4.]])
    pred=np.zeros_like(truth)
    assert h.group_loss(truth,pred,['a','b'])==(1+(9+16)/2)/2

def test_group_weighting_does_not_count_repeated_visits_as_people():
    truth=np.array([[1.],[1.],[3.]])
    assert h.group_loss(truth,np.zeros_like(truth),['a','a','b'])==5.

def test_resolution_filter_retains_totals_without_inventing_chains():
    features=pd.Index([f'PC 34:2;{i}' for i in range(6)]+[f'PC 36:3;{i}' for i in range(6)])
    incidence,changes=h.resolution_incidence(features)
    assert len(changes)==36
    assert not any(c.startswith(('acyl:','chain_')) for c in incidence)
    assert 'total_carbon:34' in incidence

def test_paired_bootstrap_identical_models_have_zero_difference():
    df=pd.DataFrame([{'group_id':str(i),'model':m,'mse':float(i+1)} for i in range(12) for m in ['a','b']])
    result=h.paired_inference(df,'a','b')
    assert result['rmse_improvement']==result['ci95_lower']==result['ci95_upper']==0.
    assert result['sign_flip_p_two_sided']==1.

def test_nested_target_eligibility_uses_only_training_values():
    training=np.array([[1.,1.,1.],[2.,2.,np.nan],[3.,3.,3.]])
    validation=np.array([[np.nan,3.,1.]])
    assert h.complete_training_targets(training).tolist()==[True,True,False]
    # Adding validation would incorrectly exclude the first training-complete target.
    assert h.complete_training_targets(np.vstack([training,validation])).tolist()==[False,True,False]

def test_group_pooling_weights_groups_not_validation_folds():
    first=h.group_losses(np.sqrt([[3.],[3.]]),np.zeros((2,1)),['a','b'])
    second=h.group_losses(np.zeros((20,1)),np.zeros((20,1)),['c']*10+['d']*10)
    assert np.isclose(np.mean([*first,*second]),1.5)

def test_masks_averaged_within_sample_before_participant():
    frame=pd.DataFrame({'sample_id':['s1','s1','s2','s2'],'group_id':['a']*4,
                        'model':['m']*4,'mse':[1.,1.,9.,np.nan]})
    assert h.summarize_group_losses(frame).iloc[0]['mse']==5.

def test_pca_components_capped_at_numerical_training_rank():
    features=pd.Index([f'PC({14+i}:0/16:1)' for i in range(10)])
    incidence=pd.DataFrame({f'd{j}':[i%5==j or (i+1)%5==j for i in range(10)] for j in range(5)},index=features)
    # Many descriptors but a single independent direction in the values.
    train=np.arange(30.)[:,None]@np.arange(1.,11.)[None,:]
    test=np.arange(5.)[:,None]@np.arange(1.,11.)[None,:]
    result=h.representations(train,test,list(features),incidence,pd.Series('PC',index=features),91)
    assert result['pca_matched_dimension'][2]['pca_training_rank']==1
    assert result['pca_matched_dimension'][2]['representation_dimension']==1
