import abc

from typing import List
from .IssueInterface import IssueInterface
from .RepositoryInterface import RepositoryInterface

class VcsHubInterface(metaclass=abc.ABCMeta):
    @classmethod
    def __subclasshook__(cls, subclass):
        return (hasattr(subclass, 'get_repository') and
                callable(subclass.get_repository) and
                hasattr(subclass, 'get_issues') and
                callable(subclass.get_issues) or
                NotImplemented)

    @abc.abstractmethod
    def get_repository(self, name: str) -> RepositoryInterface:
        """Fetches and loads a repository by its name"""
        raise NotImplementedError

    @abc.abstractmethod
    def get_issues(self, repository: RepositoryInterface, title: str) -> List[IssueInterface]:
        """Searches for a repository issue by its title"""
        raise NotImplementedError