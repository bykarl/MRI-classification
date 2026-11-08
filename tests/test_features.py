import json
import numpy as np
import pytest
from mri_pipeline.fmri import select_window, window_data, connectivity77
from mri_pipeline.io import save_component, load_component, sha256, write_json
from mri_pipeline.features import merge_features, formal_eligibility
from mri_pipeline.manifest import pilot_rows
from mri_pipeline.encoders import jepa_tensor, check_handoff
from pathlib import Path


def test_pinned_pilot_has_no_unearned_readiness():
    rows=pilot_rows(Path(__file__).resolve().parents[1])
    assert len(rows)==5
    assert all(r['training_ready']=='False' and r['person_id']=='' and r['qc_status']=='pending' for r in rows)
    assert rows[0]['record_id']=='sub-mindo304_ses-placebo'


def test_window_selects_lowest_motion_and_earliest_tie():
    fd=np.ones(170)
    fd[0]=10
    w=select_window(fd,np.ones(170,dtype=bool),np.arange(170))
    assert w['row_start']==1 and w['row_end_exclusive']==161


def test_discontinuous_frames_cannot_be_concatenated():
    frames=np.r_[np.arange(80),np.arange(81,161)]
    with pytest.raises(ValueError,match='continuous'):
        select_window(np.zeros(160),np.ones(160,dtype=bool),frames)


def test_window_slice_rejects_out_of_bounds_and_gap():
    w=select_window(np.zeros(160),np.ones(160,dtype=bool),np.arange(160))
    with pytest.raises(ValueError): window_data(np.zeros((159,450)),w)
    w['frame_indices'][20]+=1
    with pytest.raises(ValueError): window_data(np.zeros((160,450)),w)


def test_fc_edges_and_signed_values(roi_order):
    rng=np.random.default_rng(3)
    signal=rng.normal(size=160)
    x=rng.normal(size=(160,450))*.1
    for i,r in enumerate(roi_order):
        x[:,i]+=(-signal if r['network7']=='SomMot' else signal)
    values,meta=connectivity77(x,roi_order)
    assert len(values)==77 and sum(meta['edge_counts'][:28])==400*399//2
    assert sum(meta['edge_counts'][28:])==50*400
    assert values[0]>0 and values[1]<0
    # No dependence on arbitrary column positions after matched data/schema reorder.
    order=rng.permutation(450)
    reordered=[dict(roi_order[j],column_index=str(i)) for i,j in enumerate(order)]
    other,_=connectivity77(x[:,order],reordered)
    np.testing.assert_allclose(other,values,atol=1e-10)


def test_fc_rejects_zero_variance_and_incomplete_mapping(roi_order):
    x=np.random.default_rng(2).normal(size=(160,450));x[:,3]=0
    with pytest.raises(ValueError,match='variance'): connectivity77(x,roi_order)
    roi_order[50]['network7']=''
    with pytest.raises(ValueError,match='mapping'): connectivity77(x,roi_order)


def component(root,rid,name='z_t1',recipe=None,window=None):
    meta={'pipeline_id':'SYNTHETIC','qc_status':'pass','source_files':{'test':'synthetic only'},
          'names':['f0','f1'],'recipe':recipe or {'test_version':1}}
    if window: meta['window_id']=window
    return save_component(root,'SYNTHETIC',rid,name,[1.,2.],meta)


def test_features_hash_overwrite_and_record_key(tmp_path):
    p=component(tmp_path,'a')
    with pytest.raises(FileExistsError): component(tmp_path,'a')
    with (p/'z_t1.npy').open('ab') as f: f.write(b'changed')
    with pytest.raises(ValueError,match='SHA-256'): load_component(p,'z_t1')


def test_feature_merge_joins_ids_not_row_order(tmp_path):
    component(tmp_path,'b');component(tmp_path,'a')
    rows=[{'record_id':'b','label':'1','age':'70'},{'record_id':'a','label':'0','age':'60'}]
    data,_=merge_features(rows,tmp_path/'features/SYNTHETIC',['z_t1'])
    assert list(data['record_id'])==['a','b'] and list(data['label'])==[0,1]
    with pytest.raises(ValueError,match='duplicate'): merge_features(rows+rows[:1],tmp_path,['z_t1'])


def test_feature_merge_rejects_mixed_weight_recipe(tmp_path):
    component(tmp_path,'a');component(tmp_path,'b',recipe={'test_version':2})
    rows=[{'record_id':r,'label':'0','age':'60'} for r in ['a','b']]
    with pytest.raises(ValueError,match='recipe'): merge_features(rows,tmp_path/'features/SYNTHETIC',['z_t1'])


def test_formal_gate_rejects_current_pilot():
    rows=pilot_rows(Path(__file__).resolve().parents[1])
    data={k:np.asarray([r[k] for r in rows]) for k in ['record_id','label','person_id','identity_status','diagnosis_status','qc_status','training_ready']}
    with pytest.raises(ValueError,match='identity_status'): formal_eligibility(data)


