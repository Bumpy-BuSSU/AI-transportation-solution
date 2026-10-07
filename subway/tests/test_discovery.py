from pathlib import Path
import hashlib
import tempfile
import unittest

from subway.src.ingest.discovery import discover_raw_files
from subway.src.utils.hashing import sha256_file


class DiscoveryTests(unittest.TestCase):
    def test_sha256_matches_hashlib(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.bin"
            payload = b"abc123\n"
            path.write_bytes(payload)
            self.assertEqual(sha256_file(path), hashlib.sha256(payload).hexdigest())

    def test_discovers_and_classifies_files_in_stable_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "z.csv").write_text("a\n1\n", encoding="utf-8")
            (root / "a.xlsx").write_bytes(b"xlsx")
            (root / "shape.shp").write_bytes(b"shp")
            (root / "shape.dbf").write_bytes(b"dbf")
            (root / "shape.shx").write_bytes(b"shx")
            (root / "shape.prj").write_text("prj", encoding="utf-8")
            (root / "notes.txt").write_text("x", encoding="utf-8")
            nested = root / "nested"
            nested.mkdir()
            (nested / "b.xls").write_bytes(b"xls")

            before = sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file())
            records = discover_raw_files("station", root)
            after = sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file())

            self.assertEqual(before, after)
            self.assertEqual([r.relative_path for r in records], sorted(before))
            roles = {r.filename: r.role for r in records}
            self.assertEqual(roles["z.csv"], "primary")
            self.assertEqual(roles["a.xlsx"], "primary")
            self.assertEqual(roles["b.xls"], "primary")
            self.assertEqual(roles["shape.shp"], "primary")
            self.assertEqual(roles["shape.dbf"], "sidecar")
            self.assertEqual(roles["shape.shx"], "sidecar")
            self.assertEqual(roles["shape.prj"], "sidecar")
            self.assertEqual(roles["notes.txt"], "unsupported")

            for record in records:
                self.assertEqual(record.dataset_id, "station")
                self.assertEqual(record.extension, Path(record.filename).suffix.lower())
                self.assertGreaterEqual(record.size_bytes, 0)
                self.assertEqual(len(record.sha256), 64)


if __name__ == "__main__":
    unittest.main()
