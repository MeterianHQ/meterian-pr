import logging

from ..RepositoryInterface import RepositoryInterface
from ..PullRequestInterface import PullRequestInterface
from ..IssueInterface import IssueInterface
from gitlab.v4.objects.projects import Project
from typing import List

class GitlabProject(RepositoryInterface):
    
    def __init__(self, pyGitlabProject: Project):
        self.pyGitlabProject = pyGitlabProject
        self.namespace = self.pyGitlabProject.namespace['path']
        self.name = self.pyGitlabProject.name

    def get_full_name(self) -> str:
        return self.namespace + "/" + self.name
    
    def get_default_branch(self) -> str:
        return super().get_default_branch()
    
    def get_open_pulls(self, head: str = None, base: str = None) -> List[PullRequestInterface]:
        return super().get_open_pulls(head, base)
    
    def get_closed_pulls(self, head: str = None, base: str = None) -> List[PullRequestInterface]:
        return super().get_closed_pulls(head, base)

    def get_owner(self) -> str:
        return super().get_owner()
    
    def commit_change(self, author: map, message: str, branch: str, path: str, content: bytes) -> bool:
        return super().commit_change(author, message, branch, path, content)

    def create_branch(self, base_branch_name: str, ref_name: str) -> bool:
        return super().create_branch(base_branch_name, ref_name)

    def create_issue(self, title: str, body: str) -> IssueInterface:
        return super().create_issue(title, body)

    def create_pull_request(self, title: str, body: str, head: str, base: str) -> PullRequestInterface:
        return super().create_pull_request(title, body, head, base)

    def has_issues_enabled(self) -> bool:
        return super().has_issues_enabled()
    
    def is_remote_branch(self, name: str) -> bool:
        return super().is_remote_branch(name)

    def __str__(self):
        return "GitlabProject [ namespace=" + self.namespace + ", name=" + self.name + " ]"