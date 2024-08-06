import json
import re
import logging
import os

from urllib import parse
from typing import List
from pathlib import Path
from .PullRequestInterface import PullRequestInterface

class Dependency():
    def __init__(self, language: str, name: str, version: str, new_version: str) -> None:
        self.language = language
        self.name = name
        self.version = version
        self.new_version = new_version

    def to_payload(self):
        return {
            "dependency": {
                "library": {
                    "name": self.name,
                    "language": self.language
                },
                "version": self.version
            }
        }

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, Dependency):
            if self.language == __o.language and self.name == __o.name and self.version == __o.version and self.new_version == __o.new_version:
                return True
            else:
                return False
        else:
            return False
    
    def __hash__(self) -> int:
        return hash((str(self.language), str(self.name), str(self.version), str(self.new_version)))

    def __lt__(self, other):
        return (self.name+self.version) < (other.name+other.version)

    def __gt__(self, other):
        return (self.name+self.version) > (other.name+other.version)

    def __str__(self) -> str:
        return "Dependency [ language=" + str(self.language) + ", name=" + str(self.name) + ", version=" + str(self.version) + ", new_version=" + str(self.new_version) + "]"

class FilesystemChange():
    def __init__(self, rel_file_path: str, content: bytes) -> None:
        self.rel_file_path = rel_file_path
        self.content = content

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, FilesystemChange):
            if self.rel_file_path == __o.rel_file_path and self.content == __o.content:
                return True
            else:
                return False
        else:
            return False

    def __hash__(self) -> int:
        return hash((self.rel_file_path, self.content))

    def __lt__(self, other):
        return self.rel_file_path < other.rel_file_path

    def __gt__(self, other):
        return self.rel_file_path > other.rel_file_path

    def __str__(self) -> str:
        return "FilesystemChange [ file_path=" + str(self.rel_file_path) + ", content=" + str(self.content) + " ]"

class PrChange():
    def __init__(self,  meterian_project_id: str, dependencies : List[Dependency], filesystem_changes: List[FilesystemChange], pr_report: dict, manifest_info: dict, pr: PullRequestInterface = None) -> None:
        self.meterian_project_id = meterian_project_id
        self.dependencies = dependencies
        self.filesystem_changes = filesystem_changes
        self.pr_report = pr_report
        self.manifest_info = manifest_info
        self.pr = pr

    def set_pr(self, pr: PullRequestInterface):
        self.pr = pr

    def merge(self, other):
        if other is None:
            return

        for dep in other.dependencies:
            if dep not in self.dependencies:
                self.dependencies.append(dep)

        for fs_change in other.filesystem_changes:
            if fs_change not in self.filesystem_changes:
                self.filesystem_changes.append(fs_change)

        changes = self.__get_autofix_changes(self.pr_report)
        for change in self.__get_autofix_changes(other.pr_report):
            if change not in changes:
                changes.append(change)

    def __get_autofix_changes(self, report: dict):
        if report is None:
            return []

        if "autofix" in report and "changes" in report["autofix"]:
            return report["autofix"]["changes"]
        else:
            return []

    def __str__(self) -> str:
        dependencies_str = '[%s]' % ', '.join(map(str, self.dependencies)) if self.dependencies is not None else 'None'
        fs_changes_str = '[%s]' % ', '.join(map(str, self.filesystem_changes)) if self.filesystem_changes is not None else 'None'
        return "PrChange [ meterian_project_id=" + str(self.meterian_project_id) + ", dependencies=" + dependencies_str + ", filesystem_changes=" + fs_changes_str + ", pr_report=" + str(self.pr_report) + ", pr=" + str(self.pr) + " ]"

