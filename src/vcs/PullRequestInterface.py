import abc

class PullRequestInterface(metaclass=abc.ABCMeta):

    @classmethod
    def __subclasshook__(cls, subclass):
        return (hasattr(subclass, 'edit') and
                callable(subclass.edit) and
                hasattr(subclass, 'get_url') and
                callable(subclass.get_url) and
                hasattr(subclass, 'get_title') and
                callable(subclass.get_title) and
                hasattr(subclass, 'get_body') and
                callable(subclass.get_body) or
                NotImplemented)

    @abc.abstractmethod
    def edit(self, title: str = None, body: str = None):
        """Edits title and/or body"""
        raise NotImplementedError

    @abc.abstractmethod
    def get_url(self) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def get_title(self) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def get_body(self) -> str:
        raise NotImplementedError