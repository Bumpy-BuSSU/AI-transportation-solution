import hashlib
import json
from pathlib import Path
import unittest
import pandas as pd
from subway.src.utils.paths import REQUIRED_DATASET_IDS, load_dataset_config
from subway.src.validate.pipeline_validation import preflight

ROOT=Path(__file__).resolve().parents[2]
SHA='e48f83ca75f7f92a5a83e39834440c0f3149ace1113c3533102797e4d0338d76'
RAW='subway/data/raw/2024/population_direct_65_plus/201_DT_201004_O020003_2024Q2_20261006.csv'

class BaselineExtensionTests(unittest.TestCase):
    def test_approved_eighth_dataset_required_and_preflight_clean(self):
        self.assertIn('population_direct_65_plus', REQUIRED_DATASET_IDS)
        self.assertEqual(len(load_dataset_config(ROOT/'subway/config/datasets.yaml',2024)),8)
        self.assertEqual(preflight(ROOT,2024),[])

    def test_exact_new_raw_and_original_eleven_hashes(self):
        path=ROOT/RAW
        self.assertTrue(path.is_file())
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),SHA)
        old=json.loads((ROOT/'subway/data/validation/batch2r_station_blocker_summary.json').read_text(encoding='utf-8'))['verification']['raw_hashes']
        self.assertEqual(len(old),11)
        for name,expected in old.items():
            self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),expected,name)
        inv=pd.read_csv(ROOT/'subway/data/validation/raw_inventory.csv')
        self.assertEqual(len(inv),12)
        self.assertEqual(inv.dataset_id.nunique(),8)
        manifest=pd.read_csv(ROOT/'subway/data_manifest.csv',dtype=str,keep_default_na=False)
        row=manifest[manifest.dataset_id.eq('population_direct_65_plus')]
        self.assertEqual(len(row),1)
        self.assertEqual(row.sha256.iloc[0],SHA)
        self.assertEqual(row.reference_date.iloc[0],'2024-06-30')
        self.assertTrue(row.license.iloc[0])

if __name__=='__main__':unittest.main()
