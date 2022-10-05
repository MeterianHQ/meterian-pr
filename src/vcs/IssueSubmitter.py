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
        if issue_text_content[self.ISSUE_CONTENT_TITLE_KEY] == "":
            print("No problems were detected in your repository therefore no issues will be opened")
            return

        if not self.repo.has_issues_enabled():
            print("This repository does not have issues enabled, no issues will be opened")
            return

        issues = self.vcs_hub.get_issues(self.repo, issue_text_content[self.ISSUE_CONTENT_TITLE_KEY])
        if issues is None:
            print("Unable to retrieve issues")
            return

        for issue in issues:
            if issue_text_content[self.ISSUE_CONTENT_TITLE_KEY] == issue.get_title() and issue_text_content[self.ISSUE_CONTENT_BODY_KEY] == issue.get_body():
                if issue.is_open():
                    print("The issue has already been opened, view it here:\n" + issue.get_url())
                    return
                else:
                    print("The issue already exists and it has been closed, view it here:\n" + issue.get_url())
                    return

        labels = self.__get_issue_labels()
        new_issue = self.repo.create_issue(issue_text_content[self.ISSUE_CONTENT_TITLE_KEY], issue_text_content[self.ISSUE_CONTENT_BODY_KEY], labels)
        if not new_issue:
            print("Unable to create new issue")
        else:
            print("A new issue has been opened, view it here:\n" + new_issue.get_url())

    def __get_issue_labels(self) -> List[str]:
        label = self.repo.get_issue_label()
        label_available = self.repo.create_label(label.name, label.description, label.color, label.text_color)
        if label_available:
            return [self.repo.get_issue_label().name]
        else:
            return []