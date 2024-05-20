from unittest.mock import MagicMock, Mock
from gitlab.v4.objects.projects import Project
from gitlab.v4.objects.issues import IssueManager
from gitlab.v4.objects.issues import Issue
from gitlab.v4.objects.projects import ProjectManager
from gitlab import Gitlab as PyGitlab

class GitlabTestFunctions:
    def create_issueless_project(OrgAndRepo): 
        tokens = OrgAndRepo.rsplit('/', 1)
        project = Mock(spec=Project)
        project.id = 1111
        project.namespace = { 'path': tokens[0] }
        project.path = tokens[1]
        project.default_branch = "master"
        project.owner = {}
        return project

    def create_project(OrgAndRepo): 
        tokens = OrgAndRepo.rsplit('/', 1)
        project = Mock(spec=Project)
        project.id = 1111
        project.namespace = { 'path': tokens[0] }
        project.path = tokens[1]
        project.default_branch = "master"
        project.owner = {}
        # project.issues_enabled = True DEPRECATED

        pyGitlab = Mock(spec=PyGitlab)
        projects = MagicMock(spec=ProjectManager)
        issues = Mock(spec=IssueManager)

        pyGitlab.projects = projects
        issues.gitlab = pyGitlab
        project.issues = issues

        return project
