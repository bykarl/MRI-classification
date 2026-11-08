import numpy as np
import pytest
from sklearn.metrics import roc_auc_score
from mri_pipeline.models import (CrossfitModels, Parameters, FoldTransform, nested_evaluate,
    bootstrap_auc, splits, subset, person_predictions, OffsetMLP)
from conftest import synthetic_data


def test_crossfit_groups_are_disjoint_and_each_person_held_once():
    data=synthetic_data(32,2)
    m=CrossfitModels(Parameters(epochs=3,width=3),2,7).fit(data)
    held=[]
    for a in m.audit:
        assert not set(a['fit_people']) & set(a['heldout_people'])
        held+=a['heldout_people']
    assert sorted(held)==sorted(set(data['person_id']))
    p=m.predict(data)
    assert p.shape==(64,6) and np.isfinite(p).all() and np.all((p>=0)&(p<=1))
    # Exact fixed-logit semantics: zero correction reduces both U and R to S.
    for h in [m.u,m.r]: h.params=[np.zeros_like(a) for a in h.params]
    p=m.predict(data)
    np.testing.assert_allclose(p[:,1],p[:,4],atol=1e-12)
    np.testing.assert_allclose(p[:,1],p[:,5],atol=1e-12)


def test_heldout_person_cannot_change_their_nuisance_models():
    d=synthetic_data()
    p=Parameters(epochs=2,width=2)
    a=CrossfitModels(p,2,9).fit(d)
    group=a.audit[0]['heldout_people'][0]
    changed={k:v.copy() if isinstance(v,np.ndarray) else v for k,v in d.items()}
    idx=changed['person_id']==group
    changed['age'][idx]=10000;changed['s_fmri'][idx]=10000;changed['z_fmri'][idx]=10000
    b=CrossfitModels(p,2,9).fit(changed)
    np.testing.assert_array_equal(a.paths[0]['b'].coef_,b.paths[0]['b'].coef_)
    np.testing.assert_array_equal(a.paths[0]['g'].coef_,b.paths[0]['g'].coef_)
    np.testing.assert_array_equal(a.paths[0]['transform'].age_scale.mean_,b.paths[0]['transform'].age_scale.mean_)


def test_icv_adjustment_uses_training_relationship_only():
    d=synthetic_data(10)
    icv=np.linspace(1000,2000,10)
    d['icv_mm3']=icv
    d['s_t1_raw']=np.tile(icv[:,None]*2,(1,82))+10
    transform=FoldTransform().fit(subset(d,np.arange(8)))
    np.testing.assert_allclose(transform.icv_slope,2.)
    corrected=transform.raw_s(d)[:,:82]
    np.testing.assert_allclose(corrected,2*icv[:8].mean()+10)


def test_offset_mlp_uses_classification_loss_and_learns_signal():
    x=np.r_[np.full((20,1),-1.),np.full((20,1),1.)]
    y=np.r_[np.zeros(20,dtype=int),np.ones(20,dtype=int)]
    m=OffsetMLP(width=3,epochs=100,seed=4).fit(x,y,np.zeros(40))
    assert roc_auc_score(y,m.logit(x))>.99


def test_split_rejects_insufficient_people_and_label_conflict():
    with pytest.raises(ValueError): splits(np.array([0,1]),np.array(['a','b']),2,1)
    with pytest.raises(ValueError,match='Conflicting'): splits(np.array([0,1]),np.array(['a','a']),2,1)


def test_nested_synthetic_paths_keep_outer_people_out():
    d=synthetic_data(32,2)
    result=nested_evaluate(d,[Parameters(epochs=2,width=2),Parameters(logistic_c=.5,epochs=2,width=2)],
        outer_folds=2,inner_folds=2,crossfit_folds=2,repeats=1,
        paired_selection_rule='mean_inner_U_R_auc',synthetic=True)
    assert result['data_kind']=='synthetic'
    assert result['probabilities'].shape==(1,64,6)
    for fold in result['audit']:
        assert fold['selected_candidates'][4]==fold['selected_candidates'][5]
        assert not set(fold['train_people']) & set(fold['test_people'])
        for path in fold['crossfit_paths']:
            assert not set(fold['test_people']) & (set(path['fit_people'])|set(path['heldout_people']))


def test_no_synthetic_bypass_for_unmarked_data():
    d=synthetic_data();d.pop('data_kind')
    with pytest.raises(ValueError,match='tagged'):
        nested_evaluate(d,[Parameters()],outer_folds=2,inner_folds=2,crossfit_folds=2,repeats=1,
            paired_selection_rule='mean_inner_U_R_auc',synthetic=True)


def test_bootstrap_keeps_repeat_predictions_grouped_by_person():
    d=synthetic_data(32,2)
    p=np.random.default_rng(3).uniform(size=(1,64,6))
    a=bootstrap_auc(d['label'],p,d['person_id'],n_boot=12)
    b=bootstrap_auc(d['label'],np.repeat(p,3,axis=0),d['person_id'],n_boot=12)
    np.testing.assert_allclose(a['auc_interval_95'],b['auc_interval_95'],atol=1e-12)
