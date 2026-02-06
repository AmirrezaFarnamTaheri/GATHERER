import unittest
import tempfile
import hashlib
import shutil
from pathlib import Path
from mergebot.store.raw_store import RawStore
from mergebot.store.artifact_store import ArtifactStore

class TestRawStore(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.store = RawStore(base_dir=Path(self.test_dir.name))

    def tearDown(self):
        self.test_dir.cleanup()

    def test_save_and_get(self):
        data = b"test data"
        # SHA256 of "test data"
        expected_hash = hashlib.sha256(data).hexdigest()

        saved_hash = self.store.save(data)
        self.assertEqual(saved_hash, expected_hash)

        # Verify get works
        retrieved_data = self.store.get(expected_hash)
        self.assertEqual(retrieved_data, data)
        self.assertTrue(self.store.exists(expected_hash))

    def test_get_nonexistent(self):
        # Just a random hash
        self.assertIsNone(self.store.get("f2ca1bb6c7e907d06dafe4687e579fce76b37e4e93b7605022da52e6ccc26fd2"))

class TestArtifactStore(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.test_dir.name) / "artifacts"
        self.output_dir = Path(self.test_dir.name) / "output"

        # Initialize store but we need to patch output_dir after init
        # because init uses imported constant.
        # Alternatively, we can mock the imported constant, but simply setting the attribute is easier.
        self.store = ArtifactStore(base_dir=self.base_dir)
        self.store.output_dir = self.output_dir

    def tearDown(self):
        self.test_dir.cleanup()

    def test_save_artifact_internal(self):
        data = b"artifact content"
        name = "test_route"
        expected_hash = hashlib.sha256(data).hexdigest()

        saved_hash = self.store.save_artifact(name, data)
        self.assertEqual(saved_hash, expected_hash)

        # Verify internal storage structure
        internal_path = self.base_dir / name / f"{expected_hash}.bin"
        self.assertTrue(internal_path.exists())
        self.assertEqual(internal_path.read_bytes(), data)

    def test_save_output_user_facing(self):
        data = b"user content"
        # Saves to output_dir/route1/route1.txt
        path_str = self.store.save_output("route1", "txt", data)

        path = Path(path_str)
        self.assertTrue(path.exists())
        self.assertEqual(path.read_bytes(), data)
        self.assertEqual(path.name, "route1.txt")
        # Check directory structure
        self.assertEqual(path.parent.name, "route1")

if __name__ == '__main__':
    unittest.main()
