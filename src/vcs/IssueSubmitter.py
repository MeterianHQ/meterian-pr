import logging

from .RepositoryInterface import RepositoryInterface
from .VcsHubInterface import VcsHubInterface
from typing import List

class IssueSubmitter:

    ISSUE_CONTENT_TITLE_KEY = "title"
    ISSUE_CONTENT_BODY_KEY = "message"

    __log = logging.getLogger("IssueSubmitter")

    def __init__(self, vcs_hub: VcsHubInterface, repository: RepositoryInterface):
        self.vcs_hub = vcs_hub
        self.repo = repository

    def submit(self, issue_text_content: dict):
        self.__log.info("Starting process to submit issue with title '" + issue_text_content[self.ISSUE_CONTENT_TITLE_KEY] + "' on repo: " + str(self.repo.get_full_name()))

        if issue_text_content[self.ISSUE_CONTENT_TITLE_KEY] == "":
            self.__log.info("No problems were detected in your repository therefore no issues will be submitted")
            return None

        issues = self.vcs_hub.get_issues(self.repo, issue_text_content[self.ISSUE_CONTENT_TITLE_KEY])
        if issues is None:
            self.__log.error("Failed to retrieve issues from your repository")
            return None

        for issue in issues:
            if issue_text_content[self.ISSUE_CONTENT_TITLE_KEY] == issue.get_title() and issue_text_content[self.ISSUE_CONTENT_BODY_KEY] == issue.get_body():
                if issue.is_open():
                    self.__log.info("The issue has already been opened, view it here:\n" + issue.get_url())
                    return None
                else:
                    self.__log.info("The issue already exists and it has been closed, view it here:\n" + issue.get_url())
                    return None

        labels = self.__get_issue_labels()

        new_issue = self.repo.create_issue(issue_text_content[self.ISSUE_CONTENT_TITLE_KEY], issue_text_content[self.ISSUE_CONTENT_BODY_KEY], labels)
        print("New issue '" + issue_text_content[self.ISSUE_CONTENT_TITLE_KEY] + "' on repo: " + str(self.repo.get_full_name()))
        return new_issue

    def __get_issue_labels(self) -> List[str]:
        label = self.repo.get_issue_label()
        label_available = self.repo.create_label(label.name, label.description, label.color, label.text_color)
        if label_available:
            return [self.repo.get_issue_label().name]
        else:
            return []