def test_jepa_requires_confirmed_order_and_normalization(roi_order):
    x=np.random.default_rng(4).normal(size=(160,450))
    with pytest.raises(ValueError,match='not confirmed'): jepa_tensor(x,roi_order,{}, {})
    contract={'confirmed':True,'roi_labels':[r['atlas_label'] for r in roi_order],
        'atlas_name':'SYNTHETIC','atlas_space':'SYNTHETIC','atlas_sha256':'a'*64,
        'roi_order_sha256':'b'*64,'gradient_sha256':'c'*64}
    cfg={'recipe_confirmed':True,'normalization':'global_sample_standardization'}
    tensor=jepa_tensor(x,roi_order,contract,cfg)
    assert tensor.shape==(1,1,450,160)
    np.testing.assert_allclose(tensor.std(ddof=1),1.,rtol=1e-5)
    contract['roi_labels'].reverse()
    with pytest.raises(ValueError,match='order'): jepa_tensor(x,roi_order,contract,cfg)


def test_handoff_rejects_bad_hash_even_if_qc_marked_pass(tmp_path):
    p=tmp_path/'input.txt';p.write_text('synthetic')
    h={'record_id':'test','pipeline_id':'SYNTHETIC','stages':{'t1':{
        'status':'ready','qc_status':'pass','qc_reviewer':'synthetic test',
        'files':{'input':{'path':'input.txt','sha256':'a'*64}}}}}
    write_json(tmp_path/'handoff.json',h)
    with pytest.raises(ValueError,match='SHA-256'): check_handoff(tmp_path/'handoff.json','t1')


def test_joint_merge_rejects_different_windows_or_roi_order(tmp_path):
    for component_name,n in [('s_fmri',77),('z_fmri',5)]:
        metadata={'pipeline_id':'SYNTHETIC','qc_status':'pass','source_files':{'roi_timeseries':{'sha256':'x'*64}},
            'names':[f'f{i}' for i in range(n)],'recipe':{'synthetic':True},
            'window_id':'window-A' if component_name=='s_fmri' else 'window-B','roi_order_sha256':'roi-A'}
        save_component(tmp_path,'SYNTHETIC','a',component_name,np.ones(n),metadata)
    rows=[{'record_id':'a','label':'0','age':'60'}]
    root=tmp_path/'features/SYNTHETIC'
    with pytest.raises(ValueError,match='window mismatch'): merge_features(rows,root,['s_fmri','z_fmri'])
    path=root/'a/z_fmri.json';meta=json.loads(path.read_text())
    meta['window_id']='window-A';meta['roi_order_sha256']='roi-B';path.write_text(json.dumps(meta))
    with pytest.raises(ValueError,match='ROI mismatch'): merge_features(rows,root,['s_fmri','z_fmri'])
    meta['roi_order_sha256']='roi-A';path.write_text(json.dumps(meta))
    data,_=merge_features(rows,root,['s_fmri','z_fmri'])
    assert data['s_fmri'].shape==(1,77)


def test_freesurfer_names_and_thalamus_aliases(tmp_path):
    from mri_pipeline.structure import CORTEX, SUBCORTEX, volumes82, VOLUME_NAMES
    paths=[]
    for hemi in ['lh','rh']:
        p=tmp_path/f'{hemi}.aparc.stats'
        p.write_text('\n'.join(f'{n} 1 2 100 4' for n in CORTEX));paths.append(p)
    aseg=tmp_path/'aseg.stats'
    lines=[f'1 10 3 200 {side}-{n}' for side in ['Left','Right'] for n in SUBCORTEX]
    aseg.write_text('\n'.join(lines))
    current,names=volumes82(*paths,aseg)
    assert len(current)==82 and names==VOLUME_NAMES
    aseg.write_text('\n'.join(lines).replace('Thalamus','Thalamus-Proper'))
    legacy,_=volumes82(*paths,aseg)
    np.testing.assert_array_equal(legacy,current)
    aseg.write_text('\n'.join(lines)+'\n1 10 3 200 Left-Thalamus-Proper')
    with pytest.raises(ValueError,match='ambiguous'):volumes82(*paths,aseg)


def test_agreed_raw_volume_csv_interface(tmp_path):
    import csv
    from mri_pipeline.structure import VOLUME_NAMES, volume_record
    row={'record_id':'SYNTHETIC_record',**{n:100 for n in VOLUME_NAMES},
         'icv_mm3':1500000,'icv_method':'SYNTHETIC_TEST','freesurfer_version':'SYNTHETIC_TEST','qc_status':'pass'}
    p=tmp_path/'volumes.csv'
    with p.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(row));writer.writeheader();writer.writerow(row)
    values,names,metadata=volume_record(p,'SYNTHETIC_record')
    assert len(values)==82 and names==VOLUME_NAMES and metadata['icv_mm3']==1500000
    with p.open('a',newline='') as f:csv.DictWriter(f,fieldnames=list(row)).writerow(row)
    with pytest.raises(ValueError,match='duplicate'):volume_record(p,'SYNTHETIC_record')
