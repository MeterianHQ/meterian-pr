import os
from tests.vcs.ContributionSubmitterEnd2EndTest import ContributionSubmitterEnd2EndTest

WORK_DIR = os.environ["TESTS_WORK_DIR"] if "TESTS_WORK_DIR" in os.environ else ""
REPO_NAME= os.environ["TESTS_REPO_NAME"] if "TESTS_REPO_NAME" in os.environ else ""

if __name__ == "__main__":
    contribution_tester = ContributionSubmitterEnd2EndTest("gitlab")
    contribution_tester.should_submit_issue(WORK_DIR + "/report.json", REPO_NAME)
