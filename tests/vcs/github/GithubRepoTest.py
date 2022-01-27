import unittest

from unittest.mock import MagicMock
from unittest.mock import ANY
from unittest.mock import Mock
from github.Label import Label
from github.Commit import Commit
from github import GithubObject
from github.ContentFile import ContentFile
from github.InputGitAuthor import InputGitAuthor
from github.GithubException import UnknownObjectException
from github.GithubException import GithubException
from github.Organization import Organization
from github.PullRequest import PullRequest
from github.Repository import Repository as PyGithubRepository
from github.Branch import Branch
from src.vcs.RepositoryInterface import RepositoryInterface
from src.vcs.github.GithubRepo import GithubRepo
from typing import List

class GithubRepoTest(unittest.TestCase):

    def setUp(self) -> None:
        self.pyGithubRepo = Mock(spec=PyGithubRepository)
        self.githubRepo = GithubRepo(self.pyGithubRepo)
        self.author = {"username": "foo", "email": "foo@baz.com"}

    def test_should_get_repo_owner(self):
        self.pyGithubRepo.organization = Mock(spec=Organization)
        self.pyGithubRepo.organization.login = "my_org"
        self.assertEqual("my_org", self.githubRepo.get_owner())
    
    def test_should_get_repo_owner_when_repo_organization_login_is_none(self):
        self.pyGithubRepo.organization = None
        self.pyGithubRepo.owner.login = "foo"
        self.assertEqual("foo", self.githubRepo.get_owner())

# Branch creation tests

    def test_should_fail_to_create_branch_when_unexpected_exception_is_caught(self):
        self.pyGithubRepo.create_git_ref = MagicMock(side_effect=GithubException(500, {"message":  "Error"}, None))
        base_branch = Mock(spec=Branch)
        base_branch.name = "master"
        base_branch.commit.sha = "commit-sha"
        self.pyGithubRepo.get_branch = MagicMock(return_value=base_branch)
        self.pyGithubRepo.get_branches = MagicMock(return_value=[base_branch])

        result = self.githubRepo.create_branch("master", "refs/heads/new-branch-name")

        self.pyGithubRepo.get_branch.assert_called_once_with("master")
        self.pyGithubRepo.create_git_ref.assert_called_once_with(ref="refs/heads/new-branch-name", sha="commit-sha")
        self.assertFalse(result)

    def test_should_not_create_branch_when_it_exists(self):
        base_branch = Mock(spec=Branch)
        base_branch.name = "new-branch-name"
        self.pyGithubRepo.get_branches = MagicMock(return_value=[base_branch])

        result = self.githubRepo.create_branch("base-branch-name", "refs/heads/new-branch-name")

        self.pyGithubRepo.get_branches.assert_called_once()
        self.assertTrue(result)

    def test_should_create_branch(self):
        base_branch = Mock(spec=Branch)
        base_branch.name = "master"
        base_branch.commit.sha = "commit-sha"
        self.pyGithubRepo.get_branch = MagicMock(return_value=base_branch)
        self.pyGithubRepo.get_branches = MagicMock(return_value=[base_branch])

        result = self.githubRepo.create_branch("master", "refs/heads/new-branch-name")

        self.pyGithubRepo.get_branch.assert_called_once_with("master")
        self.pyGithubRepo.create_git_ref.assert_called_once_with(ref="refs/heads/new-branch-name", sha="commit-sha")
        self.assertTrue(result)

