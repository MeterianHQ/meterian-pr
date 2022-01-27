import unittest
from unittest.mock import MagicMock, Mock

from src.vcs.github.Github import Github
from src.vcs.github.GithubRepo import GithubRepo
from github import Github as PyGithub
from github import UnknownObjectException
from github import Repository as PyGithubRepository
from github import GithubException
from github import Issue

class GitHubTest(unittest.TestCase):

    def setUp(self) -> None:
        self.pyGithub = Mock(spec=PyGithub)
        self.github = Github(self.pyGithub)

    def test_should_get_none_when_repository_is_not_found(self):
        self.pyGithub.get_repo = MagicMock(side_effect=UnknownObjectException(404, {"message": "Not Found"}, None))

        repository = self.github.get_repository("nonexisten/nonexistent")

        self.pyGithub.get_repo.assert_called_once_with("nonexisten/nonexistent")
        self.assertIsNone(repository)

    def test_should_get_repository(self):
        self.pyGithub.get_repo = MagicMock(return_value=Mock(spec=PyGithubRepository))
        
        repository = self.github.get_repository("MyOrg/MyRepo")

        self.pyGithub.get_repo.assert_called_once_with("MyOrg/MyRepo")
        self.assertTrue(isinstance(repository, GithubRepo))

    def test_should_get_repository_issues_by_title_using_github_query_search(self):
        pyGhRepo = Mock(spec=PyGithubRepository)
        pyGhRepo.full_name = "MyOrg/MyRepo"
        repo = GithubRepo(pyGhRepo)
        self.pyGithub.search_issues = MagicMock(spec=[Mock(spec=Issue)])

        self.github.get_issues(repo, "issue-title")

        self.pyGithub.search_issues.assert_called_once_with(query="repo:" + "MyOrg/MyRepo" + " type:issue issue-title in:title")

    def test_should_get_no_repository_issues_when_GithubExceptionIsCaught(self):
        pyGhRepo = Mock(spec=PyGithubRepository)
        pyGhRepo.full_name = "MyOrg/MyRepo"
        repo = GithubRepo(pyGhRepo)
        self.pyGithub.search_issues = MagicMock(side_effect=GithubException(500, {"message":  "Error"}, None))

        self.assertIsNone(self.github.get_issues(repo, "issue-title"))



if __name__ == "__main__":
    unittest.main()