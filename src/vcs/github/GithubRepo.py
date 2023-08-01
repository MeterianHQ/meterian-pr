import logging
from sys import exc_info
import traceback

from github.GithubException import GithubException
from github.GithubException import UnknownObjectException
from github.Label import Label
from github.Repository import Repository as PyGithubRepository
from github.InputGitAuthor import InputGitAuthor
from github.InputGitTreeElement import InputGitTreeElement
from github.GitCommit import GitCommit
from ..CommitAuthor import CommitAuthor
from ..PrChangesGenerator import FilesystemChange
from .GithubIssue import GithubIssue
from ..PullRequestInterface import PullRequestInterface
from ..RepositoryInterface import RepositoryInterface
from ..IssueInterface import IssueInterface
from .GithubPullRequest import GithubPullRequest
from ..BranchHelper import BranchHelper
from typing import List
from github import GithubObject
from ..LabelData import LabelData
from ..gitlab.CommitData import CommitData

class GithubRepo(RepositoryInterface):

    DEFAULT_COMMITTER = CommitAuthor(
        "meterian-bot",
        "bot.github@meterian.io"
    )

    PR_LABEL = LabelData(
        RepositoryInterface.METERIAN_BOT_PR_LABEL_NAME,
        RepositoryInterface.METERIAN_BOT_PR_LABEL_DESCRIPTION,
        RepositoryInterface.METERIAN_LABEL_COLOR,
        RepositoryInterface.METERIAN_LABEL_TEXT_COLOR
    )

    ISSUE_LABEL = LabelData(
        RepositoryInterface.METERIAN_BOT_ISSUE_LABEL_NAME,
        RepositoryInterface.METERIAN_BOT_ISSUE_LABEL_DESCRIPTION,
        RepositoryInterface.METERIAN_LABEL_COLOR,
        RepositoryInterface.METERIAN_LABEL_TEXT_COLOR
    )

    __log = logging.getLogger("GithubRepo")

    def __init__(self, pyGithubRepo: PyGithubRepository):
        self.pyGithubRepo = pyGithubRepo
        self.branch_helper = BranchHelper()

    def get_full_name(self) -> str:
        return self.pyGithubRepo.full_name

    def get_owner(self) -> str:
        if self.pyGithubRepo.organization:
            return self.pyGithubRepo.organization.login
        else:
            return self.pyGithubRepo.owner.login

    def is_remote_branch(self, name: str) -> bool:
        try:
            self.pyGithubRepo.get_branch(name)
            return True
        except UnknownObjectException:
            self.__log.debug("Branch %s was not found remotely", name)
        except GithubException:
            self.__log.warning("Unexpected exception caught while fetching branch %s remotely", name)
            self.__log.debug(traceback.format_exc())

        return False

    def get_default_branch(self) -> str:
        return self.pyGithubRepo.default_branch

    def has_issues_enabled(self) -> bool:
        return self.pyGithubRepo.has_issues

    def create_branch(self, parent_branch_name: str, new_branch_name: str) -> bool:
        try:
            if any(new_branch_name == repo_branch.name for repo_branch in self.pyGithubRepo.get_branches()):
                self.__log.debug("Branch %s already exists, it will not be created", new_branch_name)
                return True

            source_branch = self.pyGithubRepo.get_branch(parent_branch_name)
            self.pyGithubRepo.create_git_ref(ref=self.branch_helper.as_branch_ref(new_branch_name), sha=source_branch.commit.sha)
            self.__log.debug("Created new branch %s", new_branch_name)
            return True
        except GithubException:
            self.__log.debug("Unexpected exception caught while dealing with branch creation", exc_info=1)
            return False

    def commit_change(self, author: CommitAuthor, message: str, branch: str, path: str, content: bytes) -> bool:
        committer = InputGitAuthor(author.getUsername(), author.getEmail())

        if any(branch == repo_branch.name for repo_branch in self.pyGithubRepo.get_branches()):
            try:
                self.__log.debug("Attempting to get contents for file %s on branch %s of repo %s", path, branch, self.get_full_name())
                remote_content = self.pyGithubRepo.get_contents(path, ref=branch)
            except UnknownObjectException as ex:
                if "404" in str(ex) or "not found" in str(ex).lower():
                    try:
                        self.__log.debug("%s not found remotely, will be created", path)
                        self.pyGithubRepo.create_file(path, message, content, branch=branch, committer=committer)
                        self.__log.debug("Successfully created %s", path)
                        return True
                    except Exception:
                        self.__log.warning("Unexpected exception caught while dealing with commit involving new remote file creation", exc_info=1)
                        return False    
            except Exception:
                    self.__log.warning("Unexpected exception caught while fetching for remote file %s", path, exc_info=1)
                    return False
            
            raw_remote_content = remote_content.decoded_content
            if content != raw_remote_content:
                try:
                    self.pyGithubRepo.update_file(remote_content.path, message, content, remote_content.sha, branch=branch, committer=committer)
                    self.__log.debug("Successfully update %s on branch %s", path, branch)
                    return True
                except GithubException:
                    self.__log.warning("Unexpected exception caught while dealing with commit involving remote file update", exc_info=1)
                    return False
            else:
                self.__log.debug("There were no changes to commit to branch %s", branch)
                return False
        else:
            self.__log.warning("Branch %s was not found, no commit will be made at this stage", branch)
            return False

    def commit_changes(self, author: CommitAuthor, message: str, branch: str, changes: List[FilesystemChange]) -> bool:
        if len(changes) < 1:
            self.__log.debug("No changes provided to commit: changes=%s", str(changes))
            return False

        if any(branch == repo_branch.name for repo_branch in self.pyGithubRepo.get_branches()):
            try:
                head_commit = self.__get_head_commit(branch)
                base_git_tree = self.pyGithubRepo.get_git_tree(sha=head_commit.sha)

                tree_elements = self.__to_tree_elements(changes)
                new_git_tree = self.pyGithubRepo.create_git_tree(tree_elements, base_git_tree)

                new_commit = self.pyGithubRepo.create_git_commit(message, new_git_tree, [head_commit])
                git_ref = self.pyGithubRepo.get_git_ref("heads/" + branch)
                git_ref.edit(sha=new_commit.sha)
                return True
            except:
                self.__log.warning("Unexpected exception caught while dealing with multiple changes commit", exc_info=1)
                return False
        else:
            self.__log.debug("Branch %s was not found, no commit will be made at this stage", branch)
            return False

    def __get_head_commit(self, branch: str) -> GitCommit:
        sha = self.pyGithubRepo.get_branch(branch).commit.sha
        return self.pyGithubRepo.get_git_commit(sha=sha)

    def __to_tree_elements(self, changes: List[FilesystemChange]) -> List[InputGitTreeElement]:
        elements = []
        for change in changes:
            blob = self.pyGithubRepo.create_git_blob(CommitData.to_base64(change.content).decode(), "base64")
            elements.append(InputGitTreeElement(path=change.rel_file_path, mode="100644", type="blob", sha=blob.sha))
        return elements

    def create_pull_request(self, title: str, body: str, head: str, base: str, labels: List[str] = []) -> PullRequestInterface:
        try:
            pr = self.pyGithubRepo.create_pull(title=title, body=body, head=head, base=base)

            if len(labels) != 0:
                for alabel in labels:
                    new_label = self.__get_label(alabel)
                    current_labels = pr.get_labels()
                    if not any(new_label.name == current_label.name for current_label in current_labels):
                        pr.add_to_labels(new_label)
            else:
                self.__log.debug("No labels provided, PR will be unlabelled")

            self.__log.debug("Created pull request %s", str(pr))
            return GithubPullRequest(pr)
        except GithubException:
            self.__log.error("Unexpected exception caught while creating pull request", exc_info=1)
            return None

    def get_open_pulls(self, head: str = None, base: str = None) -> List[PullRequestInterface]:
        return self.__do_get_pulls("open", head, base)

    def get_closed_pulls(self, head: str = None, base: str = None) -> List[PullRequestInterface]:
        return self.__do_get_pulls("closed", head, base)

    def create_issue(self, title: str, body: str, labels: List[str] = []) -> IssueInterface:
        gh_labels = []
        for label in labels:
            gh_label = self.__get_label(label)
            if gh_label is not None:
                gh_labels.append(gh_label)

        if len(gh_labels)  == 0:
            gh_labels = GithubObject.NotSet
            self.__log.debug("The issue will be unlabelled, labels requested=%s, labels found=%s", str(labels), str(gh_labels))

        issue = None
        try:
            issue = GithubIssue(self.pyGithubRepo.create_issue(title=title, body=body, labels=gh_labels))
        except GithubException:
            self.__log.debug("Unexpected exception caught while creating issue '%s'", title, exc_info=1)
        return issue

    def get_head_branch_filter_key(self, branch_name: str) -> str:
        return self.get_owner() + ":" + branch_name

    def __do_get_pulls(self, state: str, head: str, base: str) -> List[PullRequestInterface]:
        the_list = []

        the_head = GithubObject.NotSet if head is None else head
        the_base = GithubObject.NotSet if base is None else base
        paginated_results = self.pyGithubRepo.get_pulls(state=state, head=the_head, base=the_base)

        for result in paginated_results:
            the_list.append(GithubPullRequest(result))

        return the_list

    def create_label(self, name: str, description: str, color: str, text_color: str) -> bool:
        return True if self.__get_label_or_create_it(name, color, description) is not None else False

    def get_pr_label(self) -> LabelData:
        return self.PR_LABEL

    def get_issue_label(self) -> LabelData:
        return self.ISSUE_LABEL

    def __get_label(self, name) -> Label :
        try:
            return self.pyGithubRepo.get_label(name)
        except:
            return None

    def __get_label_or_create_it(self, name: str, color: str, description: str) -> Label:
        """
        Gets a label given its name if it exists or creates it otherwise. None is returned if an unexpected exception is thrown.
        """
        try:
            return self.pyGithubRepo.get_label(name)
        except UnknownObjectException:
            try:
                self.__log.debug("Meterian pr label was not found, will be created")
                return self.pyGithubRepo.create_label(name, color, description)
            except GithubException:
                pass
        except GithubException:
                pass

        self.__log.debug("Unexpected error while creating label", exc_info=1)
        return None