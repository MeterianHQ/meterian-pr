import os

from src.vcs.CommitAuthor import CommitAuthor
from tests.vcs.ContributionSubmitterEnd2EndTest import ContributionSubmitterEnd2EndTest
from github import MainClass

COMMIT_AUTHOR = CommitAuthor(
    os.environ["GITHUB_USERNAME"] if "GITHUB_USERNAME" in os.environ else "",
    os.environ["GITHUB_EMAIL"] if "GITHUB_EMAIL" in os.environ else ""
)

WORK_DIR = os.environ["TESTS_WORK_DIR"] if "TESTS_WORK_DIR" in os.environ else ""
REPO_NAME= os.environ["TESTS_REPO_NAME"] if "TESTS_REPO_NAME" in os.environ else ""
REPO_BRANCH= os.environ["TESTS_REPO_BRANCH"] if "TESTS_REPO_BRANCH" in os.environ else ""

if __name__ == "__main__":
    api_base_url = os.environ.get("GITHUB_API_BASE_URL", MainClass.DEFAULT_BASE_URL)
    contribution_tester = ContributionSubmitterEnd2EndTest("github", api_base_url)
    contribution_tester.should_submit_pull_request(
        WORK_DIR,
        REPO_NAME,
        REPO_BRANCH,
        COMMIT_AUTHOR
    )
