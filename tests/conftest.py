import numpy as np
import pytest
from mri_pipeline.fmri import NETWORKS, STRUCTURES


@pytest.fixture
def roi_order():
    # SYNTHETIC labels solely for program tests, never an atlas for real extraction.
    rows=[]
    for i in range(450):
        sub=i<50
        rows.append({'column_index':str(i),'atlas_label':f'SYNTHETIC_{i}',
            'roi_name':f'test_roi_{i}','structure_type':'subcortical' if sub else 'cortical',
            'hemisphere':'L' if i%2==0 else 'R','network7':'' if sub else NETWORKS[(i-50)%7],
            'parent_structure':STRUCTURES[i%7] if sub else ''})
    return rows


def synthetic_data(people=32, visits=1):
    rng=np.random.default_rng(17)
    n=people*visits
    y=np.repeat(np.arange(people)%2,visits)
    return {'record_id':np.asarray([f'SYNTHETIC_record_{i}' for i in range(n)]),
        'person_id':np.repeat([f'SYNTHETIC_person_{i}' for i in range(people)],visits),
        'label':y,'age':rng.normal(65,5,n),'sex':np.where(np.arange(n)%3==0,'F','M'),
        'education_code':np.where(np.arange(n)%3==0,'12','16'),
        's_fmri':rng.normal(size=(n,77)),'z_fmri':rng.normal(size=(n,5))+y[:,None]*.1,
        'data_kind':'synthetic'}
