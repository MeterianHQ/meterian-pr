import logging

from ..RepositoryInterface import RepositoryInterface
from ..PullRequestInterface import PullRequestInterface
from ..IssueInterface import IssueInterface
from .GitlabMergeRequest import GitlabMergeRequest
from gitlab.v4.objects.projects import Project
from typing import List

class GitlabProject(RepositoryInterface):

    __log = logging.getLogger("GitlabProject")

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
    
    def commit_change(self, author: dict, message: str, branch: str, path: str, content: bytes) -> bool:
        return super().commit_change(author, message, branch, path, content)

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

    def __str__(self):
        return "GitlabProject [ namespace=" + self.namespace + ", name=" + self.name + ", default_branch=" + self.default_branch + ", owner=" + self.owner + ", owner=" + self.issues_enabled + " ]"