class PrChangesGenerator():

    __logger = logging.getLogger("PrChangesGenerator")

    METERIAN_PR_FILE_REGEX = r".*\.pr\d+$"

    METERIAN_PR_REPORT_FILE_REGEX = r"^report\.json\.pr\d+$"

    SUPPORTED_MANIFEST_FILES_PATTERNS = [ "^pom\.xml$", "^composer\.json$", "^Gemfile$", "^Gemfile\.lock$", "^Pipfile$", "^Pipfile\.lock$", "^package\.json$", "^package-lock\.json$", "^.*\..+proj$", "^yarn\.lock$", "^pyproject\.toml$", "^poetry\.lock$" ]

    def __init__(self, root_folder: Path, relative_changes_paths: List[str]) -> None:
        self.root_folder = root_folder
        self.relative_changes_paths = relative_changes_paths

    def generate(self, pr_report_file: Path) -> PrChange:
        if pr_report_file.exists():
            self.__logger.debug("Loading PR report %s", self.__relative_path(pr_report_file))
            pr_report = PrChangesGenerator.__load_report_json(pr_report_file)
            self.__logger.debug("Loaded PR report.")
            if pr_report:
                fs_changes = self.__collect_fs_changes()
                dependencies = self.__collect_dependencies(pr_report)
                project_id = PrChangesGenerator.__parse_project_id(pr_report)
                if fs_changes and dependencies and project_id:
                    manifest_info = self.__get_manifest_info(pr_report)
                    pr_change = PrChange(project_id, dependencies, fs_changes, pr_report, manifest_info)
                    self.__logger.debug("Generated PR change %s", str(pr_change))
                    return pr_change
                else:
                    self.__logger.debug("Incomplete data collected for PR change, generation will be aborted")
            else:
                self.__logger.debug("Could not load PR report, generation will be aborted")
        else:
            self.__logger.debug("PR report %s not found", self.__relative_path(pr_report_file))

        self.__logger.debug("Failed to generate PR change using %s", self.__relative_path(pr_report_file))
        return None

    def __get_manifest_info(self, pr_report):
        if "autofix" in pr_report:
            if "manifests" in pr_report["autofix"]:
                manifests = pr_report["autofix"]["manifests"]
                if manifests:
                    if len(manifests) > 0:
                        return manifests[0]
        return None

    def __relative_path(self, location: Path) -> str:
        return str(PrChangesGenerator.__compute_relative_path(self.root_folder, location))

    def __compute_relative_path(root_folder: Path, location: Path) -> Path:
        return location.relative_to(root_folder)

    def __collect_dependencies(self, pr_report: dict) -> List[Dependency]:
        deps = PrChangesGenerator.collect_dependencies_from_report(pr_report)
        return deps if len(deps) > 0 else None

    def collect_dependencies_from_report(pr_report: dict) -> List[Dependency]:
        # collect autofix dependencies
        deps = []
        for change in pr_report["autofix"]["changes"]:
            dep = Dependency(change["language"], change["name"], change["version"], change["upgradedTo"])
            deps.append(dep)
            PrChangesGenerator.__logger.debug("Collected dependency %s from autofix report", str(dep))
            
        return deps

    def __collect_fs_changes(self) -> List[FilesystemChange]:
        try:
            fs_changes = []
            for rel_change in self.relative_changes_paths:
                if PrChangesGenerator.__is_supported_manifest(Path(self.root_folder, PrChangesGenerator.__without_pr_file_extension(rel_change)).name):
                    content = self.__read_file_bytes(str(Path(self.root_folder, rel_change).absolute()))
                    fs_changes.append(FilesystemChange(PrChangesGenerator.__without_pr_file_extension(rel_change), content))
                    self.__logger.debug("Loaded manifest change for %s", str(rel_change))
            return fs_changes
        except:
            self.__logger.debug("Unable to collect filesystem changes from files %s", self.relative_changes_paths, exc_info=1)
            return None

    def __without_pr_file_extension(filename: str):
        pr_no = PrChangesGenerator.__parse_pr_no(Path(filename))
        if pr_no:
            return filename.replace("."+pr_no, "")
        else:
            return filename

    def __is_supported_manifest(file_name: str) -> bool:
        res = False

        for pattern in PrChangesGenerator.SUPPORTED_MANIFEST_FILES_PATTERNS:
            if re.match(pattern, file_name):
                res = True
                break

        return res

    def __read_file_bytes(self, path: str) -> bytes:
        file = open(path, "rb")
        bytes_contents = file.read()
        file.close()
        return bytes_contents

    def fetch_changed_manifests(root_dir: Path) -> dict:
        '''
        returns map with key(Path(pr_report)), value(List[str(file changes paths relative to root_dir)])
        '''
        manifests_by_pr_reports = {}
        reports = PrChangesGenerator.__fetch_pr_reports(root_dir)
        PrChangesGenerator.__logger.debug("Found PR reports to work on %s", str(reports))
        for report in reports:
            pr_no = PrChangesGenerator.__parse_pr_no(report)
            if pr_no:
                manifests_by_pr_reports[report] = PrChangesGenerator.__find_changed_manifests(root_dir, pr_no)

        PrChangesGenerator.__logger.debug("Fetched changed manifest by pr reports: %s", manifests_by_pr_reports)
        return manifests_by_pr_reports


    def __parse_pr_no(file: Path):
        pr_no = None
        if re.match(PrChangesGenerator.METERIAN_PR_FILE_REGEX, file.name):
            last_index_of_dot = file.name.rfind('.')
            if last_index_of_dot != -1:
                pr_no = file.name[last_index_of_dot+1:]
        return pr_no

    def fetch_pr_reports(work_dir: Path) -> List[Path]:
        return PrChangesGenerator.__fetch_pr_reports(work_dir)

    def __fetch_pr_reports(work_dir: Path) -> List[Path]:
        PrChangesGenerator.__logger.debug("Fetching PR reports in %s", str(work_dir))
        reports = []
        for filename in os.listdir(work_dir):
            PrChangesGenerator.__logger.debug("Checking %s", filename)
            if os.path.isfile(Path(work_dir,filename)) and re.match(PrChangesGenerator.METERIAN_PR_REPORT_FILE_REGEX, filename):
                reports.append(Path(work_dir, filename))
                PrChangesGenerator.__logger.debug("Loaded report @ %s", str(Path(work_dir, filename)))
        return reports

    def __find_changed_manifests(work_dir: Path, pr_no: str) -> List[str]:
        manifests = []
        for root, dirs, files in os.walk(work_dir):
            files = [f for f in files if f.endswith("."+pr_no)]
            for file in files:
                manifest_file = file.replace("."+pr_no, "");
                if PrChangesGenerator.__is_supported_manifest(manifest_file):
                    manifest = Path(root, file)
                    entry = str(PrChangesGenerator.__compute_relative_path(work_dir, manifest))
                    if entry not in manifests:
                        manifests.append(entry)
        return manifests

    def __load_report_json(path: Path) -> dict:
        try:
            stream = open(path, encoding="utf-8")
            pr_report = json.load(stream)
            stream.close()
            return pr_report
        except:
            PrChangesGenerator.__logger.debug("Unable to load PR report at %s", str(path), exc_info=1)
            return None

    def __parse_project_id(pr_report: dict) -> str:
        url_str = pr_report.get("url", None)
        try:
            url = parse.urlparse(url_str)
            query_str = parse.parse_qs(url.query)
            return query_str["pid"][0]
        except:
            PrChangesGenerator.__logger.debug("Unable to parse project ID from url %s in PR report ", str(url_str), exc_info=1)
            return None

    def parse_pid(a_report: Path) -> str:
        pid = None

        report = PrChangesGenerator.__load_report_json(a_report)
        if report:
            pid = PrChangesGenerator.__parse_project_id(report)

        return pid