# Commit submission tests

    def test_should_not_commit_change_on_nonexistent_branch(self):
        branch = Mock(spec=Branch)
        branch.name = "master"
        self.pyGithubRepo.get_branches = MagicMock(return_value=[branch])

        result = self.githubRepo.commit_change(self.author, "commit message", "branch", "path/to/file", b'content')

        self.pyGithubRepo.get_branches.assert_called_once()
        self.assertFalse(result)

    def test_should_fail_to_commit_new_remote_file_when_unexpected_exception_is_caught_on_content_fetch(self):
        branches = self.__mock_branches(["master", "my_branch"])
        self.pyGithubRepo.get_branches = MagicMock(return_value=branches)
        self.pyGithubRepo.get_contents = MagicMock(side_effect=GithubException(500, {"message": "Error"}, None))

        result = self.githubRepo.commit_change(self.author, "commit message", "my_branch", "path/to/file", b'content')

        self.pyGithubRepo.get_branches.assert_called_once()
        self.pyGithubRepo.get_contents.assert_called_once_with("path/to/file", ref="my_branch")
        self.assertFalse(result)

    def test_should_fail_to_commit_new_remote_file_when_unexpected_exception_is_caught(self):
        branches = self.__mock_branches(["master", "my_branch"])
        self.pyGithubRepo.get_branches = MagicMock(return_value=branches)
        self.pyGithubRepo.get_contents = MagicMock(side_effect=UnknownObjectException(404, {"message": "Not Found"}, None))
        self.pyGithubRepo.create_file = MagicMock(side_effect=GithubException(500, {"message": "Error"}, None))

        result = self.githubRepo.commit_change(self.author, "commit message", "my_branch", "path/to/file", b'content')

        self.pyGithubRepo.get_branches.assert_called_once()
        self.pyGithubRepo.get_contents.assert_called_once_with("path/to/file", ref="my_branch")
        self.pyGithubRepo.create_file.assert_called_once_with("path/to/file", "commit message", b'content', branch="my_branch", committer=ANY)
        self.assertFalse(result)

    def test_should_create_file_when_committing_new_remote_file(self):
        branches = self.__mock_branches(["master", "my_branch"])
        self.pyGithubRepo.get_branches = MagicMock(return_value=branches)
        self.pyGithubRepo.get_contents = MagicMock(side_effect=UnknownObjectException(404, {"message": "Not Found"}, None))
        self.pyGithubRepo.create_file = MagicMock(return_value={"content": Mock(spec=ContentFile), "commit": Mock(spec=Commit)})

        result = self.githubRepo.commit_change(self.author, "commit message", "my_branch", "path/to/file", b'content')

        self.pyGithubRepo.get_branches.assert_called_once()
        self.pyGithubRepo.get_contents.assert_called_once_with("path/to/file", ref="my_branch")
        self.pyGithubRepo.create_file.assert_called_once_with("path/to/file", "commit message", b'content', branch="my_branch", committer=ANY)
        kwargs = self.pyGithubRepo.create_file.call_args[1]
        self.assertEqual(self.__as_committer(self.author)._InputGitAuthor__name, kwargs["committer"]._InputGitAuthor__name)
        self.assertEqual(self.__as_committer(self.author)._InputGitAuthor__email, kwargs["committer"]._InputGitAuthor__email)
        self.assertTrue(result)

    def test_should_fail_to_commit_change_to_existent_remote_file_when_unexpected_exception_is_caught(self):
        branches = self.__mock_branches(["master", "my_branch"])
        self.pyGithubRepo.get_branches = MagicMock(return_value=branches)
        content = self.__create_content("path/to/file", b'old content', "commit-sha")
        self.pyGithubRepo.get_contents = MagicMock(return_value=content)
        self.pyGithubRepo.update_file = MagicMock(side_effect=GithubException(500, {"message": "Error"}, None))

        result = self.githubRepo.commit_change(self.author, "commit message", "my_branch", "path/to/file", b'new content')

        self.pyGithubRepo.get_branches.assert_called_once()
        self.pyGithubRepo.get_contents.assert_called_once_with("path/to/file", ref="my_branch")
        self.pyGithubRepo.update_file.assert_called_once_with("path/to/file", "commit message", b'new content', "commit-sha", branch="my_branch", committer=ANY)
        self.assertFalse(result)

    def test_should_not_update_file_when_committing_no_change_to_existent_remote_file(self):
        branches = self.__mock_branches(["master", "my_branch"])
        self.pyGithubRepo.get_branches = MagicMock(return_value=branches)
        content = self.__create_content("path/to/file", b'old content', "commit-sha")
        self.pyGithubRepo.get_contents = MagicMock(return_value=content)

        result = self.githubRepo.commit_change(self.author, "commit message", "my_branch", "path/to/file", b'old content')

        self.pyGithubRepo.get_branches.assert_called_once()
        self.pyGithubRepo.get_contents.assert_called_once_with("path/to/file", ref="my_branch")
        self.assertFalse(result)

    def test_should_update_file_when_committing_change_to_existent_remote_file(self):
        branches = self.__mock_branches(["master", "my_branch"])
        self.pyGithubRepo.get_branches = MagicMock(return_value=branches)
        content = self.__create_content("path/to/file", b'old content', "commit-sha")
        self.pyGithubRepo.get_contents = MagicMock(return_value=content)
        self.pyGithubRepo.update_file = MagicMock(return_value={"content": Mock(spec=ContentFile), "commit": Mock(spec=Commit)})

        result = self.githubRepo.commit_change(self.author, "commit message", "my_branch", "path/to/file", b'new content')

        self.pyGithubRepo.get_branches.assert_called_once()
        self.pyGithubRepo.get_contents.assert_called_once_with("path/to/file", ref="my_branch")
        self.pyGithubRepo.update_file.assert_called_once_with("path/to/file", "commit message", b'new content', "commit-sha", branch="my_branch", committer=ANY)
        kwargs = self.pyGithubRepo.update_file.call_args[1]
        self.assertEqual(self.__as_committer(self.author)._InputGitAuthor__name, kwargs["committer"]._InputGitAuthor__name)
        self.assertEqual(self.__as_committer(self.author)._InputGitAuthor__email, kwargs["committer"]._InputGitAuthor__email)
        self.assertTrue(result)

