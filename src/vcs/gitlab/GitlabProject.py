import logging

from ..RepositoryInterface import RepositoryInterface
from ..PullRequestInterface import PullRequestInterface
from ..IssueInterface import IssueInterface
from .GitlabMergeRequest import GitlabMergeRequest
from .CommitData import CommitData
from ..CommitAuthor import CommitAuthor
from gitlab.v4.objects.projects import Project
from gitlab.v4.objects.files import ProjectFile
from typing import List

class GitlabProject(RepositoryInterface):

    __log = logging.getLogger("GitlabProject")

    DEFAULT_COMMITTER = CommitAuthor(
        "meterian-bot",
        "bot.gitlab@meterian.io"
    )

    def __init__(self, pyGitlabProject: Project):
        self.pyGitlabProject = pyGitlabProject
        self.namespace = self.__getOrDefault(self.pyGitlabProject.namespace, 'path', None)
        self.name = self.pyGitlabProject.name
        self.default_branch = self.pyGitlabProject.default_branch
        self.owner = self.__getOrDefault(self.pyGitlabProject.owner, 'username', None)
        self.issues_enabled = self.pyGitlabProject.issues_enabled

    def get_full_name(self) -> str:
        return self.namespace + "/" + self.name
    
    def get_default_branch(self) -> str:
        return self.default_branch
    
    def get_open_pulls(self, head: str = None, base: str = None) -> List[PullRequestInterface]:
        return self.__do_get_mrs('opened', head, base)
    
    def get_closed_pulls(self, head: str = None, base: str = None) -> List[PullRequestInterface]:
        return self.__do_get_mrs('closed', head, base)

    def get_owner(self) -> str:
        return self.owner
    
    def commit_change(self, author: CommitAuthor, message: str, branch: str, path: str, content: bytes) -> bool:
        remote_file = self.__get_remote_file(path, branch)

        commit_data = None
        if remote_file is not None:
            if CommitData.to_base64(content) != remote_file.content:
                commit_data = CommitData.update_commit_data(author, message, branch, path, content)
                self.__log.debug("File %s found remotely on branch %s of repo %s; it will be updated", path, branch, self.get_full_name())
            else:
                self.__log.debug("No changes were detected, no commit will take place")
        else:
            commit_data = CommitData.create_commit_data(author, message, branch, path, content)
            self.__log.debug("File %s not found remotely on branch %s of repo %s; it will be created", path, branch, self.get_full_name())
 
        res = None
        try:
            if commit_data:
                res = self.pyGitlabProject.commits.create(commit_data.to_payload())
                self.__log.debug("Commit performed with results %s", str(res))
        except:
            self.__log.warning("Unexpected: failed to perform commit", exc_info=1)

        return True if res is not None else False

    def create_branch(self, base_branch_name: str, ref_name: str) -> bool:
        return super().create_branch(base_branch_name, ref_name)

    def create_issue(self, title: str, body: str) -> IssueInterface:
        return super().create_issue(title, body)

    def create_pull_request(self, title: str, body: str, head: str, base: str) -> PullRequestInterface:
        return super().create_pull_request(title, body, head, base)

    def has_issues_enabled(self) -> bool:
        return self.issues_enabled
    
    def is_remote_branch(self, name: str) -> bool:
        try:
            return True if self.pyGitlabProject.branches.get(name) is not None else False
        except:
            self.__log.debug("Could not retrieve branch %s remotely", name, exc_info=1)

        return False

    def __do_get_mrs(self, state: str, source_branch: str, target_branch: str) -> List[PullRequestInterface]:
        mrs = []
        for mr in self.pyGitlabProject.mergerequests.list(state=state, source_branch=source_branch, target_branch=target_branch):
            mrs.append = GitlabMergeRequest(mr)

        return mrs

    def __getOrDefault(self, map: dict, key: str, defVal: str) -> str:
        try:
            return map[key]
        except:
            return defVal

    def __get_remote_file(self, path: str, branch: str) -> ProjectFile:
        try:
            return self.pyGitlabProject.files.get(file_path=path, ref=branch)
        except:
            self.__log.debug("File @ path %s on branch %s of repo %s was not found remotely", path, branch, self.get_full_name())
            return None

    def __str__(self):
        return "GitlabProject [ namespace=" + str(self.namespace) + ", name=" + str(self.name) + ", default_branch=" + str(self.default_branch) + ", owner=" + str(self.owner) + ", issues_enabled=" + str(self.issues_enabled) + " ]"