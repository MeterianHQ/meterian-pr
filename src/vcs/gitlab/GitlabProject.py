import logging

from ..RepositoryInterface import RepositoryInterface
from ..PullRequestInterface import PullRequestInterface
from ..IssueInterface import IssueInterface
from .GitlabMergeRequest import GitlabMergeRequest
from .GitlabIssue import GitlabIssue
from .CommitData import CommitData
from ..LabelData import LabelData
from ..CommitAuthor import CommitAuthor
from ..PrChangesGenerator import FilesystemChange
from gitlab.v4.objects.projects import Project
from gitlab.v4.objects.files import ProjectFile
from gitlab.v4.objects.branches import ProjectBranch
from gitlab.v4.objects.labels import ProjectLabel
from typing import List

class GitlabProject(RepositoryInterface):

    __log = logging.getLogger("GitlabProject")

    DEFAULT_COMMITTER = CommitAuthor(
        "meterian-bot",
        "bot.gitlab@meterian.io"
    )

    MR_LABEL = LabelData(
        RepositoryInterface.METERIAN_BOT_PR_LABEL_NAME,
        RepositoryInterface.METERIAN_BOT_PR_LABEL_DESCRIPTION.replace("Pull", "Merge"),
        "#" + RepositoryInterface.METERIAN_LABEL_COLOR,
        "#" + RepositoryInterface.METERIAN_LABEL_TEXT_COLOR
    )

    ISSUE_LABEL = LabelData(
        RepositoryInterface.METERIAN_BOT_ISSUE_LABEL_NAME,
        RepositoryInterface.METERIAN_BOT_ISSUE_LABEL_DESCRIPTION,
        "#" + RepositoryInterface.METERIAN_LABEL_COLOR,
        "#" + RepositoryInterface.METERIAN_LABEL_TEXT_COLOR
    )

    def __init__(self, pyGitlabProject: Project):
        self.pyGitlabProject = pyGitlabProject
        self.namespace = self.__getOrDefault(self.pyGitlabProject.namespace, 'path', None)
        self.name = self.pyGitlabProject.path
        self.default_branch = self.pyGitlabProject.default_branch
        self.issues_enabled = self.pyGitlabProject.issues_enabled

        # despite having access to a project you may still not access to ownership info
        if hasattr(pyGitlabProject, "owner"):
            self.owner = self.__getOrDefault(self.pyGitlabProject.owner, 'username', None)
        else:
            self.__log.debug("Ownership information inaccessible, attribute owner will be set to empty")
            self.owner = ""

    def get_full_name(self) -> str:
        return self.namespace + "/" + self.name
    
    def get_default_branch(self) -> str:
        return self.default_branch
    
    def get_open_pulls(self, head: str = None, base: str = None) -> List[PullRequestInterface]:
        return self.__do_get_mrs('opened', head, base)
    
    def get_closed_pulls(self, head: str = None, base: str = None) -> List[PullRequestInterface]:
        return self.__do_get_mrs('closed', head, base)

    def get_owner(self) -> str:
        return self.owner
    
    def commit_change(self, author: CommitAuthor, message: str, branch: str, path: str, content: bytes) -> bool:
        remote_file = self.__get_remote_file(path, branch)

        commit_data = None
        if remote_file is not None:
            if CommitData.to_base64(content) != remote_file.content.encode():
                commit_data = CommitData.update_commit_data(author, message, branch, path, content)
                self.__log.debug("File %s found remotely on branch %s of project %s; it will be updated with %s", path, branch, self.get_full_name(), commit_data)
            else:
                self.__log.debug("No changes were detected, no commit will take place")
        else:
            commit_data = CommitData.create_commit_data(author, message, branch, path, content)
            self.__log.debug("File %s not found remotely on branch %s of project %s; it will be created with %s", path, branch, self.get_full_name(), commit_data)
 
        res = None
        try:
            if commit_data:
                res = self.pyGitlabProject.commits.create(commit_data.to_payload())
                self.__log.debug("Commit performed with results %s", str(res))
        except:
            self.__log.warning("Unexpected: failed to perform commit", exc_info=1)

        return True if res is not None else False

    def commit_changes(self, author: CommitAuthor, message: str, branch: str, changes: List[FilesystemChange]) -> bool:
        res = None

        if len(changes) > 0:
            payload = CommitData(author, message, branch, None, None, b'').to_payload()

            payload["actions"] = []
            for change in changes:
                remote_file = self.__get_remote_file(change.rel_file_path, branch)
                if remote_file:
                    if CommitData.to_base64(change.content) != remote_file.content.encode():
                        commit_data = CommitData.update_commit_data(author, message, branch, change.rel_file_path, change.content)
                    else:
                        commit_data = None
                        self.__log.debug("%s has not changed, it will not be added to the commit", change.rel_file_path)
                else:
                    commit_data = CommitData.create_commit_data(author, message, branch, change.rel_file_path, change.content)
                if commit_data:
                    payload["actions"].append(commit_data.to_payload()["actions"][0])

            if len(payload["actions"]) > 0:
                try:
                    res = self.pyGitlabProject.commits.create(payload)
                except:
                    self.__log.debug("Unexpected: failed to perform commit", exc_info=1)

        return True if res is not None else False

    def create_branch(self, parent_branch_name: str, new_branch_name: str) -> bool:
        res = None

        res = self.__get_remote_branch(new_branch_name)
        if res is None:
            try:
                res = self.pyGitlabProject.branches.create({
                    'branch': new_branch_name,
                    'ref': parent_branch_name
                })
                self.__log.debug("New branch %s successfully created with result=%s", new_branch_name, str(res))
            except Exception as ex:
                res = None
                self.__log.error("Unexpected: failed to create branch %s from parent branch %s on project %s: %s", new_branch_name, parent_branch_name, self.get_full_name(), str(ex))
                self.__log.debug("Unexpected: failed to create branch %s from parent branch %s on project %s", new_branch_name, parent_branch_name, self.get_full_name(), exc_info=1)
        else:
            self.__log.debug("Branch %s already exists, it won't be created", new_branch_name)

        return True if res is not None else False

    def create_issue(self, title: str, body: str, labels: List[str] = []) -> IssueInterface:
        payload = {
            'title': title,
            'description': body,
        }

        if labels is not None and len(labels) > 0:
            payload["labels"] = labels

        try:
            issue = GitlabIssue(self.pyGitlabProject.issues.create(payload))
            self.__log.debug("Created issue %s", str(issue))
            return issue
        except Exception as ex:
            self.__log.error("Could not create issue (%s) on project %s: %s", str(payload), self.get_full_name(), str(ex))
            self.__log.debug("Could not create issue (%s) on project %s", str(payload), self.get_full_name(), exc_info=1)
            return None

    def create_label(self, name: str, description: str, color: str, text_color: str) -> bool:
        return True if self.__get_or_create_label(LabelData(name, description, color, text_color)) else False

    def create_pull_request(self, title: str, body: str, head: str, base: str, labels: List[str] = []) -> PullRequestInterface:
        payload = {
            'source_branch': head,
            'target_branch': base,
            'title': title,
            'description': body,
        }

        if labels is not None and len(labels) > 0:
            payload["labels"] = labels

        try:
            mr = GitlabMergeRequest(self.pyGitlabProject.mergerequests.create(payload))
            self.__log.debug("Created MR %s", str(mr))
            return mr
        except Exception as ex:
            self.__log.error("Could not create MR (%s) on project %s: %s", str(payload), self.get_full_name(), str(ex))
            self.__log.debug("Could not create MR (%s) on project %s", str(payload), self.get_full_name(), exc_info=1)
            return None

    def has_issues_enabled(self) -> bool:
        return self.issues_enabled

    def is_remote_branch(self, name: str) -> bool:
        try:
            return True if self.pyGitlabProject.branches.get(name) is not None else False
        except:
            self.__log.debug("Could not retrieve branch %s remotely", name, exc_info=1)

        return False

    def get_pr_label(self) -> LabelData:
        return self.MR_LABEL

    def get_issue_label(self) -> LabelData:
        return self.ISSUE_LABEL

    def get_head_branch_filter_key(self, branch_name: str) -> str:
        # The filter key for pulls that uses head user or head organization and branch name in the format of user:ref-name or organization:ref-name doesn't appear to be be supported on GitLab
        return branch_name

    def __do_get_mrs(self, state: str, source_branch: str, target_branch: str) -> List[PullRequestInterface]:
        mrs = []
        for mr in self.pyGitlabProject.mergerequests.list(state=state, source_branch=source_branch, target_branch=target_branch, get_all=True):
            mrs.append(GitlabMergeRequest(mr))

        return mrs

    def __getOrDefault(self, map: dict, key: str, defVal: str) -> str:
        try:
            return map[key]
        except:
            return defVal

    def __get_remote_file(self, path: str, branch: str) -> ProjectFile:
        try:
            return self.pyGitlabProject.files.get(file_path=path, ref=branch)
        except:
            self.__log.debug("File @ path %s on branch %s of project %s was not found remotely", path, branch, self.get_full_name())
            return None

    def __get_remote_branch(self, name: str) -> ProjectBranch:
        try:
            return self.pyGitlabProject.branches.get(name)
        except:
            return None

    def __get_or_create_label(self, label_data: LabelData) -> ProjectLabel:
        try:
            return self.pyGitlabProject.labels.get(label_data.name)
        except:
            self.__log.debug("Label %s was not found in project %s", label_data.name, self.get_full_name(), exc_info=1)

        label = None
        try:
            label = self.pyGitlabProject.labels.create(label_data.to_payload())
            self.__log.debug("Created label %s for project %s", str(label), self.get_full_name())
        except:
            self.__log.debug("Unable to create label %s for project %s", label_data.name, self.get_full_name(), exc_info=1)

        return label

    def __str__(self):
        return "GitlabProject [ namespace=" + str(self.namespace) + ", name=" + str(self.name) + ", default_branch=" + str(self.default_branch) + ", owner=" + str(self.owner) + ", issues_enabled=" + str(self.issues_enabled) + " ]"