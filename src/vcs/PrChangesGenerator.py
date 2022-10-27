import os
import json
import re
import logging

from urllib import parse
from typing import List
from pathlib import Path
from .PullRequestInterface import PullRequestInterface

class Dependency():
    def __init__(self, language: str, name: str, version: str) -> None:
        self.language = language
        self.name = name
        self.version = version

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
            if self.language == __o.language and self.name == __o.name and self.version == __o.version:
                return True
            else:
                return False
        else:
            return False
    
    def __hash__(self) -> int:
        return hash((str(self.language), str(self.name), str(self.version)))

    def __str__(self) -> str:
        return "Dependency [ language=" + str(self.language) + ", name=" + str(self.name) + ", version=" + str(self.version) + "]"

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

    def __str__(self) -> str:
        return "FilesystemChange [ file_path=" + str(self.rel_file_path) + ", content=" + str(self.content) + " ]"

class PrChange():
    def __init__(self,  meterian_project_id: str, dependencies : List[Dependency], filesystem_changes: List[FilesystemChange], pr_report: dict, pr: PullRequestInterface = None) -> None:
        self.meterian_project_id = meterian_project_id
        self.dependencies = dependencies
        self.filesystem_changes = filesystem_changes
        self.pr_report = pr_report
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

    PR_REPORT_FILENAME = ".pr_report.json"
    __SUPPORTED_MANIFEST_FILES_PATTERNS = [ "pom.xml", "composer.json", "Gemfile", "Gemfile.lock", "Pipfile", "Pipfile.lock", "package.json", "package-lock.json", "^.*\..+proj$" ]

    def __init__(self, root_folder: Path, git_changes: List[str]) -> None:
        self.root_folder = root_folder
        self.git_changes = git_changes

    def generate(self, location: Path) -> PrChange:
        if Path(location, self.PR_REPORT_FILENAME).exists:
            self.__logger.debug("Detected PR report at in %s", self.__relative_path(location))
            pr_report = self.__load_report_json(Path(location, self.PR_REPORT_FILENAME))
            if pr_report:
                if any(location in Path(self.root_folder, fs_change).parents for fs_change in self.git_changes):
                    self.__logger.debug("Viable changes found in %s, proceeding to generate PR change information...", self.__relative_path(location))
                    fs_changes = self.__collect_fs_changes(location)
                    dependencies = self.__collect_dependencies(pr_report)
                    project_id = self.__parse_project_id(pr_report)
                    if fs_changes and dependencies and project_id:
                        pr_change = PrChange(project_id, dependencies, fs_changes, pr_report)
                        self.__logger.debug("Generated PR change %s", str(pr_change))
                        return pr_change
                    else:
                        self.__logger.debug("Incomplete data collected for PR change, generation will be aborted")
            else:
                self.__logger.debug("Could not load PR report, generation will be aborted")
        else:
            self.__logger.debug("No PR report detected in %s", self.__relative_path(location))

        self.__logger.error("Failed to generate PR change information for changes detected in %s", self.__relative_path(location))
        return None

    def __relative_path(self, location: Path) -> str:
        return str(location.relative_to(self.root_folder))

    def __load_report_json(self, path: Path) -> dict:
        try:
            stream = open(path, encoding="utf-8")
            pr_report = json.load(stream)
            stream.close()
            return pr_report
        except:
            self.__logger.debug("Unable to load PR report at %s", str(path), exc_info=1)
            return None

    def __collect_dependencies(self, pr_report: dict) -> List[Dependency]:
        # collect autofix dependencies
        deps = []
        for change in pr_report["autofix"]["changes"]:
            dep = Dependency(None, change["name"], change["version"])
            deps.append(dep)
            self.__logger.debug("Collected dependency %s from autofix report", str(dep))

        # adjust dependencies language
        final_deps = []
        reports = pr_report["reports"]["licensing"]["reports"]
        for dep in deps:
            lang = self.__find_lang(reports, dep)
            if lang:
                dep.language = lang
                final_deps.append(dep)
                self.__logger.debug("Loaded dependency %s", str(dep))
            else:
                self.__logger.warning("Unexpected unable to finalise dependency %s: no language found, will be discarded", str(dep))
            
        return final_deps if len(final_deps) > 0 else None

    def __find_lang(self, reports, dep):
        for report in reports:
            lang = report["language"]
            for result in report["results"]:
                if dep.name == result["name"] and dep.version == result["version"]:
                    return lang
        return None

    def __parse_project_id(self, pr_report: dict) -> str:
        url_str = pr_report.get("url", None)
        try:
            url = parse.urlparse(url_str)
            query_str = parse.parse_qs(url.query)
            return query_str["pid"][0]
        except:
            self.__logger.debug("Unable to parse project ID from url %s in PR report ", str(url_str), exc_info=1)
            return None

    def __collect_fs_changes(self, location: Path) -> List[FilesystemChange]:
        try:
            fs_changes = []
            for git_change in self.git_changes:
                if location in Path(self.root_folder, git_change).parents and self.__is_supported_manifest(Path(self.root_folder, git_change).name):
                    content = self.__read_file_bytes(str(Path(self.root_folder, git_change).absolute()))
                    fs_changes.append(FilesystemChange(git_change, content))
                    self.__logger.debug("Loaded manifest change for %s", str(git_change))
            return fs_changes
        except:
            self.__logger.debug("Unable to collect filesystem changes in %s", self.__relative_path(location), exc_info=1)
            return None

    def __is_supported_manifest(self, file_name: str) -> bool:
        res = False

        for pattern in self.__SUPPORTED_MANIFEST_FILES_PATTERNS:
            if re.match(pattern, file_name):
                res = True
                break

        return res

    def __read_file_bytes(self, path: str) -> bytes:
        file = open(path, "rb")
        bytes_contents = file.read()
        file.close()
        return bytes_contents