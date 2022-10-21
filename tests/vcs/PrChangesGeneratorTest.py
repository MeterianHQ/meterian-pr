import unittest
import os, tempfile
from pathlib import Path
from src.vcs.PrChangesGenerator import Dependency, PrChangesGenerator
import shutil

class PrChangesGeneratorTest(unittest.TestCase):
    
    def setUp(self) -> None:
        self.test_folder = self.__generate_test_dir()
        self.test_folder_with_pr_report_only = Path(self.test_folder, "pr_report_only")
        self.test_folder_with_pr_report_only.mkdir(exist_ok=True)
        self.test_folder_with_fs_changes_only = Path(self.test_folder, "fs_changes_only")
        self.test_folder_with_fs_changes_only.mkdir(exist_ok=True)
        self.test_folder_with_fs_and_pr_report = Path(self.test_folder, "pr_and_fs_changes")
        self.test_folder_with_fs_and_pr_report.mkdir(exist_ok=True)

        self.__generate_pr_report(self.test_folder_with_pr_report_only)
        self.__generate_pr_report(self.test_folder_with_fs_and_pr_report)
        self.git_changes = [
            self.test_folder_with_fs_changes_only.name + "/" + self.__generate_fs_change(self.test_folder_with_fs_changes_only),
            self.test_folder_with_fs_and_pr_report.name + "/" + self.__generate_fs_change(self.test_folder_with_fs_and_pr_report)
        ]

        self.generator = PrChangesGenerator(Path(self.test_folder), self.git_changes)

    def tearDown(self) -> None:
        shutil.rmtree(self.test_folder)

    def test_should_not_generate_change_from_location_where_no_pr_report_is_available(self):
        res = self.generator.generate(self.test_folder_with_fs_changes_only)
        self.assertIsNone(res)

    def test_should_not_generate_change_from_location_where_no_file_system_changes_are_available(self):
        res = self.generator.generate(self.test_folder_with_pr_report_only)
        self.assertIsNone(res)

    def test_should_generate_changes_from__location_where_changes_are_available(self):
        pr_change = self.generator.generate(self.test_folder_with_fs_and_pr_report)

        self.assertEqual(1, len(pr_change.dependencies))
        self.assertEqual(Dependency("nodejs", "minimist", "1.1.1"), pr_change.dependencies[0])
        self.assertEqual("b407fb0d-abbf-aaaa-aaaa-aaaaaaaaaaaa", pr_change.meterian_project_id)
        self.assertEqual(1, len(pr_change.filesystem_changes))
        self.assertEqual(self.git_changes[1], pr_change.filesystem_changes[0].rel_file_path)
        content = self.git_changes[1].split("/")[1].encode()
        self.assertEqual(content, pr_change.filesystem_changes[0].content)

    def __generate_test_dir(self) -> Path:
        dir = tempfile.mkdtemp(prefix="meterian_pr_")
        return Path(dir)

    def __generate_fs_change(self, path: Path) -> str:
        res = tempfile.mkstemp(prefix="manifest_", dir=path, suffix=".testproj")
        with os.fdopen(res[0], "w") as file:
            file.write(str(Path(res[1]).name))
            file.close()
        return str(Path(res[1]).name)

    def __generate_pr_report(self, path: Path) -> str:
        res = tempfile.mkstemp(dir=path)
        with os.fdopen(res[0], "wb") as file:
            file.write("""{
  "url": "https://www.meterian.com/projects/?pid\u003db407fb0d-abbf-aaaa-aaaa-aaaaaaaaaaaa\u0026branch\u003dmain\u0026mode\u003deli",
  "reports": {
    "licensing": {
      "reports": [
        {
          "language": "nodejs",
          "results": [
            {
              "name": "minimist",
              "version": "1.1.1",
              "warnings": [],
              "violations": [],
              "licenses": [
                {
                  "id": "MIT",
                  "name": "MIT License",
                  "uri": "https://spdx.org/licenses/MIT.html",
                  "wildcard": false
                }
              ]
            },
            {
              "name": "path-parse",
              "version": "1.0.6",
              "warnings": [],
              "violations": [],
              "licenses": [
                {
                  "id": "MIT",
                  "name": "MIT License",
                  "uri": "https://spdx.org/licenses/MIT.html",
                  "wildcard": false
                }
              ]
            },
            {
              "name": "sample",
              "version": "1.0.0",
              "warnings": [],
              "violations": [],
              "licenses": [
                {
                  "id": "MIT",
                  "name": "MIT License",
                  "uri": "https://spdx.org/licenses/MIT.html",
                  "wildcard": false
                }
              ]
            }
          ],
          "warningsCount": 0,
          "violationsCount": 0
        }
      ],
      "warningsCount": 0,
      "violationsCount": 0,
      "score": 100
    }
  },
  "autofix": {
    "applied": true,
    "modestring": "aggressive",
    "changes": [
      {
        "name": "minimist",
        "version": "1.1.1",
        "upgradedTo": "1.2.7",
        "upgradedAs": "minor",
        "reason": "stability",
        "live": true,
        "versions": {
          "latestMinor": "1.2.7"
        }
      }
    ]
  }
}""".encode("utf-8"))
            file.close()
        pr_report = Path(res[1])
        pr_report.rename(Path(pr_report.parent, ".pr_report.json"))
        return str(pr_report.name)

if __name__ == "__main__":
    unittest.main()