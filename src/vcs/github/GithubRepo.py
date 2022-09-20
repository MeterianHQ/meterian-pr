import logging
from sys import exc_info
import traceback

from github.GithubException import GithubException
from github.GithubException import UnknownObjectException
from github.Label import Label
from github.Repository import Repository as PyGithubRepository
from github.InputGitAuthor import InputGitAuthor
from src.vcs.CommitAuthor import CommitAuthor
from .GithubIssue import GithubIssue
from ..PullRequestInterface import PullRequestInterface
from ..RepositoryInterface import RepositoryInterface
from ..IssueInterface import IssueInterface
from .GithubPullRequest import GithubPullRequest
from ..BranchHelper import BranchHelper
from typing import List
from github import GithubObject

class GithubRepo(RepositoryInterface):

    DEFAULT_COMMITTER = CommitAuthor(
        "meterian-bot",
        "bot.github@meterian.io"
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

    def create_branch(self, base_branch_name: str, ref_name: str) -> bool:
        try:
            if any(self.branch_helper.as_branch_name(ref_name) == repo_branch.name for repo_branch in self.pyGithubRepo.get_branches()):
                self.__log.debug("Branch %s already exists it will not be created", self.branch_helper.as_branch_name(ref_name))
                return True

            source_branch = self.pyGithubRepo.get_branch(base_branch_name)
            self.pyGithubRepo.create_git_ref(ref=ref_name, sha=source_branch.commit.sha)
            self.__log.debug("Created new branch %s", self.branch_helper.as_branch_name(ref_name))
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

    def create_pull_request(self, title: str, body: str, head: str, base: str) -> PullRequestInterface:
        try:
            pr = self.pyGithubRepo.create_pull(title=title, body=body, head=head, base=base)

            meterian_pr_label = self.__get_label(self.METERIAN_BOT_PR_LABEL_NAME, self.METERIAN_LABEL_COLOR, self.METERIAN_BOT_PR_LABEL_DESCRIPTION)
            if (meterian_pr_label is not None):
                if meterian_pr_label not in pr.get_labels():
                    pr.add_to_labels(meterian_pr_label)
                else:
                    self.__log.debug("Label was already found on PR?")
            else:
                self.__log.warning("Could not retrieve Meterian PR label, PR will be unlabelled")

            self.__log.debug("Created pull request %s", str(pr))
            return GithubPullRequest(pr)
        except GithubException:
            self.__log.error("Unexpected exception caught while creating pull request", exc_info=1)
            return None

    def get_open_pulls(self, head: str = None, base: str = None) -> List[PullRequestInterface]:
        return self.__do_get_pulls("open", head, base)

    def get_closed_pulls(self, head: str = None, base: str = None) -> List[PullRequestInterface]:
        return self.__do_get_pulls("closed", head, base)

    def create_issue(self, title: str, body: str) -> IssueInterface:
        meterian_issue_label = self.__get_label(self.METERIAN_BOT_ISSUE_LABEL_NAME, self.METERIAN_LABEL_COLOR, self.METERIAN_BOT_ISSUE_LABEL_DESCRIPTION)

        labels = [meterian_issue_label] if meterian_issue_label else GithubObject.NotSet
        if labels == GithubObject.NotSet:
            self.__log.warning("Could not retrieve/create Meterian issue label, the issue will be unlabelled")

        issue = None
        try:
            issue = GithubIssue(self.pyGithubRepo.create_issue(title=title, body=body, labels=labels))
        except GithubException:
            self.__log.debug("Unexpected exception caught while creating issue '%s'", title, exc_info=1)
        return issue

    def __do_get_pulls(self, state: str, head: str, base: str) -> List[PullRequestInterface]:
        the_list = []

        the_head = GithubObject.NotSet if head is None else head
        the_base = GithubObject.NotSet if base is None else base
        paginated_results = self.pyGithubRepo.get_pulls(state=state, head=the_head, base=the_base)

        for result in paginated_results:
            the_list.append(GithubPullRequest(result))

        return the_list

    def __get_label(self, name: str, color_if_not_found: str, description_if_not_found: str) -> Label:
        """
        Gets a label given its name if it's exists or creates it of otherwise. None is returned if an unexpected exception is thrown.
        """
        try:
            return self.pyGithubRepo.get_label(name)
        except UnknownObjectException:
            try:
                self.__log.debug("Meterian pr label was not found, will be created")
                return self.pyGithubRepo.create_label(name, color_if_not_found, description_if_not_found)
            except GithubException:
                pass
        except GithubException:
                pass

        self.__log.debug("Unexpected error while creating label", exc_info=1)
        return None