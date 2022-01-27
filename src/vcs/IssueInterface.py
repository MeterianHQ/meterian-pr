import abc

class IssueInterface(metaclass=abc.ABCMeta):

    @classmethod
    def __subclasshook__(cls, subclass):
        return (hasattr(subclass, 'get_url') and
                callable(subclass.get_url) and
                hasattr(subclass, 'get_title') and
                callable(subclass.get_title) and
                hasattr(subclass, 'get_body') and
                callable(subclass.get_body) and
                hasattr(subclass, 'get_state') and
                callable(subclass.get_state) or
                NotImplemented)

    @abc.abstractmethod
    def get_url(self) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def get_title(self) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def get_body(self) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def get_state(self) -> str:
        raise NotImplementedError