from pathlib import Path
import tempfile
import unittest

from subway.src.utils.paths import load_dataset_config, resolve_repo_relative


REQUIRED = {
    "senior_ridership",
    "total_ridership",
    "weather",
    "station",
    "population",
    "boundary",
    "shelter",
}


class PathsTests(unittest.TestCase):
    def test_loads_all_required_2024_dataset_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "datasets.yaml"
            config.write_text(
                "datasets:\n"
                + "\n".join(
                    f"  {dataset_id}:\n    raw_dir: subway/data/raw/{{year}}/{dataset_id}"
                    for dataset_id in sorted(REQUIRED)
                )
                + "\n",
                encoding="utf-8",
            )
            loaded = load_dataset_config(config, 2024)
            self.assertEqual(set(loaded), REQUIRED)
            for dataset_id, entry in loaded.items():
                self.assertEqual(entry["raw_dir"], f"subway/data/raw/2024/{dataset_id}")

    def test_rejects_absolute_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            absolute = str((repo_root / "elsewhere").resolve())
            with self.assertRaises(ValueError):
                resolve_repo_relative(repo_root, absolute)

    def test_rejects_path_traversal_outside_repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            with self.assertRaises(ValueError):
                resolve_repo_relative(repo_root, "../outside")

    def test_missing_dataset_id_is_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "datasets.yaml"
            ids = sorted(REQUIRED - {"shelter"})
            config.write_text(
                "datasets:\n"
                + "\n".join(
                    f"  {dataset_id}:\n    raw_dir: subway/data/raw/{{year}}/{dataset_id}"
                    for dataset_id in ids
                )
                + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "missing dataset ids"):
                load_dataset_config(config, 2024)


if __name__ == "__main__":
    unittest.main()
