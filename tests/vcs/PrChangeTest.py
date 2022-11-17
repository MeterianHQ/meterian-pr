import unittest
from src.vcs.PrChangesGenerator import Dependency, PrChange, FilesystemChange

class PrChangeTest(unittest.TestCase):

    def test_should_merge_pr_change(self):
        changeOne = PrChange(
            "uuid",
            [ Dependency("dotnet", "System.Net.Http", "4.3.0", "4.3.4") ],
            [ FilesystemChange("src/mylibs/alpha.csproj", b"content") ],
            self.__create_report(Dependency("dotnet", "System.Net.Http", "4.3.0", "4.3.4")),
            None
        )
        changeTwo = PrChange(
            "uuid",
            [ Dependency("dotnet", "System.Text.RegularExpressions", "4.3.0", "4.3.4") ],
            [ FilesystemChange("src/mylib/beta.csproj", b"content") ],
            self.__create_report(Dependency("dotnet", "System.Text.RegularExpressions", "4.3.0", "4.3.4")),
            None
        )

        changeOne.merge(changeTwo)

        self.assertEqual(2, len(changeOne.dependencies))
        self.assertTrue(Dependency("dotnet", "System.Text.RegularExpressions", "4.3.0", "4.3.4") in changeOne.dependencies)
        self.assertEqual(2, len(changeOne.filesystem_changes))
        self.assertTrue(FilesystemChange("src/mylib/beta.csproj", b"content") in changeOne.filesystem_changes)
        self.__assert_change_present_in_autofix("System.Text.RegularExpressions", "4.3.0", changeOne.pr_report["autofix"]["changes"])

    def __assert_change_present_in_autofix(self, dep_name, dep_version, changes):
        for change in changes:
            if dep_name == change["name"] and dep_version == change["version"]:
                return

        self.fail(f"Change {dep_name}@{dep_version} was not found!")


    def __create_report(self, dep: Dependency) -> dict:
        return {
            "autofix": {
                "applied": True,
                "modestring": "safe+vulns,safe+dated",
                "changes": [
                    {
                        "name": dep.name,
                        "version": dep.version,
                        "upgradedTo": "4.3.4",
                        "upgradedAs": "patch",
                        "reason": "security",
                        "live": True,
                        "versions": {
                            "latestPatch": "4.3.4"
                        },
                        "advisories": [
                            {
                                "id": "3fbb34a8-ee91-4774-a059-d545aaaaaaaa",
                                "library": {
                                    "name": dep.name,
                                    "language": dep.language
                                }
                            }
                        ]
                    }
                ]
            }
        }

if __name__ == "__main__":
    unittest.main()