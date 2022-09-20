from unittest.mock import Mock
from gitlab.v4.objects.projects import Project

class GitlabTestFunctions:
    def create_project(OrgAndRepo): 
        tokens = OrgAndRepo.rsplit('/', 1)
        project = Mock(spec=Project)
        project.namespace = { 'path': tokens[0] }
        project.name = tokens[1]
        project.default_branch = "master"
        project.owner = {}
        project.issues_enabled = True
        return project
