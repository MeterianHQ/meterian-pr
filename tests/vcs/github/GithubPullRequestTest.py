import unittest

from unittest.mock import MagicMock
from unittest.mock import Mock
from github.PullRequest import PullRequest as PyGithubPullRequest
from src.vcs.github.GithubPullRequest import GithubPullRequest
from github import GithubObject

class GithubPullRequestTest(unittest.TestCase):

    def setUp(self) -> None:
        self.pyGithubPr = Mock(spec=PyGithubPullRequest)
        self.githubPr = GithubPullRequest(self.pyGithubPr)

    def test_should_edit_pull_request(self):
        self.githubPr.edit(title="new-title", body="new-body")
        self.pyGithubPr.edit.assert_called_once_with(title="new-title", body="new-body")
    
    def test_should_only_edit_pull_request_title(self):
        self.githubPr.edit(title="new-title")
        self.pyGithubPr.edit.assert_called_once_with(title="new-title", body=GithubObject.NotSet)

    def test_should_only_edit_pull_request_body(self):
        self.githubPr.edit(body="new-body")
        self.pyGithubPr.edit.assert_called_once_with(title=GithubObject.NotSet, body="new-body")

if __name__ == "__main__":
    unittest.main()