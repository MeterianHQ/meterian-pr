import logging

from .RepositoryInterface import RepositoryInterface
from .VcsHubInterface import VcsHubInterface

class IssueOrchestrator:

    ISSUE_CONTENT_TITLE_KEY = "title"
    ISSUE_CONTENT_BODY_KEY = "message"

    __log = logging.getLogger("IssueOrchestrator")

    def __init__(self, vcs_hub: VcsHubInterface, repository: RepositoryInterface):
        self.vcs_hub = vcs_hub
        self.repo = repository

    def orchestrate(self, issue_text_content: dict):
        if issue_text_content[self.ISSUE_CONTENT_TITLE_KEY] == "":
            print("No problems were detected in your repository therefore no issues will be opened")
            return

        if not self.repo.has_issues_enabled():
            print("This repository does not have issues enabled, no issues will be opened")
            return
        
        issues = self.vcs_hub.get_issues(self.repo, issue_text_content[self.ISSUE_CONTENT_TITLE_KEY])
        if issues is None:
            print("Unable retreive issues")
            return

        for issue in issues:
            if issue_text_content[self.ISSUE_CONTENT_TITLE_KEY] == issue.get_title() and issue_text_content[self.ISSUE_CONTENT_BODY_KEY] == issue.get_body():
                if "open" == issue.get_state():
                    print("The issue has already been opened, view it here:\n" + issue.get_url())
                    return
                else:
                    print("The issue already exists and it has been closed, view it here:\n" + issue.get_url())
                    return
        
        new_issue = self.repo.create_issue(issue_text_content[self.ISSUE_CONTENT_TITLE_KEY], issue_text_content[self.ISSUE_CONTENT_BODY_KEY])
        if not new_issue:
            print("Unable to create new issue")
        else:
            print("A new issue has been opened, view it here:\n" + new_issue.get_url())