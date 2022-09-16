import unittest
from unittest.mock import MagicMock, Mock

from src.vcs.gitlab.Gitlab import Gitlab
from src.vcs.gitlab.GitlabProject import GitlabProject
from src.vcs.gitlab.GitlabIssue import GitlabIssue
from gitlab import Gitlab as PyGitlab
from gitlab import GitlabHttpError
from gitlab.v4.objects.projects import ProjectManager
from gitlab.v4.objects.projects import Project
from gitlab.v4.objects.issues import IssueManager
from gitlab.v4.objects.issues import Issue

class GitlabTest(unittest.TestCase):

    def setUp(self) -> None:
        self.pyGitlab = Mock(spec=PyGitlab)
        self.gitlab = Gitlab(self.pyGitlab)
        self.projects = Mock(spec=ProjectManager)
        self.pyGitlab.projects = self.projects
        self.issues = Mock(spec=IssueManager)
        self.pyGitlab.issues = self.issues

    def test_should_get_none_when_repository_is_not_found(self):
        self.pyGitlab.projects.get = MagicMock(side_effect=GitlabHttpError("404 Project Not Found", 404, None))

        repo = self.gitlab.get_repository("nonexistent/nonexistent")

        self.pyGitlab.projects.get.assert_called_once_with("nonexistent/nonexistent")
        self.assertIsNone(repo)

    def test_should_get_GitlabProject_when_repository_is_found(self):
        project = self.__create_project("MyOrg/MyRepo")
        self.pyGitlab.projects.get = MagicMock(return_value=project)

        repo =self.gitlab.get_repository("MyOrg/MyRepo")

        self.pyGitlab.projects.get.assert_called_once_with("MyOrg/MyRepo")
        self.assertTrue(isinstance(repo, GitlabProject))
        print(repo)

    def test_should_fetch_issues_by_title(self):
        self.issues.list = MagicMock(return_value=[self.__create_open_issue("Sample issue 12345")])
        project = self.__create_project("MyOrg/MyRepo")
        project.issues = self.issues
        self.pyGitlab.projects.get = MagicMock(return_value=project)

        issues = self.gitlab.get_issues(GitlabProject(project), "Sample issue 12345")

        self.pyGitlab.projects.get.assert_called_once_with("MyOrg/MyRepo")
        self.issues.list.assert_called_once_with(search="Sample issue 12345")
        self.assertTrue(isinstance(issues[0], GitlabIssue))
        print(issues[0])

    def test_should_find_no_issues_when_give_non_existent_project(self):
        self.pyGitlab.projects.get = MagicMock(side_effect=GitlabHttpError("404 Project Not Found", 404, None))

        issues = self.gitlab.get_issues(GitlabProject(self.__create_project("foo/bar")), "title keyword")

        self.assertTrue(len(issues) == 0)

    def test_should_find_no_issues_when_passed_None_title_keyword(self):
        issues = self.gitlab.get_issues(GitlabProject(self.__create_project("foo/bar")), None)
        self.assertTrue(len(issues) == 0)

    def __create_open_issue(self, title):
        issue = Mock(spec=Issue)
        issue.title = title
        issue.description = "description"
        issue.web_url = "https://gitlab.com/namespace/repo/~/issues/1"
        issue.state = "open"
        return issue

    def __create_project(self, name: str):
        tokens = name.rsplit('/', 1)
        project = Mock(spec=Project)
        project.namespace = { 'path': tokens[0]}
        project.name = tokens[1]
        return project


if __name__ == "__main__":
    unittest.main()
