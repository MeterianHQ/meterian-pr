import os

from src.vcs.CommitAuthor import CommitAuthor
from tests.vcs.ContributionSubmitterEnd2EndTest import ContributionSubmitterEnd2EndTest
from gitlab.const import DEFAULT_URL

COMMIT_AUTHOR = CommitAuthor(
    os.environ["GITLAB_USERNAME"] if "GITLAB_USERNAME" in os.environ else "",
    os.environ["GITLAB_EMAIL"] if "GITLAB_EMAIL" in os.environ else ""
)

WORK_DIR = os.environ["TESTS_WORK_DIR"] if "TESTS_WORK_DIR" in os.environ else ""
REPO_NAME= os.environ["TESTS_REPO_NAME"] if "TESTS_REPO_NAME" in os.environ else ""
REPO_BRANCH= os.environ["TESTS_REPO_BRANCH"] if "TESTS_REPO_BRANCH" in os.environ else ""

if __name__ == "__main__":
    api_base_url = os.environ.get("GITLAB_API_BASE_URL", DEFAULT_URL)
    contribution_tester = ContributionSubmitterEnd2EndTest("gitlab", api_base_url)
    # TODO enable GitCli to figure repo name and branch on its own (will still need to be passed to method)
    contribution_tester.should_submit_pull_request(
        WORK_DIR,
        REPO_NAME,
        REPO_BRANCH,
        COMMIT_AUTHOR
    )

