import logging

from ..PullRequestInterface import PullRequestInterface
from gitlab.v4.objects.merge_requests import ProjectMergeRequest

class GitlabMergeRequest(PullRequestInterface):

    __log = logging.getLogger("GitlabMergeRequest")

    def __init__(self, pyMergeRequest: ProjectMergeRequest):
        self.pyMergeRequest = pyMergeRequest
        self.title = self.pyMergeRequest.title
        self.body = self.pyMergeRequest.description
        self.url = self.pyMergeRequest.web_url

    def edit(self, title: str = None, body: str = None):
        self.pyMergeRequest.title = self.__parseNone(title, self.title)
        self.pyMergeRequest.description = self.__parseNone(body, self.body)
        self.pyMergeRequest.save()

    def get_url(self) -> str:
        return self.url

    def get_title(self) -> str:
        return self.title

    def get_body(self) -> str:
        return self.body

    def __str__(self):
        return "GitlabMergeRequest [ title=" + self.title + ", url=" + self.url + ", body=" + self.body + " ]"

    def __parseNone(self, text: str, defVal: str) -> str:
        return defVal if text is None else text