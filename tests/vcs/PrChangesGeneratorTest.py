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
        res = self.generator.generate(Path(self.test_folder_with_fs_changes_only, ".pr_report_dotnet.json"))
        self.assertIsNone(res)

    def test_should_not_generate_change_from_location_where_no_file_system_changes_are_available(self):
        res = self.generator.generate(Path(self.test_folder_with_pr_report_only, ".pr_report_dotnet.json"))
        self.assertIsNone(res)

    def test_should_generate_changes_from__location_where_changes_are_available(self):
        pr_change = self.generator.generate(Path(self.test_folder_with_fs_and_pr_report, ".pr_report_dotnet.json"))

        self.assertEqual(1, len(pr_change.dependencies))
        self.assertEqual(Dependency("dotnet", "Hangfire.AspNetCore", "1.7.25"), pr_change.dependencies[0])
        self.assertEqual("b407fb0d-abbf-aaaa-aaaa-aaaaaaaaaaaa", pr_change.meterian_project_id)
        self.assertEqual(1, len(pr_change.filesystem_changes))
        self.assertEqual(self.git_changes[1], pr_change.filesystem_changes[0].rel_file_path)
        content = self.git_changes[1].split("/")[1].encode()
        self.assertEqual(content, pr_change.filesystem_changes[0].content)

    def __generate_test_dir(self) -> Path:
        dir = tempfile.mkdtemp(prefix="meterian_pr_")
        return Path(dir)

    def __generate_fs_change(self, path: Path) -> str:
        res = tempfile.mkstemp(dir=path)
        with os.fdopen(res[0], "w") as file:
            file.write("manifest.testproj")
            file.close()
        manifest = Path(res[1])
        manifest.rename(Path(manifest.parent, "manifest.testproj"))
        return "manifest.testproj"

    def __generate_pr_report(self, path: Path) -> str:
        res = tempfile.mkstemp(dir=path)
        with os.fdopen(res[0], "wb") as file:
            report = """{
  "url": "https://www.meterian.com/projects/?pid\u003db407fb0d-abbf-aaaa-aaaa-aaaaaaaaaaaa\u0026branch\u003dmain\u0026mode\u003deli",
  "autofix": {
    "applied": true,
    "modestring": "aggressive",
    "changes": [
    {
      "name": "Hangfire.AspNetCore",
      "version": "1.7.25",
      "language": "dotnet",
      "upgradedTo": "1.7.31",
      "upgradedAs": "patch",
      "reason": "stability",
      "live": true,
      "versions": {
        "latestPatch": "1.7.31",
        "latestMinor": "1.8.0-rc1"
      },
      "locations": [
        "%location%"
      ]
    }
    ]
  }
}"""
            report = report.replace("%location%", str(Path(path, "manifest.testproj")))
            file.write(report.encode("utf-8"))
            file.close()
        pr_report = Path(res[1])
        pr_report.rename(Path(pr_report.parent, ".pr_report_dotnet.json"))
        return ".pr_report_dotnet.json"

if __name__ == "__main__":
    unittest.main()