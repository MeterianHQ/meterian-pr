import os

from src.vcs.CommitAuthor import CommitAuthor
from tests.vcs.ContributionSubmitterEnd2EndTest import ContributionSubmitterEnd2EndTest
from github import MainClass
from tests.vcs.End2EndTestFunctions import End2EndTestFunctions

COMMIT_AUTHOR = CommitAuthor(
    os.environ["GITHUB_USERNAME"] if "GITHUB_USERNAME" in os.environ else End2EndTestFunctions.raise_unset_envvar_exception("GITHUB_USERNAME"),
    os.environ["GITHUB_EMAIL"] if "GITHUB_EMAIL" in os.environ else End2EndTestFunctions.raise_unset_envvar_exception("GITHUB_EMAIL")
)

WORK_DIR = os.environ["TESTS_PROJECT_DIR"] if "TESTS_PROJECT_DIR" in os.environ else End2EndTestFunctions.raise_unset_envvar_exception("TESTS_PROJECT_DIR")
REPO_NAME= os.environ["TESTS_REPO_NAME"] if "TESTS_REPO_NAME" in os.environ else End2EndTestFunctions.raise_unset_envvar_exception("TESTS_REPO_NAME")
REPO_BRANCH= os.environ["TESTS_REPO_BRANCH"] if "TESTS_REPO_BRANCH" in os.environ else End2EndTestFunctions.raise_unset_envvar_exception("TESTS_REPO_BRANCH")

if __name__ == "__main__":
    api_base_url = os.environ.get("GITHUB_API_BASE_URL", MainClass.DEFAULT_BASE_URL)
    contribution_tester = ContributionSubmitterEnd2EndTest("github", api_base_url)
    contribution_tester.should_submit_pull_request(
        WORK_DIR,
        REPO_NAME,
        REPO_BRANCH,
        COMMIT_AUTHOR
    )
