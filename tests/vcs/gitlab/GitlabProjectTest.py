import unittest
import base64

from unittest.mock import Mock
from unittest.mock import MagicMock
from unittest.mock import ANY
from src.vcs.PullRequestInterface import PullRequestInterface
from src.vcs.gitlab.GitlabProject import GitlabProject
from src.vcs.LabelData import LabelData
from src.vcs.gitlab.GitlabIssue import GitlabIssue
from src.vcs.CommitAuthor import CommitAuthor
from gitlab.v4.objects.commits import ProjectCommitManager
from gitlab.v4.objects.files import ProjectFileManager
from gitlab.v4.objects.branches import ProjectBranchManager
from gitlab.v4.objects.merge_requests import MergeRequestManager
from gitlab.v4.objects.merge_requests import ProjectMergeRequest
from gitlab.v4.objects.labels import ProjectLabelManager
from gitlab.v4.objects.issues import IssueManager
from gitlab.v4.objects.labels import ProjectLabel
from gitlab.v4.objects.branches import ProjectBranch
from gitlab.v4.objects.files import ProjectFile
from gitlab.v4.objects.issues import ProjectIssue
from tests.vcs.gitlab.GitlabTestFunctions import GitlabTestFunctions
from gitlab import GitlabHttpError

class GitlabProjectTest(unittest.TestCase):

    def setUp(self) -> None:
        self.pyGitlabProject = self.__create_project("MyOrg/MyRepo")
        self.project = GitlabProject(self.pyGitlabProject)
        self.commits = Mock(spec=ProjectCommitManager)
        self.files = Mock(spec=ProjectFileManager)
        self.branches = Mock(spec=ProjectBranchManager)
        self.mergerequests = Mock(spec=MergeRequestManager)
        self.labels = Mock(spec=ProjectLabelManager)
        self.issues = Mock(spec=IssueManager)

        self.author = CommitAuthor(
            "joe.bloggs",
            "joe.bloggs@baz.com"
        )

    def test_should_commit_change_to_existent_remote_file(self):
        self.pyGitlabProject.commits = self.commits
        remote_file = self.__create_remote_file(b"file content")
        self.files.get = MagicMock(return_value=remote_file)
        self.pyGitlabProject.files = self.files

        result = self.project.commit_change(self.author, "the commit message", "feature/branch", "path/to/file", b"new file content")

        self.assertTrue(result)
        self.pyGitlabProject.files.get.assert_called_once_with(file_path="path/to/file", ref="feature/branch")

        self.pyGitlabProject.commits.create.assert_called_once_with(ANY)
        commit_data = self.pyGitlabProject.commits.create.call_args.args[0]
        self.__assertAuthorEqual(self.author, commit_data)
        self.assertEqual("feature/branch", commit_data["branch"])
        self.assertEqual("the commit message", commit_data["commit_message"] )
        self.assertEqual("update", commit_data["actions"][0]["action"])
        self.assertEqual("path/to/file", commit_data["actions"][0]["file_path"])
        self.assertEqual("base64", commit_data["actions"][0]["encoding"])
        self.assertEqual(self.__to_base64(b"new file content"), commit_data["actions"][0]["content"])

    def test_should_fail_to_commit_changes_when_there_are_no_changes(self):
        self.pyGitlabProject.commits = self.commits
        remote_file = self.__create_remote_file(b"file content")
        self.files.get = MagicMock(return_value=remote_file)
        self.pyGitlabProject.files = self.files

        result = self.project.commit_change(self.author, "the commit message", "feature/branch", "path/to/file", b"file content")

        self.assertFalse(result)
        self.pyGitlabProject.files.get.assert_called_once_with(file_path="path/to/file", ref="feature/branch")

    def test_should_create_file_when_committing_new_remote_file(self):
        self.pyGitlabProject.commits = self.commits
        self.files.get = MagicMock(side_effect=GitlabHttpError("404 File Not Found", 404, None))
        self.pyGitlabProject.files = self.files

        result = self.project.commit_change(self.author, "the commit message", "feature/branch", "path/to/file", b"file content")

        self.assertTrue(result)
        self.pyGitlabProject.files.get.assert_called_once_with(file_path="path/to/file", ref="feature/branch")

        self.pyGitlabProject.commits.create.assert_called_once_with(ANY)
        commit_data = self.pyGitlabProject.commits.create.call_args.args[0]
        self.__assertAuthorEqual(self.author, commit_data)
        self.assertEqual("feature/branch", commit_data["branch"])
        self.assertEqual("the commit message", commit_data["commit_message"] )
        self.assertEqual("create", commit_data["actions"][0]["action"])
        self.assertEqual("path/to/file", commit_data["actions"][0]["file_path"])
        self.assertEqual("base64", commit_data["actions"][0]["encoding"])
        self.assertEqual(self.__to_base64(b"file content"), commit_data["actions"][0]["content"])

    def test_should_fail_to_commit_change_to_when_exception_is_thrown(self):
        self.pyGitlabProject.commits = self.commits
        remote_file = self.__create_remote_file(b"file content")
        self.files.get = MagicMock(return_value=remote_file)
        self.pyGitlabProject.files = self.files
        self.pyGitlabProject.commits.create = MagicMock(side_effect=GitlabHttpError("Error", 500, None))

        self.assertFalse(self.project.commit_change(self.author, "the commit message", "feature/branch", "path/to/file", b"new file content"))

    def test_should_fail_to_commit_new_file_when_exception_is_thrown(self):
        self.pyGitlabProject.commits = self.commits
        remote_file = self.__create_remote_file(b"file content")
        self.files.get = MagicMock(return_value=remote_file)
        self.pyGitlabProject.files = self.files
        self.pyGitlabProject.commits.create = MagicMock(side_effect=GitlabHttpError("Error", 500, None))

        self.assertFalse(self.project.commit_change(self.author, "the commit message", "feature/branch", "path/to/file", b"new file content"))

    def test_should_create_feature_branch_when_it_does_not_exist(self):
        self.branches.get = MagicMock(side_effect=GitlabHttpError("404", "404 Branch Not Found"))
        self.pyGitlabProject.branches = self.branches

        result = self.project.create_branch("master", "feature1")

        self.assertTrue(result)
        self.pyGitlabProject.branches.create.assert_called_once_with({"branch": "feature1", "ref": "master"})

    def test_should_not_create_branch_when_it_already_exist(self):
        self.branches.get = MagicMock(return_vale=self.__create_remote_branch("feature1"))
        self.pyGitlabProject.branches = self.branches

        result = self.project.create_branch("master", "feature1")

        self.assertTrue(result)
        self.pyGitlabProject.branches.get.assert_called_once_with("feature1")
        self.pyGitlabProject.branches.create.assert_not_called

    def test_should_fail_to_create_branch_when_exception_is_thrown(self):
        self.branches.create = MagicMock(side_effect=GitlabHttpError("500", "Error"))
        self.branches.get = MagicMock(side_effect=GitlabHttpError("404", "404 Branch Not Found"))
        self.pyGitlabProject.branches = self.branches

        self.assertFalse(self.project.create_branch("master", "feature1"))

    def test_should_open_labelled_merge_request(self):
        self.mergerequests.create = MagicMock(return_value=self.__create_mr("MR title", "MR content"))
        self.pyGitlabProject.mergerequests = self.mergerequests

        result = self.project.create_pull_request("MR title", "MR content", "feature1", "master", ["meterian-bot-pr"])

        self.assertTrue(isinstance(result, PullRequestInterface))
        self.pyGitlabProject.mergerequests.create.assert_called_once_with(ANY)
        mr_payload = self.pyGitlabProject.mergerequests.create.call_args.args[0]
        self.assertEqual("feature1", mr_payload["source_branch"])
        self.assertEqual("master", mr_payload["target_branch"])
        self.assertEqual("MR title", mr_payload["title"])
        self.assertEqual("MR content", mr_payload["description"])
        self.assertTrue(any("meterian-bot-pr" == label_title for label_title in mr_payload["labels"]))

    def test_should_open_unlabelled_merge_request(self):
        self.mergerequests.create = MagicMock(return_value=self.__create_mr("MR title", "MR content"))
        self.pyGitlabProject.mergerequests = self.mergerequests

        result = self.project.create_pull_request("MR title", "MR content", "feature1", "master", [])

        self.assertTrue(isinstance(result, PullRequestInterface))
        self.pyGitlabProject.mergerequests.create.assert_called_once_with(ANY)
        mr_payload = self.pyGitlabProject.mergerequests.create.call_args.args[0]
        self.assertEqual("feature1", mr_payload["source_branch"])
        self.assertEqual("master", mr_payload["target_branch"])
        self.assertEqual("MR title", mr_payload["title"])
        self.assertEqual("MR content", mr_payload["description"])
        self.assertFalse("labels" in mr_payload)

    def test_should_fail_to_open_mr_when_exception_is_thrown(self):
        self.mergerequests.create = MagicMock(side_effect=GitlabHttpError("500", "Error"))
        self.pyGitlabProject.mergerequests = self.mergerequests

        self.assertIsNone(self.project.create_pull_request("MR title", "MR content", "feature1", "master", []))

    def test_should_create_label(self):
        self.labels.get = MagicMock(side_effect=GitlabHttpError("404", "404 Label Not Found"))
        self.labels.create = MagicMock(return_value=self.__create_label(LabelData("name", "description", "color", "text_color")))
        self.pyGitlabProject.labels = self.labels

        self.assertTrue(self.project.create_label("name", "description", "color", "text_color"))
        self.pyGitlabProject.labels.create.assert_called_once_with(LabelData("name", "description", "color", "text_color").to_payload())

    def test_should_not_create_label_when_it_already_exists(self):
        self.labels.get = MagicMock(return_value=self.__create_label(LabelData("name", "description", "color", "text_color")))
        self.pyGitlabProject.labels = self.labels

        self.assertTrue(self.project.create_label("name", "description", "color", "text_color"))
        self.pyGitlabProject.labels.create.assert_not_called

    def test_should_fail_to_create_label_when_exception_thrown(self):
        self.labels.get = MagicMock(side_effect=GitlabHttpError("404", "404 Label Not Found"))
        self.labels.create = MagicMock(side_effect=GitlabHttpError("500", "Error"))
        self.pyGitlabProject.labels = self.labels

        self.assertFalse(self.project.create_label("name", "description", "color", "text_color"))

    def test_should_open_labelled_issue(self):
        self.issues.create = MagicMock(return_value=self.__create_issue("The title", "The description"))
        self.pyGitlabProject.issues = self.issues

        issue = self.project.create_issue("The title", "The description", ["meterian-bot-issue"])

        self.assertTrue(isinstance(issue, GitlabIssue))
        self.pyGitlabProject.issues.create.assert_called_once_with(ANY)
        issue_payload = self.pyGitlabProject.issues.create.call_args.args[0]
        self.assertEqual("The title", issue_payload["title"])
        self.assertEqual("The description", issue_payload["description"])
        self.assertTrue(any("meterian-bot-issue" == label_title for label_title in issue_payload["labels"]))

    def test_should_open_unlabelled_issue(self):
        self.issues.create = MagicMock(return_value=self.__create_issue("The title", "The description"))
        self.pyGitlabProject.issues = self.issues

        issue = self.project.create_issue("The title", "The description", [])

        self.assertTrue(isinstance(issue, GitlabIssue))
        self.pyGitlabProject.issues.create.assert_called_once_with(ANY)
        issue_payload = self.pyGitlabProject.issues.create.call_args.args[0]
        self.assertEqual("The title", issue_payload["title"])
        self.assertEqual("The description", issue_payload["description"])
        self.assertFalse("labels" in issue_payload)

    def test_should_fail_to_open_issue_when_exception_is_thrown(self):
        self.issues.create = MagicMock(side_effect=GitlabHttpError("500", "Error"))
        self.pyGitlabProject.issues = self.issues

        self.assertIsNone(self.project.create_issue("The title", "The description", []))

    def __assertAuthorEqual(self, expected_author: CommitAuthor, glab_commit_data: dict):
        self.assertEqual(expected_author.username, glab_commit_data["author_name"])
        self.assertEqual(expected_author.email, glab_commit_data["author_email"])

    def __create_project(self, name: str):
        return GitlabTestFunctions.create_project(name)

    def __to_base64(self, data: bytes) -> bytes:
        return base64.b64encode(data)

    def __create_remote_file(self, content: bytes):
        afile = Mock(spec=ProjectFile)
        afile.content = self.__to_base64(content).decode("utf-8")
        return afile

    def __create_remote_branch(self, name: str):
        branch = Mock(spec=ProjectBranch)
        branch.name = name
        return branch

    def __create_label(self, label_data: LabelData):
        label = Mock(spec=ProjectLabel)
        label.name = label_data.name
        label.description = label_data.description
        label.color = label_data.color
        label.text_color = label_data.text_color
        label.is_project_label = True
        return label

    def __create_mr(self, title: str, desc: str):
        mr = Mock(spec=ProjectMergeRequest)
        mr.title = title
        mr.description = desc
        mr.web_url = "https://gitlab.com/" + self.project.get_full_name() + "/-/merge_requests/1"
        return mr

    def __create_issue(self, title: str, desc: str):
        issue = Mock(spec=ProjectIssue)
        issue.title = title
        issue.description = desc
        issue.web_url = "https://gitlab.com/" + self.project.get_full_name() + "/-/issues/1"
        return issue

if __name__ == "__main__":
    unittest.main()