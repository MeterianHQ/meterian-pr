from ..IssueInterface import IssueInterface
from github.Issue import Issue as PyGithubIssue

class GithubIssue(IssueInterface):

    def __init__(self, pyGithubIssue: PyGithubIssue):
        self.pyGithubIssue = pyGithubIssue

    def get_url(self) -> str:
        return self.pyGithubIssue.html_url

    def get_title(self) -> str:
        return self.pyGithubIssue.title

    def get_body(self) -> str:
        return self.pyGithubIssue.body

    def is_open(self) -> bool:
        return False if self.pyGithubIssue.state == "closed" else True