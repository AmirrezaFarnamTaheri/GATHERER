import unittest
import os
import tempfile
from pathlib import Path
from mergebot.config.loader import load_config
from mergebot.config.schema import AppConfig

class TestConfigLoader(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.config_path = Path(self.test_dir.name) / "config.yaml"

    def tearDown(self):
        self.test_dir.cleanup()

    def test_load_valid_config(self):
        config_content = """
        sources:
          - id: test_source
            type: telegram
            telegram:
              token: "123:ABC"
              chat_id: "-1001"
            selector:
              include_formats: ["all"]
        publishing:
          routes:
            - name: test_route
              from_sources: ["test_source"]
              formats: ["npvt"]
              destinations:
                - chat_id: "-1002"
                  mode: bundle
        """
        with open(self.config_path, "w") as f:
            f.write(config_content)

        config = load_config(self.config_path)
        self.assertIsInstance(config, AppConfig)
        self.assertEqual(len(config.sources), 1)
        self.assertEqual(config.sources[0].id, "test_source")
        self.assertEqual(len(config.routes), 1)
        self.assertEqual(config.routes[0].name, "test_route")

    def test_load_invalid_yaml(self):
        with open(self.config_path, "w") as f:
            f.write("invalid: yaml: [")

        with self.assertRaises(Exception):
            load_config(self.config_path)

    def test_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            load_config(Path("non_existent.yaml"))

if __name__ == '__main__':
    unittest.main()
