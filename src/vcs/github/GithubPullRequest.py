import logging

from ..PullRequestInterface import PullRequestInterface
from github.PullRequest import PullRequest as PyGithubPullRequest
from github import GithubObject
from github import GithubException

class GithubPullRequest(PullRequestInterface):

    __log = logging.getLogger("GithubPullRequest")

    def __init__(self, pyGithubPullRequest: PyGithubPullRequest):
        self.pyGithubPullRequest = pyGithubPullRequest
    
    def edit(self, title: str = None, body: str = None):
        the_title = GithubObject.NotSet if title is None else title
        the_body = GithubObject.NotSet if body is None else body
        try: 
            self.pyGithubPullRequest.edit(title=the_title, body=the_body)
        except GithubException:
            self.__log.warning("Unexpected exception caught while trying to edit PR %s", self.pyGithubPullRequest)
            self.__log.debug("GithubException caught attempting to edit PR", exc_info=1)

    def get_url(self) -> str:
        return self.pyGithubPullRequest.html_url

    def get_title(self) -> str:
        return self.pyGithubPullRequest.title

    def get_body(self) -> str:
        return self.pyGithubPullRequest.body

    def __str__(self) -> str:
        return "GithubPullRequest [ title=" + self.get_title() + ", html_url=" + self.get_url() + " ]"