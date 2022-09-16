import abc

from typing import List
from .IssueInterface import IssueInterface
from .PullRequestInterface import PullRequestInterface

class RepositoryInterface(metaclass=abc.ABCMeta):

    METERIAN_LABEL_COLOR = "2883fa"
    METERIAN_BOT_ISSUE_LABEL_NAME = "meterian-bot-issue"
    METERIAN_BOT_ISSUE_LABEL_DESCRIPTION = "Issue opened to highlight outdated dependencies found by Meterian's analysis"
    METERIAN_BOT_PR_LABEL_NAME = "meterian-bot-pr"
    METERIAN_BOT_PR_LABEL_DESCRIPTION = "Pull requests that update dependency files based on Meterian's analysis"

    COMMITTER_NAME_KEY = "username"
    COMMITTER_EMAIL_KEY = "email"

    @classmethod
    def __subclasshook__(cls, subclass):
        return (hasattr(subclass, 'get_full_name') and
                callable(subclass.get_full_name) and
                hasattr(subclass, 'get_owner') and
                callable(subclass.get_owner) and
                hasattr(subclass, 'is_remote_branch') and
                callable(subclass.is_remote_branch) and
                hasattr(subclass, 'get_default_branch') and
                callable(subclass.get_default_branch) and
                hasattr(subclass, 'has_issues_enabled') and
                callable(subclass.has_issues_enabled) and
                hasattr(subclass, 'create_branch') and
                callable(subclass.create_branch) and
                hasattr(subclass, 'commit_change') and
                callable(subclass.commit_change) and
                hasattr(subclass, 'create_pull_request') and
                callable(subclass.create_pull_request) and
                hasattr(subclass, 'get_open_pulls') and
                callable(subclass.get_open_pulls) and
                hasattr(subclass, 'get_closed_pulls') and
                callable(subclass.get_closed_pulls) and
                hasattr(subclass, 'create_issue') and
                callable(subclass.create_issue) or
                NotImplemented)

    @abc.abstractmethod
    def get_full_name(self) -> str:
        """Gets the full name of the repository"""
        raise NotImplementedError

    @abc.abstractmethod
    def get_owner(self) -> str:
        """Gets the name of the owner of the repository"""
        raise NotImplementedError

    @abc.abstractmethod
    def is_remote_branch(self, name: str) -> bool:
        """Verifies if a branch exists remotely"""
        raise NotImplementedError

    @abc.abstractmethod
    def get_default_branch(self) -> str:
        """Gets the default branch"""
        raise NotImplementedError

    @abc.abstractmethod
    def has_issues_enabled(self) -> bool:
        """Checks whether issues are enabled on the repository"""
        raise NotImplementedError

    @abc.abstractmethod
    def create_branch(self, base_branch_name: str, ref_name: str) -> bool:
        """Creates branch"""
        raise NotImplementedError

    @abc.abstractmethod
    def commit_change(self, author: map, message: str, branch: str, path: str, content: bytes) -> bool:
        """Commits change to file on a branch"""
        raise NotImplementedError

    @abc.abstractmethod
    def create_pull_request(self, title: str, body: str, head: str, base: str) -> PullRequestInterface:
        """Creates a pull request"""
        raise NotImplementedError

    @abc.abstractmethod
    def get_open_pulls(self, head: str = None, base: str = None) -> List[PullRequestInterface]:
        """Gets a list of open pull requests possibly filtered by head branch and base branch"""
        raise NotImplementedError
    
    @abc.abstractmethod
    def get_closed_pulls(self, head: str = None, base: str = None) -> List[PullRequestInterface]:
        """Gets a list of closed pull requests possibly filtered by head branch and base branch"""
        raise NotImplementedError

    @abc.abstractmethod
    def create_issue(self, title: str, body: str) -> IssueInterface:
        """Create an issue with given title and body content"""
        raise NotImplementedError