import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd
import yaml

from subway.src.clean.contracts import StageResult
from subway.src.ingest.schema_inspector import inspect_primary_file
from subway.src.utils.artifacts import write_artifacts
from subway.src.utils.hashing import sha256_file
from subway.src.utils.paths import REQUIRED_DATASET_IDS
from subway.src.validate.raw_validation import Finding
from subway.src.validate.pipeline_validation import preflight, pipeline_status, validate_frame


class PipelineContractsTests(unittest.TestCase):
    def make_repo(self, root):
        (root / 'subway/config').mkdir(parents=True)
        (root / 'subway/data/validation').mkdir(parents=True)
        datasets, contracts, snapshot, inventory, manifest = {}, {}, {}, [], []
        for name in sorted(REQUIRED_DATASET_IDS):
            directory = root / f'subway/data/raw/2024/{name}'
            directory.mkdir(parents=True)
            path = directory / f'{name}.csv'
            path.write_bytes(b'id\n1\n')
            datasets[name] = {'raw_dir': f'subway/data/raw/{{year}}/{name}'}
            contracts[name] = {'primary_file': path.name, 'format': 'csv', 'encoding': 'utf-8-sig', 'columns': ['id'], 'row_count': 1}
            snapshot[f'{name}/{path.name}'] = inspect_primary_file(path)
            record = {'dataset_id': name, 'relative_path': path.name, 'filename': path.name, 'extension': '.csv', 'size_bytes': path.stat().st_size, 'sha256': sha256_file(path), 'role': 'primary'}
            inventory.append(record)
            manifest.append({'dataset_id': name, 'year': 2024, 'raw_path': path.relative_to(root).as_posix(), 'sha256': record['sha256']})
        config = root / 'subway/config'
        (config / 'datasets.yaml').write_text(yaml.safe_dump({'datasets': datasets}), encoding='utf-8')
        (config / 'source_contracts_2024.yaml').write_text(yaml.safe_dump({'year': 2024, 'contracts': contracts}), encoding='utf-8')
        (config / 'validation_rules.yaml').write_text('schema_version: 1\nyear: 2024\n', encoding='utf-8')
        validation = root / 'subway/data/validation'
        (validation / 'raw_schema_snapshot.json').write_text(json.dumps(snapshot), encoding='utf-8')
        pd.DataFrame(inventory).to_csv(validation / 'raw_inventory.csv', index=False)
        pd.DataFrame(manifest).to_csv(root / 'subway/data_manifest.csv', index=False)
        return root / 'subway/data/raw/2024/weather/weather.csv'

    def test_preflight_valid_and_input_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); raw = self.make_repo(root)
            before = {p: p.read_bytes() for p in root.rglob('*') if p.is_file()}
            self.assertEqual(preflight(root, 2024), [])
            self.assertEqual(before, {p: p.read_bytes() for p in before})

    def test_hash_drift_and_manifest_not_rewritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); raw = self.make_repo(root)
            manifest = (root / 'subway/data_manifest.csv').read_bytes()
            raw.write_bytes(b'id\n2\n')
            self.assertIn('RAW_HASH_DRIFT', {f.code for f in preflight(root, 2024)})
            self.assertEqual((root / 'subway/data_manifest.csv').read_bytes(), manifest)

    def test_required_header_and_authoritative_snapshot_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); raw = self.make_repo(root)
            raw.write_bytes(b'other\n1\n')
            self.assertIn('SOURCE_SCHEMA_DRIFT', {f.code for f in preflight(root, 2024)})

    def test_contract_snapshot_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.make_repo(root)
            p = root / 'subway/config/source_contracts_2024.yaml'
            c = yaml.safe_load(p.read_text()); c['contracts']['weather']['columns'] = ['wrong']
            p.write_text(yaml.safe_dump(c))
            self.assertIn('CONTRACT_BASELINE_MISMATCH', {f.code for f in preflight(root, 2024)})

    def test_contract_year_missing_and_unsupported_configuration(self):
        for failure in ['year', 'missing', 'version']:
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp); self.make_repo(root)
                p = root / 'subway/config/validation_rules.yaml'
                if failure == 'missing': p.unlink()
                elif failure == 'version': p.write_text('schema_version: 99\nyear: 2024\n')
                else:
                    p = root / 'subway/config/source_contracts_2024.yaml'
                    c = yaml.safe_load(p.read_text()); c['year'] = 2025; p.write_text(yaml.safe_dump(c))
                self.assertTrue(any(f.severity == 'ERROR' for f in preflight(root, 2024)))

    def test_pipeline_statuses_and_unknown_metadata(self):
        self.assertEqual(pipeline_status([]), ('PIPELINE PASSED', 0))
        self.assertEqual(pipeline_status([Finding('INFO','x','I','info')]), ('PIPELINE PASSED', 0))
        warning = Finding('WARNING','x','W','warning')
        self.assertEqual(pipeline_status([warning]), ('PIPELINE PASSED WITH WARNINGS', 0))
        self.assertEqual(pipeline_status([warning, Finding('ERROR','x','E','error')]), ('PIPELINE FAILED', 1))
        result = StageResult(pd.DataFrame({'crs': [None]}), [], pd.DataFrame())
        self.assertIsNone(result.frame.loc[0, 'crs'])

    def test_generic_validation(self):
        frame = pd.DataFrame({'id': ['x', 'x', None], 'value': [1, -1, None]})
        findings = validate_frame(frame, 'fixture', {'required': ['id', 'value'], 'unique_key': ['id'], 'nonnegative': ['value']})
        self.assertTrue({'MANDATORY_NULL', 'LOGICAL_DUPLICATE', 'NEGATIVE_VALUE'}.issubset({f.code for f in findings}))

    def test_artifact_serialization_and_empty_header(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            frame = pd.DataFrame({'id': pd.Series(['b','a'],dtype='string'), 'value': pd.Series([None, 1],dtype='Int64')})
            empty = pd.DataFrame(columns=['severity','dataset_id','code','message','relative_path'])
            summary = {'year': 2024, 'crs': None, 'status': 'partial'}
            frames = {'values.csv': frame, 'values.parquet': frame, 'empty.csv': empty}
            first = write_artifacts(root, frames, summary)
            before = {p.name:p.read_bytes() for p in root.iterdir()}
            second = write_artifacts(root, {k:v.iloc[::-1] for k,v in frames.items()}, summary)
            self.assertEqual(first, second)
            self.assertEqual(before, {p.name:p.read_bytes() for p in root.iterdir()})
            self.assertEqual((root/'empty.csv').read_bytes(), b'severity,dataset_id,code,message,relative_path\n')
            self.assertNotIn(b'\r', (root/'values.csv').read_bytes())
            self.assertIsNone(json.loads((root/'pipeline_summary.json').read_text())['crs'])
            pd.testing.assert_frame_equal(pd.read_parquet(root/'values.parquet'), frame.iloc[::-1].reset_index(drop=True))

    def test_artifacts_reject_absolute_paths_and_runtime_timestamp(self):
        with tempfile.TemporaryDirectory() as tmp:
            for payload in [{'source_file': 'C:/Users/private/raw.csv'}, {'execution_timestamp': '2026-10-06T01:00:00'}]:
                with self.subTest(payload=payload), self.assertRaises(ValueError):
                    write_artifacts(Path(tmp), {}, payload)

    def test_null_empty_and_mixed_types_sort_deterministically(self):
        frames = {'nullable.parquet': pd.DataFrame({'name': pd.Series(['', pd.NA], dtype='string'), 'value': [1, 1]}),
                  'mixed.csv': pd.DataFrame({'value': pd.Series([1, '1', None, ''], dtype=object)})}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = write_artifacts(root, frames, {})
            second = write_artifacts(root, {k: v.iloc[::-1] for k, v in frames.items()}, {})
            self.assertEqual(first, second)

    def test_native_ordering_with_declared_unique_sort_columns(self):
        frame=pd.DataFrame({'source_row_id':pd.Series([3,1,2],dtype='Int64'),
                            'count':pd.Series([0,pd.NA,5],dtype='Int64'),
                            'name':pd.Series(['C','A','B'],dtype='string')})
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(pd.DataFrame,'itertuples',side_effect=AssertionError('row-wise Python sorting forbidden')):
                first=write_artifacts(Path(tmp),{'values.parquet':frame},{},sort_columns={'values.parquet':['source_row_id']})
                second=write_artifacts(Path(tmp),{'values.parquet':frame.iloc[::-1]},{},sort_columns={'values.parquet':['source_row_id']})
            self.assertEqual(first,second)
            self.assertEqual(pd.read_parquet(Path(tmp)/'values.parquet').source_row_id.tolist(),[1,2,3])
            for keys in [['unknown'],[],['name','name']]:
                with self.subTest(keys=keys),self.assertRaises(ValueError):
                    write_artifacts(Path(tmp),{'values.csv':frame},{},sort_columns={'values.csv':keys})
            tied=frame.copy(); tied['source_row_id']=1
            with self.assertRaises(ValueError):
                write_artifacts(Path(tmp),{'values.csv':tied},{},sort_columns={'values.csv':['source_row_id']})

    def test_native_default_ordering_and_explicit_null_last(self):
        frame=pd.DataFrame({'count':pd.Series([2,pd.NA,1],dtype='Int64'),
                            'name':pd.Series(['B','C','A'],dtype='string')})
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(pd.DataFrame,'itertuples',side_effect=AssertionError('row-wise Python sorting forbidden')):
                first=write_artifacts(Path(tmp),{'values.parquet':frame},{})
                second=write_artifacts(Path(tmp),{'values.parquet':frame.iloc[::-1]},{})
            self.assertEqual(first,second)
            loaded=pd.read_parquet(Path(tmp)/'values.parquet')
            self.assertEqual(loaded['count'].iloc[:2].tolist(),[1,2])
            self.assertTrue(pd.isna(loaded['count'].iloc[-1]))

    def test_geoparquet_ordering_preserves_geometry_and_crs(self):
        import geopandas as gpd
        from shapely.geometry import Point
        frame=gpd.GeoDataFrame({'id':['b','a']},geometry=[Point(1,2),Point(3,4)],crs='EPSG:4326')
        with tempfile.TemporaryDirectory() as tmp:
            first=write_artifacts(Path(tmp),{'geo.parquet':frame},{})
            second=write_artifacts(Path(tmp),{'geo.parquet':frame.iloc[::-1]},{})
            self.assertEqual(first,second)
            loaded=gpd.read_parquet(Path(tmp)/'geo.parquet')
            self.assertEqual(loaded.crs,frame.crs)
            self.assertEqual(loaded.geometry.to_wkb().tolist(),frame.iloc[::-1].geometry.to_wkb().tolist())

    def test_signed_zero_order_is_deterministic_and_values_preserved(self):
        import numpy as np
        for dtype in ['float64','Float64','float32']:
            with self.subTest(dtype=dtype),tempfile.TemporaryDirectory() as tmp:
                frame=pd.DataFrame({'value':pd.Series([0.0,-0.0,None],dtype=dtype)})
                root=Path(tmp); frames={'zeros.csv':frame,'zeros.parquet':frame}
                first=write_artifacts(root,frames,{})
                second=write_artifacts(root,{k:v.iloc[::-1] for k,v in frames.items()},{})
                self.assertEqual(first,second)
                loaded=pd.read_parquet(root/'zeros.parquet')
                self.assertEqual(np.signbit(loaded.value.iloc[:2].to_numpy(dtype=float)).tolist(),[False,True])
                self.assertTrue(pd.isna(loaded.value.iloc[-1]))

    def test_missing_format_metadata_is_configuration_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.make_repo(root)
            p = root / 'subway/config/source_contracts_2024.yaml'
            doc = yaml.safe_load(p.read_text()); del doc['contracts']['weather']['encoding']
            p.write_text(yaml.safe_dump(doc))
            self.assertIn('CONFIGURATION_ERROR', {f.code for f in preflight(root, 2024)})

    def test_malformed_configuration_and_snapshot_are_findings(self):
        for failure in ['datasets', 'snapshot', 'schema', 'sheets']:
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp); self.make_repo(root)
                if failure == 'datasets':
                    (root/'subway/config/datasets.yaml').write_text('- invalid\n')
                else:
                    p = root/'subway/data/validation/raw_schema_snapshot.json'
                    doc = json.loads(p.read_text())
                    if failure == 'snapshot': doc = []
                    elif failure == 'schema': doc['weather/weather.csv'] = []
                    else:
                        doc['weather/weather.csv'].update({'format':'spreadsheetml', 'sheets': []})
                        cpath = root/'subway/config/source_contracts_2024.yaml'
                        contracts = yaml.safe_load(cpath.read_text())
                        contracts['contracts']['weather'].update({'format':'spreadsheetml', 'selected_sheet':'data', 'worksheet_names':['data'], 'title_row_count':0})
                        cpath.write_text(yaml.safe_dump(contracts))
                    p.write_text(json.dumps(doc))
                self.assertTrue(any(f.severity == 'ERROR' for f in preflight(root, 2024)))


if __name__ == '__main__':
    unittest.main()
