import logging
from src.vcs.gitlab.GitlabIssue import GitlabIssue
from src.vcs.gitlab.GitlabProject import GitlabProject
from ..VcsHubInterface import VcsHubInterface
from ..RepositoryInterface import RepositoryInterface
from ..IssueInterface import IssueInterface
from gitlab import Gitlab as PyGitlab
from gitlab import GitlabHttpError
from gitlab.v4.objects.projects import Project
from typing import List

class Gitlab(VcsHubInterface):

    __log = logging.getLogger("Gitlab")

    def __init__(self, pyGitlab: PyGitlab):
        self.pyGitlab = pyGitlab

    def get_repository(self, name: str) -> RepositoryInterface:
        project = self.__do_get_project(name)
        if project is not None:
            return GitlabProject(project)
        else:
            return None

    def get_issues(self, repository: RepositoryInterface, title: str) -> List[IssueInterface]:
        if title is None:
            self.__log.debug("Cant find issues with None title")
            return []

        project = self.__do_get_project(repository.get_full_name())
        if project is None:
            return []

        issues = project.issues.list(search=title)
        new_issues = []
        for issue in issues:
            new_issues.append(GitlabIssue(issue))

        self.__log.debug("Issues found %s", str(new_issues))
        return new_issues

    def __do_get_project(self, name: str) -> Project:
        try:
            project = self.pyGitlab.projects.get(name)
            self.__log.debug("Found project %s", project)
            return project
        except GitlabHttpError:
            self.__log.debug("Project %s was not found", name, exc_info=1)
            return None