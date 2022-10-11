import logging

from src.vcs.CommitAuthor import CommitAuthor
from src.vcs.PullRequestSubmitter import PullRequestSubmitter
from src.vcs.IssueSubmitter import IssueSubmitter
from src.vcs.VcsHubFactory import VcsHubFactory
from src.gitbot.GitbotMessageGenerator import GitbotMessageGenerator
from src.vcs.GitCli import GitCli
from tests.vcs.End2EndTestFunctions import End2EndTestFunctions

class ContributionSubmitterEnd2EndTest:

    def __init__(self, vcs_platform: str, api_base_url: str) -> None:
        End2EndTestFunctions.init_logging(logging.DEBUG)

        self.gitbot = GitbotMessageGenerator()
        self.vcs_platform = VcsHubFactory(vcs_platform, api_base_url).create()

    def should_submit_pull_request(self, work_dir: str, repository_name: str, repository_branch, author: CommitAuthor):
        pr_text_content = self.gitbot.genMessage(
            End2EndTestFunctions.read_JSON_report(work_dir + "/report.json"),
            {
                GitbotMessageGenerator.AUTOFIX_OPT_KEY: True,
                GitbotMessageGenerator.REPORT_OPT_KEY: True,
                GitbotMessageGenerator.ISSUE_OPT_KEY: False
            }
        )

        repo = self.vcs_platform.get_repository(repository_name)

        git = GitCli(work_dir)
        changes = git.get_changes()

        submitter = PullRequestSubmitter(work_dir, repo, author)
        submitter.submit(pr_text_content, changes, repository_branch, "report.pdf")

    def should_submit_issue(self, meterian_json_report_path: str, repository_name: str):
        issue_text_content = self.gitbot.genMessage(
            End2EndTestFunctions.read_JSON_report(meterian_json_report_path),
            {
                GitbotMessageGenerator.ISSUE_OPT_KEY: True,
                GitbotMessageGenerator.AUTOFIX_OPT_KEY: False,
                GitbotMessageGenerator.REPORT_OPT_KEY: False
            }
        )

        repo = self.vcs_platform.get_repository(repository_name)

        submitter = IssueSubmitter(self.vcs_platform, repo)
        submitter.submit(issue_text_content)