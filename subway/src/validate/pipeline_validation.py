from pathlib import Path
import json

import pandas as pd
import yaml

from subway.src.ingest.discovery import discover_raw_files
from subway.src.ingest.schema_inspector import inspect_primary_file
from subway.src.utils.paths import REQUIRED_DATASET_IDS, load_dataset_config, resolve_repo_relative
from subway.src.validate.raw_validation import Finding


def pipeline_status(findings: list[Finding]) -> tuple[str, int]:
    if any(f.severity == 'ERROR' for f in findings):
        return 'PIPELINE FAILED', 1
    if any(f.severity == 'WARNING' for f in findings):
        return 'PIPELINE PASSED WITH WARNINGS', 0
    return 'PIPELINE PASSED', 0


def validate_frame(frame: pd.DataFrame, dataset_id: str, rules: dict) -> list[Finding]:
    findings = []
    for name in rules.get('required', []):
        if name not in frame:
            findings.append(Finding('ERROR', dataset_id, 'MISSING_COLUMN', name))
        elif (frame[name].isna() | frame[name].astype('string').str.strip().eq('').fillna(False)).any():
            findings.append(Finding('ERROR', dataset_id, 'MANDATORY_NULL', name))
    keys = rules.get('unique_key', [])
    if keys and all(k in frame for k in keys) and frame.duplicated(keys, keep=False).any():
        findings.append(Finding('ERROR', dataset_id, 'LOGICAL_DUPLICATE', ','.join(keys)))
    for name in rules.get('nonnegative', []):
        if name in frame and pd.to_numeric(frame[name], errors='coerce').lt(0).any():
            findings.append(Finding('ERROR', dataset_id, 'NEGATIVE_VALUE', name))
    return findings


def _schema_matches(schema: dict, contract: dict) -> bool:
    if not schema.get('loadable') or schema.get('format') != contract.get('format'):
        return False
    actual = schema
    if contract['format'] in {'spreadsheetml', 'excel'}:
        if contract.get('selected_sheet') not in schema.get('sheets', {}):
            return False
        actual = schema['sheets'][contract['selected_sheet']]
    for key in ['columns', 'row_count', 'title_row_count']:
        if key in contract and actual.get(key) != contract[key]:
            return False
    for key in ['encoding', 'crs', 'geometry_types', 'worksheet_names']:
        if key in contract and schema.get(key) != contract[key]:
            return False
    return True


def preflight(repo_root: Path, year: int) -> list[Finding]:
    """Compare current Raw to recorded evidence; never rewrite the manifest/baseline."""
    repo_root = repo_root.resolve()
    config_dir = repo_root / 'subway/config'
    findings = []
    try:
        datasets = load_dataset_config(config_dir / 'datasets.yaml', year)
        contract_doc = yaml.safe_load((config_dir / f'source_contracts_{year}.yaml').read_text(encoding='utf-8'))
        rules = yaml.safe_load((config_dir / 'validation_rules.yaml').read_text(encoding='utf-8'))
        if not isinstance(rules, dict) or rules.get('schema_version') != 1 or rules.get('year') != year:
            raise ValueError('unsupported validation configuration version/year')
        if not isinstance(contract_doc, dict) or contract_doc.get('year') != year:
            raise ValueError('contract year mismatch')
        contracts = contract_doc.get('contracts')
        if not isinstance(contracts, dict) or set(contracts) != REQUIRED_DATASET_IDS:
            raise ValueError('contract dataset IDs mismatch')
        validation = repo_root / 'subway/data/validation'
        snapshot = json.loads((validation / 'raw_schema_snapshot.json').read_text(encoding='utf-8'))
        inventory = pd.read_csv(validation / 'raw_inventory.csv', dtype=str, keep_default_na=False)
        manifest = pd.read_csv(repo_root / 'subway/data_manifest.csv', dtype=str, keep_default_na=False)
        if not {'dataset_id', 'relative_path', 'sha256', 'size_bytes', 'role'}.issubset(inventory.columns):
            raise ValueError('inventory columns missing')
        if not {'dataset_id', 'year', 'raw_path', 'sha256'}.issubset(manifest.columns):
            raise ValueError('manifest columns missing')
        if inventory.duplicated(['dataset_id', 'relative_path']).any() or manifest.duplicated(['dataset_id', 'year', 'raw_path']).any():
            raise ValueError('authoritative inventory/manifest duplicate')
    except (OSError, ValueError, TypeError, KeyError, yaml.YAMLError) as exc:
        return [Finding('ERROR', 'pipeline', 'CONFIGURATION_ERROR', str(exc))]

    for dataset_id in sorted(datasets):
        contract = contracts[dataset_id]
        if (not isinstance(contract, dict) or not {'primary_file', 'format', 'columns', 'row_count'}.issubset(contract)
                or contract.get('format') not in {'csv', 'spreadsheetml', 'excel', 'shapefile'}):
            findings.append(Finding('ERROR', dataset_id, 'CONFIGURATION_ERROR', 'unsupported or incomplete source contract'))
            continue
        try:
            directory = resolve_repo_relative(repo_root, datasets[dataset_id]['raw_dir'])
            records = discover_raw_files(dataset_id, directory)
            old = inventory[inventory['dataset_id'] == dataset_id]
            expected = {row['relative_path']: row for _, row in old.iterrows()}
            if {r.relative_path for r in records} != set(expected):
                findings.append(Finding('ERROR', dataset_id, 'RAW_INVENTORY_DRIFT', 'Raw file set differs from baseline'))
            for record in records:
                previous = expected.get(record.relative_path)
                if previous is None or record.sha256 != previous['sha256'] or record.size_bytes != int(previous['size_bytes']):
                    findings.append(Finding('ERROR', dataset_id, 'RAW_HASH_DRIFT', 'Raw bytes differ from recorded inventory', record.relative_path))
            primary = [r for r in records if r.role == 'primary']
            if len(primary) != 1 or primary[0].relative_path != contract['primary_file']:
                findings.append(Finding('ERROR', dataset_id, 'CONTRACT_FILE_MISMATCH', 'required primary file differs'))
                continue
            record = primary[0]
            relative_path = f"{datasets[dataset_id]['raw_dir']}/{record.relative_path}"
            rows = manifest[(manifest['dataset_id'] == dataset_id) & (manifest['year'] == str(year)) & (manifest['raw_path'] == relative_path)]
            if len(rows) != 1 or rows.iloc[0]['sha256'] != record.sha256:
                findings.append(Finding('ERROR', dataset_id, 'MANIFEST_HASH_MISMATCH', 'manifest does not match Raw', record.relative_path))
            previous_schema = snapshot.get(f'{dataset_id}/{record.relative_path}', {})
            if not _schema_matches(previous_schema, contract):
                findings.append(Finding('ERROR', dataset_id, 'CONTRACT_BASELINE_MISMATCH', 'contract differs from Stage 1 schema', record.relative_path))
            current_schema = inspect_primary_file(resolve_repo_relative(repo_root, relative_path))
            if not _schema_matches(current_schema, contract):
                findings.append(Finding('ERROR', dataset_id, 'SOURCE_SCHEMA_DRIFT', 'current source differs from contract', record.relative_path))
        except (OSError, ValueError, TypeError, KeyError) as exc:
            findings.append(Finding('ERROR', dataset_id, 'CONFIGURATION_ERROR', str(exc)))
    return sorted(findings, key=lambda f: (f.dataset_id, f.code, f.relative_path))
