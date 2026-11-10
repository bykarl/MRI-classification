"""SYNTHETIC UNIT TESTS only: no MRI, FreeSurfer binary, license, or network."""
import io
import json
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
sys.path.insert(0,str(ROOT/'src'))
import freesurfer_pilot as runner
import freesurfer_volumes as volume
from mri_pipeline.structure import volumes82,volume_record


def fixtures(folder,alias=False):
    names=json.loads((ROOT/'schemas/t1_volume_names.json').read_text())['names']
    expected={name:float(100+i*3) for i,name in enumerate(names)}
    for side in ['lh','rh']:
        text='# SYNTHETIC_UNIT_TEST, not patient statistics\n# ColHeaders StructName NumVert SurfArea GrayVol ThickAvg ThickStd MeanCurv GausCurv FoldInd CurvInd\n'
        for name in names:
            if name.startswith(side+'_'):
                text+=f'{name[3:-4]} 10 20 {expected[name]} 2 0.1 0 0 0 0\n'
        (folder/(side+'.aparc.stats')).write_text(text)
    text='# SYNTHETIC_UNIT_TEST\n# Measure EstimatedTotalIntraCranialVol, eTIV, Estimated Total Intracranial Volume, 1500000.25, mm^3\n'
    text+='# ColHeaders Index SegId NVoxels Volume_mm3 StructName normMean normStdDev normMin normMax normRange\n'
    index=0
    for name in names[68:]:
        side,region=name[:-4].split('_',1)
        if alias and region=='Thalamus':region='Thalamus-Proper'
        text+=f'{index} {index+10} 10 {expected[name]} {side}-{region} 1 2 3 4 5\n';index+=1
    (folder/'aseg.stats').write_text(text)
    return names,expected


class VolumeInterfaceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.folder=Path(self.tmp.name)
        self.names,self.expected=fixtures(self.folder)
    def tearDown(self):self.tmp.cleanup()
    def test_all82_match_existing_peer_reader(self):
        ours,icv=volume.extract82(self.folder,self.names)
        peer,names=volumes82(*(self.folder/name for name in volume.STATS))
        self.assertEqual(names,self.names)
        self.assertEqual(ours,peer.tolist())
        self.assertEqual(ours,[self.expected[name] for name in self.names])
        self.assertEqual(icv,1500000.25)
    def test_old_thalamus_alias_is_compatible(self):
        fixtures(self.folder,alias=True)
        ours,_=volume.extract82(self.folder,self.names)
        peer,_=volumes82(*(self.folder/name for name in volume.STATS))
        self.assertEqual(ours,peer.tolist())
    def test_both_thalamus_aliases_rejected(self):
        with (self.folder/'aseg.stats').open('a') as stream:stream.write('99 99 1 100 Left-Thalamus-Proper 1 2 3 4 5\n')
        with self.assertRaisesRegex(ValueError,'ambiguous'):volume.extract82(self.folder,self.names)
    def test_duplicate_cortex_rejected(self):
        with (self.folder/'lh.aparc.stats').open('a') as stream:stream.write('bankssts 10 20 100 2 0.1 0 0 0 0\n')
        with self.assertRaisesRegex(ValueError,'Duplicate'):volume.extract82(self.folder,self.names)
    def test_icv_wrong_units_or_duplicate_rejected(self):
        p=self.folder/'aseg.stats';original=p.read_text()
        p.write_text(original.replace('mm^3','cm^3'))
        with self.assertRaisesRegex(ValueError,'units'):volume.etiv(p)
        p.write_text(original+'# Measure EstimatedTotalIntraCranialVol, eTIV, Estimated Total Intracranial Volume, 1500000.25, mm^3\n')
        with self.assertRaisesRegex(ValueError,'exactly one'):volume.etiv(p)
    def test_pending_csv_is_blocked_by_peer(self):
        values,icv=volume.extract82(self.folder,self.names);p=self.folder/'pending.csv'
        volume.write_csv(p,'SYNTHETIC_UNIT_TEST',self.names,values,icv,'8.2.0','pending')
        with self.assertRaisesRegex(ValueError,'QC pass'):volume_record(p,'SYNTHETIC_UNIT_TEST')
    def test_accepted_csv_columns_work_with_peer(self):
        values,icv=volume.extract82(self.folder,self.names);p=self.folder/'synthetic_pass.csv'
        volume.write_csv(p,'SYNTHETIC_UNIT_TEST',self.names,values,icv,'8.2.0','pass')
        array,names,meta=volume_record(p,'SYNTHETIC_UNIT_TEST')
        self.assertEqual(array.tolist(),values);self.assertEqual(names,self.names)
        self.assertEqual(meta['icv_mm3'],icv)
    def test_missing_region_rejected(self):
        p=self.folder/'rh.aparc.stats';p.write_text('\n'.join(l for l in p.read_text().splitlines() if not l.startswith('insula '))+'\n')
        with self.assertRaises(KeyError):volume.extract82(self.folder,self.names)


class ExecutionGuardTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def test_insufficient_memory_blocks_before_download(self):
        cfg=json.loads((ROOT/'configs/freesurfer_pilot.json').read_text())
        cfg['persistent_root']=str(self.root)
        fake={'os_id':'ubuntu','os_version':'24.04','architecture':'x86_64','avx_present':True,
              'effective_memory_gib':12.67,'free_disk_gib':100}
        with patch.object(runner,'runtime_info',return_value=fake),patch.object(runner.subprocess,'run') as call:
            with self.assertRaisesRegex(RuntimeError,'too small'):runner.install(cfg,True)
            call.assert_not_called()
    def test_install_requires_explicit_license_acceptance(self):
        with patch.object(runner.subprocess,'run') as call:
            with self.assertRaisesRegex(RuntimeError,'license'):runner.install({},False)
            call.assert_not_called()
    def test_stage_order_and_duplicate_job(self):
        with self.assertRaisesRegex(RuntimeError,'Previous'):runner.stage_allowed(self.root,'autorecon2')
        (self.root/'autorecon1.completed.json').write_text('{}')
        runner.stage_allowed(self.root,'autorecon2')
        (self.root/'autorecon2.running.json').write_text('{}')
        with self.assertRaisesRegex(RuntimeError,'job marker'):runner.stage_allowed(self.root,'autorecon2')
    def test_checkpoint_does_not_overwrite_different_file(self):
        a=self.root/'a';b=self.root/'b';a.write_bytes(b'SYNTHETIC_A');b.write_bytes(b'SYNTHETIC_B')
        with self.assertRaisesRegex(RuntimeError,'differing'):runner.copy_checked(a,b)
        self.assertEqual(b.read_bytes(),b'SYNTHETIC_B')
    def test_archive_path_traversal_rejected(self):
        archive=self.root/'bad.tar.gz'
        with tarfile.open(archive,'w:gz') as tar:
            item=tarfile.TarInfo('../outside.txt');item.size=1;tar.addfile(item,io.BytesIO(b'x'))
        destination=self.root/'out';destination.mkdir()
        with self.assertRaisesRegex(RuntimeError,'Unsafe'):runner.safe_extract(archive,destination,'SYNTHETIC')
        self.assertFalse((self.root/'outside.txt').exists())
    def test_finalize_cannot_auto_pass_qc(self):
        with self.assertRaisesRegex(RuntimeError,'accept'):volume.finalize({},'SYNTHETIC',self.root/'none','SYNTHETIC',False)
    def test_restore_uses_original_snapshot_owner(self):
        cfg={'persistent_root':str(self.root/'drive'),'project_root':str(self.root/'work'),'subject_id':'SYNTHETIC'}
        fp={'SYNTHETIC_FINGERPRINT':True}
        source=runner.persistent_run(cfg,'SOURCE');source.mkdir(parents=True)
        owner=runner.persistent_run(cfg,'OWNER');owner.mkdir(parents=True)
        archive=owner/'autorecon1.subject.tar.gz'
        with tarfile.open(archive,'w:gz') as tar:
            item=tarfile.TarInfo('SYNTHETIC/fixture.txt');payload=b'SYNTHETIC_ONLY';item.size=len(payload);tar.addfile(item,io.BytesIO(payload))
        (source/'run.json').write_text(json.dumps({'software_fingerprint':fp,'config':cfg}))
        marker={'exit_code':0,'snapshot':{'archive':archive.name,'owner_run_id':'OWNER','sha256':runner.digest(archive),'readback':'pass'}}
        (source/'autorecon1.completed.json').write_text(json.dumps(marker))
        def initialize(*args):
            run=runner.run_dir(cfg,'NEW');(run/'subjects').mkdir(parents=True);return run
        with patch.object(runner,'fingerprint',return_value=fp),patch.object(runner,'initialize',side_effect=initialize),patch('builtins.print'):
            runner.restore(cfg,'NEW','SOURCE','autorecon1')
        self.assertEqual((runner.run_dir(cfg,'NEW')/'subjects/SYNTHETIC/fixture.txt').read_bytes(),b'SYNTHETIC_ONLY')
        self.assertEqual(json.loads((runner.run_dir(cfg,'NEW')/'autorecon1.completed.json').read_text())['snapshot']['owner_run_id'],'OWNER')


if __name__=='__main__':unittest.main()
