import logging

from github import Github as PyGithub
from .GithubIssue import GithubIssue
from .GithubRepo import GithubRepo
from ..VcsHubInterface import VcsHubInterface
from ..RepositoryInterface import RepositoryInterface
from ..IssueInterface import IssueInterface
from github import UnknownObjectException
from github import GithubException
from typing import List

class Github(VcsHubInterface):

    __log = logging.getLogger("Github")

    def __init__(self, pyGithub: PyGithub):
        self.pyGithub = pyGithub

    def get_repository(self, name):
        try:
            self.__log.debug("Currently authenticated as %s", str(self.pyGithub.get_user()))
            self.__log.debug("Getting repository %s", name)
            repo = self.pyGithub.get_repo(name)
            return GithubRepo(repo)
        except UnknownObjectException:
            self.__log.error("Repo %s was not found", name, exc_info=1)
            return None
    
    def get_issues(self, repository: RepositoryInterface, title: str) -> List[IssueInterface]:
        query="repo:" + repository.get_full_name() + " type:issue " + title + " in:title"
        try:
            issues = self.pyGithub.search_issues(query=query)

            results = []
            for issue in issues:
                results.append(GithubIssue(issue))
            self.__log.debug("Issues found %s", str(results))
            return results
            
        except GithubException:
            self.__log.error("Unexpected GithubException caught while searching for issue with query %s", query, exc_info=1)
        
        return None