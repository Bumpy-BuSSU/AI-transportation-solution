from pathlib import Path
import tempfile
import unittest

import pandas as pd
import yaml

from subway.tools.inspect_raw_inputs import run_inspection


DATASET_IDS = [
    "senior_ridership",
    "total_ridership",
    "weather",
    "station",
    "population",
    "boundary",
    "shelter",
]


class InspectRawInputsTests(unittest.TestCase):
    def _make_repo(self, root: Path, missing: str | None = None) -> None:
        config_dir = root / "subway" / "config"
        config_dir.mkdir(parents=True)
        datasets = {}
        for dataset_id in DATASET_IDS:
            rel = f"subway/data/raw/{{year}}/{dataset_id}"
            datasets[dataset_id] = {"raw_dir": rel}
            if dataset_id == missing:
                continue
            raw_dir = root / rel.format(year=2024)
            raw_dir.mkdir(parents=True)
            pd.DataFrame({"값": [1]}).to_csv(
                raw_dir / f"{dataset_id}.csv",
                index=False,
                encoding="utf-8-sig",
            )
        (config_dir / "datasets.yaml").write_text(
            yaml.safe_dump({"datasets": datasets}, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        manifest = root / "subway" / "data_manifest.csv"
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text(
            "dataset_id,year,dataset_name,provider,source_url,raw_path,reference_date,download_date,file_format,sha256,license,notes\n",
            encoding="utf-8",
        )

    def test_deterministic_outputs_and_manifest_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._make_repo(root)
            self.assertEqual(run_inspection(root, 2024), 0)

            validation = root / "subway" / "data" / "validation"
            outputs = [
                validation / "raw_inventory.csv",
                validation / "raw_schema_snapshot.json",
                validation / "raw_inspection_report.csv",
                validation / "raw_inspection_summary.json",
            ]
            first = {p.name: p.read_bytes() for p in outputs}
            import json
            summary = json.loads(
                (validation / "raw_inspection_summary.json").read_text(encoding="utf-8")
            )
            self.assertEqual(summary["status"], "RAW INSPECTION PASSED")

            manifest_path = root / "subway" / "data_manifest.csv"
            manifest = pd.read_csv(manifest_path, dtype=str, keep_default_na=False)
            manifest.loc[manifest["dataset_id"] == "weather", "provider"] = "기상청"
            manifest.to_csv(manifest_path, index=False, lineterminator="\n")

            self.assertEqual(run_inspection(root, 2024), 0)
            self.assertEqual(first, {p.name: p.read_bytes() for p in outputs})
            manifest2 = pd.read_csv(manifest_path, dtype=str, keep_default_na=False)
            self.assertEqual(
                manifest2.loc[manifest2["dataset_id"] == "weather", "provider"].iloc[0],
                "기상청",
            )

    def test_missing_dataset_returns_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._make_repo(root, missing="shelter")
            self.assertEqual(run_inspection(root, 2024), 1)
            report = pd.read_csv(
                root / "subway" / "data" / "validation" / "raw_inspection_report.csv"
            )
            matches = report[
                (report["dataset_id"] == "shelter")
                & (report["code"] == "MISSING_DATASET_DIRECTORY")
            ]
            self.assertEqual(len(matches), 1)
            self.assertEqual(matches.iloc[0]["severity"], "ERROR")
            import json
            summary = json.loads(
                (
                    root
                    / "subway"
                    / "data"
                    / "validation"
                    / "raw_inspection_summary.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual(summary["status"], "RAW INSPECTION FAILED")


if __name__ == "__main__":
    unittest.main()