# Pull request creation tests

    def test_should_create_pull_request(self):
        label = Mock(spec=Label)
        label.name = "meterian-bot-pr"
        pull = Mock(spec=PullRequest)
        pull.get_labels = MagicMock(return_value=[Mock(spec=Label)])
        self.pyGithubRepo.create_pull = MagicMock(return_value=pull)
        self.pyGithubRepo.get_label = MagicMock(return_value=label)

        pr = self.githubRepo.create_pull_request("title", "body text", "head", "base")

        self.pyGithubRepo.create_pull.assert_called_once_with(title="title", body="body text", head="head", base="base")
        pull.add_to_labels.assert_called_once_with(ANY)
        args = pull.add_to_labels.call_args[0]
        self.assertEqual(RepositoryInterface.METERIAN_BOT_PR_LABEL_NAME, args[0].name)
        self.assertTrue(isinstance(pr, PullRequest))
    
    def test_should_create_pull_request_without_adding_meterian_label_when_label_cannot_be_retrieved(self):
        label = Mock(spec=Label)
        label.name = "meterian-bot-pr"
        pull = Mock(spec=PullRequest)
        pull.get_labels = MagicMock(return_value=[Mock(spec=Label)])
        self.pyGithubRepo.create_pull = MagicMock(return_value=pull)
        self.pyGithubRepo.get_label = MagicMock(side_effect=GithubException(500, {"message": "Error"}, None))

        pr = self.githubRepo.create_pull_request("title", "body text", "head", "base")

        self.pyGithubRepo.create_pull.assert_called_once_with(title="title", body="body text", head="head", base="base")
        pull.add_to_labels.assert_not_called()
        self.assertTrue(isinstance(pr, PullRequest))

    def test_should_create_pull_request_without_adding_meterian_label_when_pr_is_already_labelled(self):
        label = Mock(spec=Label)
        label.name = "meterian-bot-pr"
        pull = Mock(spec=PullRequest)
        pull.get_labels = MagicMock(return_value=[label])
        self.pyGithubRepo.create_pull = MagicMock(return_value=pull)
        self.pyGithubRepo.get_label = MagicMock(return_value=label)

        print("The labels" + str(pull.get_labels()))

        pr = self.githubRepo.create_pull_request("title", "body text", "head", "base")

        self.pyGithubRepo.create_pull.assert_called_once_with(title="title", body="body text", head="head", base="base")
        pull.get_labels.assert_called()
        pull.add_to_labels.assert_not_called()
        self.assertTrue(isinstance(pr, PullRequest))

    def test_should_not_create_pull_request_when_exception_is_caught(self):
        self.pyGithubRepo.create_pull = MagicMock(side_effect=GithubException(500, {"message": "Error"}, None))

        pr = self.githubRepo.create_pull_request("title", "body text", "head", "base")

        self.pyGithubRepo.create_pull.assert_called_once_with(title="title", body="body text", head="head", base="base")
        self.assertIsNone(pr)


# Issue creation tests

    def test_should_not_open_issue_when_GithubException_caught(self):
        label = Mock(spec=Label)
        label.name = "meterian-bot-issue"
        label.color = "2883fa"
        self.pyGithubRepo.get_label = MagicMock(return_value=label)

        self.pyGithubRepo.create_issue = MagicMock(side_effect=GithubException(500, {"message": "Error"}, None))
        self.assertIsNone(self.githubRepo.create_issue("title", "body"))

    def test_should_open_labelled_issue_when_meterian_label_can_be_retrieved(self):
        label = Mock(spec=Label)
        label.name = "meterian-bot-issue"
        label.color = "2883fa"
        self.pyGithubRepo.get_label = MagicMock(return_value=label)

        self.githubRepo.create_issue("title", "body")

        self.pyGithubRepo.create_issue.assert_called_once_with(title="title", body="body", labels=[ANY])
        kwargs = self.pyGithubRepo.create_issue.call_args[1]
        labels = kwargs["labels"]
        self.assertEqual(1, len(labels), "Expected the usage of only one label")
        self.assertEqual(RepositoryInterface.METERIAN_BOT_ISSUE_LABEL_NAME, labels[0].name)
        self.assertEqual(RepositoryInterface.METERIAN_LABEL_COLOR, labels[0].color)

    def test_should_open_unlabelled_issue_when_meterian_label_cannot_be_retrieved(self):
        self.pyGithubRepo.get_label = MagicMock(side_effect=GithubException(500, {"message": "Error"}, None))

        self.githubRepo.create_issue("title", "body")

        self.pyGithubRepo.create_issue.assert_called_once_with(title="title", body="body", labels=GithubObject.NotSet)

    
    def __create_content(self, path: str, content: bytes, commit_sha: str, ) -> ContentFile:
        the_content = Mock(spec=ContentFile)
        the_content.decoded_content = content
        the_content.path = path
        the_content.sha = commit_sha
        return the_content

    def __mock_branches(self, branch_names: list) -> list:
        mock_branches = []

        for branch_name in branch_names:
            branch = Mock(spec=Branch)
            branch.name = branch_name
            mock_branches.append(branch)

        return mock_branches

    def __as_committer(self, author_data: dict) -> InputGitAuthor:
        return InputGitAuthor(
            author_data["username"],
            author_data["email"]
        )

if __name__ == "__main__":
    unittest.main()