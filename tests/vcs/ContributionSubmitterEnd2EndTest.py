import logging
import os

from pathlib import Path
from src.vcs.CommitAuthor import CommitAuthor
from src.vcs.PullRequestSubmitter import PullRequestSubmitter
from src.vcs.IssueSubmitter import IssueSubmitter
from src.vcs.VcsHubFactory import VcsHubFactory
from src.gitbot.GitbotMessageGenerator import GitbotMessageGenerator
from tests.vcs.End2EndTestFunctions import End2EndTestFunctions
from src.vcs.PrChangesGenerator import PrChangesGenerator

class ContributionSubmitterEnd2EndTest:

    def __init__(self, vcs_platform: str, api_base_url: str) -> None:
        End2EndTestFunctions.init_logging(logging.DEBUG)

        self.gitbot = GitbotMessageGenerator()
        self.vcs_platform = VcsHubFactory(vcs_platform, api_base_url).create()

    def should_submit_pull_request(self, work_dir: str, repository_name: str, repository_branch, author: CommitAuthor):

        repo = self.vcs_platform.get_repository(repository_name)
        always_open_prs = True if str(os.environ.get("TESTS_ALWAYS_OPEN_PRS", "")).lower() == "true" else False
        submitter = PullRequestSubmitter(work_dir, repo, author, always_open_prs)

        reports_and_changes = PrChangesGenerator.fetch_changed_manifests(Path(work_dir))

        for pr_report_path, changes in reports_and_changes.items():

            generator = PrChangesGenerator(Path(work_dir), changes)
            pr_change = generator.generate(pr_report_path)

            pr_text_content = self.gitbot.genMessage(
                pr_change.pr_report,
                {
                    GitbotMessageGenerator.AUTOFIX_OPT_KEY: True,
                    GitbotMessageGenerator.REPORT_OPT_KEY: True,
                    GitbotMessageGenerator.ISSUE_OPT_KEY: False
                },
                "issues,licenses"
            )

            submitter.submit(pr_text_content, pr_change, repository_branch)

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
