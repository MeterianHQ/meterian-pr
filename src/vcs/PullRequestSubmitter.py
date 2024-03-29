import logging
import uuid
import time
import hashlib

from .PullRequestInterface import PullRequestInterface
from .RepositoryInterface import RepositoryInterface
from .BranchHelper import BranchHelper
from .CommitAuthor import CommitAuthor
from .PrChangesGenerator import FilesystemChange
from .PrChangesGenerator import PrChange
from pathlib import Path
from typing import List

class PullRequestSubmitter:

    PR_BRANCH_NAME_PREFIX = "meterian-bot/pr/"

    PR_CONTENT_TITLE_KEY = "title"
    PR_CONTENT_BODY_KEY = "message"

    __COMMIT_RETRY_LIMIT = 10

    __log = logging.getLogger("PullRequestSubmitter")

    def __init__(self, workdir:str, repository: RepositoryInterface, author: CommitAuthor, always_open_prs: bool = False):
        self.workdir = workdir
        self.repo = repository
        self.branch_helper = BranchHelper()
        self.author = author
        self.always_open_prs = always_open_prs

    def submit(self, pr_text_content: dict, pr_change: PrChange, base_branch: str, pdf_report_path: str = None) -> PrChange:
        if self.__log.level == logging.DEBUG:
            self.__log.debug("Changes detected were:")
            for fs_change in pr_change.filesystem_changes:
                self.__log.debug("- %s", str(fs_change.rel_file_path))

        labels = self.__get_pr_labels()

        changes = pr_change.filesystem_changes
        if pdf_report_path:
            self.__log.debug("Requested addition of PDF report in PR, reading contents...")
            pdf_report_contents = self.__read_file_bytes(str(Path(self.workdir, pdf_report_path).absolute()))
            self.__log.debug("Read contents of PDF report %s", pdf_report_path)
            changes.append(FilesystemChange(pdf_report_path, pdf_report_contents))

        pr_branch_ref = self.__create_pr_branch_ref(base_branch, pr_change)
        if pr_branch_ref is None:
            print(f"Invalid branch ref was generated ({pr_branch_ref}), hence no PR will be will be opened")
            return None

        if not self.repo.create_branch(base_branch, self.branch_helper.as_branch_name(pr_branch_ref)):
            print("Unable to create PR branch %s" % self.branch_helper.as_branch_name(pr_branch_ref))
            return None

        opened_prs = self.__get_pulls(self.repo.get_owner(), self.branch_helper.as_branch_name(pr_branch_ref), base_branch, self.repo.get_open_pulls)
        closed_prs = self.__get_pulls(self.repo.get_owner(), self.branch_helper.as_branch_name(pr_branch_ref), base_branch, self.repo.get_closed_pulls)
        if len(opened_prs) > 0 or len(closed_prs) > 0:
            self.__log.debug("Pull request for PR change %s has already been opened", str(pr_change))
            return None

        commit_message = self.__generate_commit_message(pr_change)

        were_changes_committed = self.__do_commit(commit_message, self.branch_helper.as_branch_name(pr_branch_ref), changes)
        if were_changes_committed:
            new_pr = self.repo.create_pull_request(pr_text_content[self.PR_CONTENT_TITLE_KEY], pr_text_content[self.PR_CONTENT_BODY_KEY], self.branch_helper.as_branch_name(pr_branch_ref),
                                                    base_branch, labels)
            if new_pr:
                self.__log.debug("Successful submission (%s)", new_pr.get_url())
                pr_change.set_pr(new_pr)
            else:
                self.__log.debug("Unexpected, unsuccessful submission")
        else:
            self.__log.error("Changes were not committed, unable to proceed with submission")

        if pr_change.pr:
            return pr_change
        else:
            return None

    def __generate_commit_message(self, pr_change: PrChange):
        msg = "Autofix"
        deps = pr_change.dependencies if pr_change.dependencies is not None else []
        if len(deps) > 0:
            msg += "\n\n"
        for dep in deps:
            msg += "- updated " + dep.name + " from " + dep.version + " to " + dep.new_version + "\n"
        return msg

    def __get_pr_labels(self) -> List[str]:
        label = self.repo.get_pr_label()
        label_available = self.repo.create_label(label.name, label.description, label.color, label.text_color)
        if label_available:
            return [self.repo.get_pr_label().name]
        else:
            return []

    def __get_pulls(self, owner: str, head_branch: str, base_branch: str, pulls_supplier):
        self.__log.debug("Getting pulls through pulls supplier %s", str(pulls_supplier))

        if owner is None or owner == "":
            pulls = pulls_supplier(head_branch, base_branch)
            self.__log.debug("Retrieved PRs %s with head=%s and base=%s", pulls, head_branch, base_branch)
            return pulls
        else:
            self.__log.debug("Attempting to fetch pulls with head branch filter key")
            head_branch_filter = self.repo.get_head_branch_filter_key(self.branch_helper.as_branch_name(head_branch))
            pulls = pulls_supplier(head_branch_filter, base_branch)
            self.__log.debug("Retrieved PRs %s with head=%s and base=%s", pulls, head_branch_filter, base_branch)
            return pulls

    def __edit_pr(self, pr: PullRequestInterface, title: str, body: str):
        """Helper method to only edit pr title and body where these actually change"""
        the_title = None
        if title:
            if title !=  pr.get_title():
                the_title = title

        the_body = None
        if body:
            if body !=  pr.get_body():
                the_body = body

        if the_body or the_title:
            pr.edit(title=the_title, body=the_body)

    def __do_commit(self, commit_message: str, branch_name: str, changes: List[FilesystemChange]) -> bool:
        times_retried = 0
        res = self.repo.commit_changes(self.author, commit_message, branch_name, changes)
        while res == False and times_retried < self.__COMMIT_RETRY_LIMIT:
            time.sleep(1)
            res = self.repo.commit_changes(self.author, commit_message, branch_name, changes)
            times_retried+=1

        if res == False and times_retried == self.__COMMIT_RETRY_LIMIT:
            fs_changes = []
            for change in changes:
                fs_changes.append(change.rel_file_path)

            self.__log.warning("Maximum retry limit exceeded, failed to commit changes to %s on branch %s", str(fs_changes), branch_name)

        return res

    def __read_file_bytes(self, path: str) -> bytes:
        file = open(path, "rb")
        bytes_contents = file.read()
        file.close()
        return bytes_contents

    def __create_pr_branch_ref(self, base_branch: str, pr_change: PrChange) -> str:
        pr_branch_name = self.PR_BRANCH_NAME_PREFIX
        if base_branch != self.repo.get_default_branch():
            pr_branch_name = base_branch + "_" + pr_branch_name

        pr_branch_name += self.__generate_uuid(pr_change)
        pr_branch_name = self.branch_helper.to_branch_ref(pr_branch_name)

        self.__log.debug("Generated PR branch ref %s", str(pr_branch_name))
        return pr_branch_name

    def __generate_uuid(self, pr_change: PrChange) -> str:
        if self.always_open_prs:
            return str(uuid.uuid4())

        deps_seed = ""
        deps = pr_change.dependencies
        deps.sort()
        for dep in deps:
            deps_seed += dep.name+dep.version

        manifests_seed = b''
        manifests = pr_change.filesystem_changes
        manifests.sort()
        for manifest in manifests:
            manifests_seed += manifest.content

        seed = deps_seed.encode("utf-8")+manifests_seed
        if pr_change.manifest_info:
            seed += Path(pr_change.manifest_info["solution"]["path"]).name.encode("utf-8")

        m = hashlib.md5()
        m.update(seed)
        return str(uuid.UUID(m.hexdigest()))
