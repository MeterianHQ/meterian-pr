import unittest
import base64

from unittest.mock import Mock
from unittest.mock import MagicMock
from unittest.mock import ANY
from src.vcs.gitlab.Gitlab import GitlabProject
from src.vcs.CommitAuthor import CommitAuthor
from gitlab.v4.objects.commits import ProjectCommitManager
from gitlab.v4.objects.files import ProjectFileManager
from gitlab.v4.objects.files import ProjectFile
from tests.vcs.gitlab.GitlabTestFunctions import GitlabTestFunctions
from gitlab import GitlabHttpError

class GitlabProjectTest(unittest.TestCase):

    def setUp(self) -> None:
        self.pyGitlabProject = self.__create_project("MyOrg/MyRepo")
        self.project = GitlabProject(self.pyGitlabProject)
        self.commits = Mock(spec=ProjectCommitManager)
        self.files = Mock(spec=ProjectFileManager)

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

    def __assertAuthorEqual(self, expected_author: CommitAuthor, glab_commit_data: dict):
        self.assertEqual(expected_author.username, glab_commit_data["author_name"])
        self.assertEqual(expected_author.email, glab_commit_data["author_email"])

    def __create_project(self, name: str):
        return GitlabTestFunctions.create_project(name)

    def __to_base64(self, data: bytes) -> bytes:
        return base64.b64encode(data)

    def __create_remote_file(self, content: bytes):
        afile = Mock(spec=ProjectFile)
        afile.content = self.__to_base64(content)
        return afile

if __name__ == "__main__":
    unittest.main()