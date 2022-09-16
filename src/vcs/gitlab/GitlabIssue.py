from ..IssueInterface import IssueInterface
from gitlab.v4.objects.issues import Issue

class GitlabIssue(IssueInterface):
    
    def __init__(self, pyGitlabIssue: Issue):
        self.pyGitlabIssue = pyGitlabIssue
        self.title = self.pyGitlabIssue.title
        self.body = self.pyGitlabIssue.description
        self.url = self.pyGitlabIssue.web_url
        self.is_open = True if self.pyGitlabIssue == "open" else False

    def get_url(self) -> str:
        return self.url

    def get_title(self) -> str:
        return self.title

    def get_body(self) -> str:
        return self.body

    def is_open(self) -> str:
        return self.is_open

    def __str__(self):
        return "GitlabIssue [ title=" + self.title + ", url=" + self.url + ", is_open=" + str(self.is_open) + ", body=" + self.body + " ]"