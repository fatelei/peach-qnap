import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("release", Path(__file__).resolve().parents[1] / "scripts/release.py")
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "qpkg.cfg").write_text('QPKG_VER="0.1.1"\n')

    def tearDown(self):
        self.temp.cleanup()

    def test_matching_tag(self):
        self.assertEqual(release.validate_tag("v0.1.1", self.root), "0.1.1")

    def test_mismatched_tag(self):
        with self.assertRaisesRegex(ValueError, "Update QPKG_VER"):
            release.validate_tag("v0.1.2", self.root)

    def test_invalid_tags(self):
        for tag in ("main", "0.1.1", "v01.1.1", "v0.1.1-rc1", "v0.1.1\n", "v0.1.1;echo bad"):
            with self.subTest(tag=tag), self.assertRaises(ValueError):
                release.validate_tag(tag, self.root)

    def test_qnap_version_field_limit(self):
        with self.assertRaisesRegex(ValueError, "10-character"):
            release.validate_tag("v1234.1234.1234", self.root)

    def test_invalid_package_rejected(self):
        path = self.root / "test.qpkg"
        path.write_bytes(b"not a QPKG")
        with self.assertRaisesRegex(ValueError, "footer"):
            release.verify_package(path, self.root)

    def test_incomplete_artifacts_rejected(self):
        with self.assertRaisesRegex(ValueError, "exactly one"):
            release.write_checksums(self.root)

    def test_portable_checksums(self):
        (self.root / "test.qpkg").write_bytes(b"abc")
        (self.root / "test-source.tar.gz").write_bytes(b"abc")
        release.write_checksums(self.root)
        text = (self.root / "SHA256SUMS.txt").read_text()
        self.assertNotIn(str(self.root), text)
        self.assertEqual(text.count("ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"), 2)


if __name__ == "__main__":
    unittest.main()
