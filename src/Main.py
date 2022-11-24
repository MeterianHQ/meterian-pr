import argparse
import json
import sys
import logging
import http.client
import os
import shutil
import requests

from vcs.IssueSubmitter import IssueSubmitter
from vcs.GitCli import GitCli
from vcs.VcsHubFactory import VcsHubFactory
from vcs.github.GithubRepo import GithubRepo
from vcs.gitlab.GitlabProject import GitlabProject
from vcs.PullRequestSubmitter import PullRequestSubmitter
from gitbot.GitbotMessageGenerator import GitbotMessageGenerator
from vcs.CommitAuthor import CommitAuthor
from pathlib import Path
from github import MainClass
from gitlab.const import DEFAULT_URL
from typing import List
from vcs.PrChangesGenerator import PrChangesGenerator
from vcs.PrChangesGenerator import PrChange
from datetime import datetime

VCS_PLATFORMS = [ "github", "gitlab" ] #, "bitbucket" ]

DEFAULT_AUTHORS_BY_PLATFORM = {
    "github": GithubRepo.DEFAULT_COMMITTER,
    "gitlab": GitlabProject.DEFAULT_COMMITTER
    # ,"bitbucket": BitbucketRepo.DEFAULT_COMMITTER_DATA
}

DEFAULT_API_BASE_URL_BY_PLATFORM = {
    "github": MainClass.DEFAULT_BASE_URL,
    "gitlab": DEFAULT_URL
}

ACTIONS = [ "PR", "ISSUE" ]

WORK_DIR = None

PR_REPORT_FILENAME_PREFIX = ".pr_report_"

VERSION = "1.1.14"

METERIAN_ENV = os.environ["METERIAN_ENV"] if "METERIAN_ENV" in os.environ else "www"

log = logging.getLogger("Main")

class HelpingParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.stderr.write('\n')
        sys.exit(-1)

def logHttpRequests():
    http.client.HTTPConnection.debuglevel = 1

    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.INFO)
    requests_log.propagate = True

    logging.debug('Full debug log for HTTP requests enabled')

def parse_args():
    parser = HelpingParser()
    parser.add_argument("workdir", help="The path to the work directory")
    parser.add_argument("action", help="The action you want to perform as a result of the autofix results\n (i.e. PR: open a pull request on the a repository; ISSUE: open an issue on a repository)")
    parser.add_argument("repository", help="The name of the remote repository\n (i.e. aws/aws-cli)")
    parser.add_argument("branch", help="The name of the current branch (must be a branch available remotely)")

    parser.add_argument(
        "-v",
        "--vcs",
        default="github",
        metavar="PLATFORM",
        help="The version control system platform where your repository is hosted\n (i.e. github) (default is github) (supported: " + str(VCS_PLATFORMS) + ")"
    )

    parser.add_argument(
        "--api-base-url",
        metavar="URL",
        help="Allows to override the API base URL for the chosen version control system platform"
    )

    parser.add_argument(
        "--record-prs",
        action='store_true',
        help="Allows to record information about pull requests opened on the Meterian report (note: a valid Meterian authentication token must be set in the environment)"
    )

    parser.add_argument(
        "--always-open-prs",
        action='store_true',
        help="By default identical pull requests are not opened, with this flag you can override this behaviour to always open PRs"
    )

    parser.add_argument(
        "--json-report",
        metavar="PATH",
        help="Allows to specify the path to the Meterian JSON report. This option is required if 'ISSUE' is the action being used (view help for more details on actions)"
    )

    parser.add_argument(
        "--with-pdf-report",
        metavar="PATH",
        help="Allows to specify the path to the Meterian PDF report to add as part of the pull request if any are opened. This option is considered only if 'PR' is the action being used (view help for more details on actions)"
    )

    parser.add_argument(
        "--commit-author-username",
        metavar="USERNAME",
        help="Allows to specify a different commit author username to use (by default the Meterian bot username is used)"
    )

    parser.add_argument(
        "--commit-author-email",
        metavar="EMAIL",
        help="Allows to specify a different commit author email address to use (by default the Meterian bot email address is used)"
    )

    parser.add_argument(
        "-l",
        "--log",
        default="warning",
        metavar="LOGLEVEL",
        help="Sets the logging level (default is warning)"
    )

    parser.add_argument(
        "--version",
        action="version",
        help="Show version and exit",
        version=VERSION
    )

    return parser.parse_args()

def initLogging(args):
    levels = {
        'critical': logging.CRITICAL,
        'error': logging.ERROR,
        'warn': logging.WARNING,
        'warning': logging.WARNING,
        'info': logging.INFO,
        'debug': logging.DEBUG
    }

    level = levels.get(args.log.lower())
    if level is None:
        raise ValueError("Invalid log level requested - must be one of the following " + levels.keys())

    logging.basicConfig(
        level = level,
        format='%(asctime)-15s - %(levelname)-6s - %(name)s :: %(message)s'
    )

    if level == logging.DEBUG:
        logHttpRequests()
    else:
        logging.getLogger('requests').setLevel(logging.WARNING)

    loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]
    for logger in loggers:
        logger.setLevel(level)
    
    log.debug('Logging initiated')

def is_tool_installed(tool_name):
    return shutil.which(tool_name) is not None

def generate_contribution_content(gitbot: GitbotMessageGenerator, meterian_json_report: dict, options: dict, exclusions: str = None) -> dict:
    content = gitbot.genMessage(meterian_json_report, options, exclusions)
    return content

def get_commit_author_details(args):
    username = DEFAULT_AUTHORS_BY_PLATFORM[args.vcs].username
    email = DEFAULT_AUTHORS_BY_PLATFORM[args.vcs].email

    if args.commit_author_username:
        username = args.commit_author_username
    if args.commit_author_email:
        email = args.commit_author_email

    author = CommitAuthor(username, email)
    log.info("Commit author to be employed is: %s", author)
    return author

def create_vcs_platform(args):
    api_base_url = DEFAULT_API_BASE_URL_BY_PLATFORM[args.vcs]

    if args.api_base_url:
        api_base_url = args.api_base_url
        log.info("Overridden API base URL for %s with %s", args.vcs, api_base_url)

    vcs = VcsHubFactory(args.vcs, api_base_url).create()

    return vcs

def record_pr_info_on_report(meterian_project_id: str, pr_infos_by_dep: dict, open_prs_links: List[str]):
    print("Recording PR information to report")
    log.debug("Requested to record PR information. Prepping data...")
    data = {}
    data["createdAt"] = datetime.strftime(datetime.now(), '%d/%m/%Y-%H:%M:%S')
    data["entries"] = []
    data["openPrLinks"] = open_prs_links
    for dependency, pr_infos in pr_infos_by_dep.items():
        entry = {}
        entry["dependency"] = dependency.to_payload()["dependency"]
        entry["prs"] = pr_infos
        data["entries"].append(entry)

    json_data = json.dumps(data) 
    log.debug("Data prepped: %s", json_data)

    log.debug("Recording data...")
    meterian_token = os.environ.get("METERIAN_API_TOKEN", None)
    headers = {"Content-Type": "application/json", "Authorization": "token " + str(meterian_token)}
    url = "https://" + METERIAN_ENV + ".meterian.com/api/v1/reports/" + meterian_project_id + "/prs"
    response = requests.post(url, data = json_data, headers = headers)

    if response.status_code == 200:
        log.debug("PR data successfully recorded to report (PID: %s)", str(meterian_project_id))
        print("PR data successfully recorded to report")
    else:
        print("Failed to record PR data")
        log.error("Could not record PR data\nStatus code: %s\nResponse: %s", str(response.status_code), str(response.text))

def load_pr_summary_report(dir) -> dict:
    try:
        stream = open(Path(dir, ".pr_summary.json"), encoding="utf-8")
        pr_report = json.load(stream)
        stream.close()
        return pr_report
    except:
        log.debug("Unexpected error loading PR summary report %s", str(Path(dir, ".pr_summary.json")), exc_info=1)
        return None

def submit_pr(pr_change: PrChange, branch: str, pr_text_content: dict, meterian_pdf_report_path: str, record_prs: bool, opened_prs: list, pr_infos_by_dep: dict):
    pr_change = pr_submitter.submit(pr_text_content, pr_change, branch, meterian_pdf_report_path)
    if pr_change:
        opened_prs.append(pr_change)

        if record_prs == True:
            for dependency in pr_change.dependencies:
                pr_info = { "title": pr_change.pr.get_title(), "url": pr_change.pr.get_url() }
                pr_infos = pr_infos_by_dep.get(dependency, [])
                if pr_info not in pr_infos:
                    pr_infos.append(pr_info)
                    pr_infos_by_dep[dependency] = pr_infos

if __name__ ==  "__main__":
    print()

    print("Meterian-pr v" + str(VERSION))

    print()
    args = parse_args()
    initLogging(args)

    WORK_DIR = args.workdir
    if os.path.exists(WORK_DIR) is False:
        sys.stderr.write("Work directory %s does not exist\n" % WORK_DIR)
        sys.stderr.write("\n")
        sys.exit(-1)
    else:
        WORK_DIR = str(os.path.abspath(WORK_DIR))

    if args.vcs not in VCS_PLATFORMS:
        sys.stderr.write("Invalid version control system: %s\n" % args.vcshub)
        sys.stderr.write("Available ones are: %s\n" % str(VCS_PLATFORMS))
        sys.stderr.write("\n")
        sys.exit(-1)

    if args.action not in ACTIONS:
        sys.stderr.write("Invalid action: %s\n" % args.action)
        sys.stderr.write("Available actions are: %s\n" % str(ACTIONS))
        sys.stderr.write("\n")
        sys.exit(-1)

    meterian_pdf_report_path = None
    if args.with_pdf_report:
        if args.action == "PR":
            meterian_pdf_report_path = os.path.abspath(args.with_pdf_report)
            if os.path.exists(meterian_pdf_report_path) is False:
                sys.stderr.write("Path for PDF report " + meterian_pdf_report_path + " does not exists\n")
                sys.stderr.write("\n")
                sys.exit(-1)
            else:
                if Path(WORK_DIR) in Path(meterian_pdf_report_path).parents:
                    log.debug("Specified PDF report %s relative to project dir %s", meterian_pdf_report_path, str(WORK_DIR))
                    meterian_pdf_report_path = str(Path(meterian_pdf_report_path).relative_to(WORK_DIR))
                    log.debug("Will use relative path of PDF report %s", meterian_pdf_report_path)
                else:
                    log.warning("PDF report %s will be ignored as it's not relative to project in directory %s", meterian_pdf_report_path, str(WORK_DIR))
        elif args.action == "ISSUE":
            log.warning("Unsupported option '--with-pdf-report' being used with action 'ISSUE, it will be ignored")

    record_prs = False
    if args.record_prs is not None and args.record_prs == True:
        if "METERIAN_API_TOKEN" in os.environ:
            record_prs = True
        else:
            log.warning("A Meterian API token was not found in your environment, PRs information won't be recorded")

    vcsPlatform = create_vcs_platform(args)
    if vcsPlatform is None:
        sys.stderr.write("Unable to create an instance for the " +args.vcs.title()+ " platform, ensure appropriate access token environment variables are appropriately set\n")
        sys.stderr.write("Ensure these environment variables are set per platform:\n")

        for key, value in VcsHubFactory.PLATFORMS_AND_ENVVARS.items():
            sys.stderr.write(key + " ~> " + value + "\n")
    
        sys.stderr.write("\n")
        sys.exit(-1)

    if not is_tool_installed("git"):
        sys.stderr.write("Required tool git has not been detected in the environment\n")
        sys.stderr.write("\n")
        sys.exit(-1)

    remote_repo = vcsPlatform.get_repository(args.repository)
    if remote_repo:
        if not remote_repo.is_remote_branch(args.branch):
            sys.stderr.write("Unable to find branch %s remotely\n" % args.branch)
            sys.stderr.write("\n")
            sys.exit(-1)
    else:
        sys.stderr.write("Repository %s was not found\n" % args.repository)
        sys.stderr.write("\n")
        sys.exit(-1)
    

    gitbot_msg_generator = GitbotMessageGenerator()

    if "PR" == args.action:
        reports_and_changes = PrChangesGenerator.fetch_changed_manifests(Path(WORK_DIR))
        if len(reports_and_changes) == 0:
            sys.stderr.write("No changes were detected in your repository in order to open PRs\n\n")
            sys.exit(-1)

        a_report = list(reports_and_changes.keys())[0]
        meterian_project_id = PrChangesGenerator.parse_pid(a_report)
        opened_prs = []
        pr_infos_by_dep = {}
        author = get_commit_author_details(args)
        always_open_prs = args.always_open_prs is not None and args.always_open_prs == True
        pr_submitter = PullRequestSubmitter(WORK_DIR, remote_repo, author, always_open_prs)

        for pr_report_path, changes in reports_and_changes.items():
            log.debug("Prepping PR with report %s and changes %s", pr_report_path, changes)

            generator = PrChangesGenerator(Path(WORK_DIR), changes)
            pr_change = generator.generate(pr_report_path)

            if pr_change:
                pr_text_content = generate_contribution_content(gitbot_msg_generator, pr_change.pr_report, {
                    GitbotMessageGenerator.AUTOFIX_OPT_KEY: True,
                    GitbotMessageGenerator.REPORT_OPT_KEY: bool(args.with_pdf_report),
                    GitbotMessageGenerator.ISSUE_OPT_KEY: False
                }, "issues,licenses")
                if not pr_text_content:
                    log.error("Failed to generate the text content for the pull request, current changes will be skipped")
                    continue

                log.debug("Opening PR via PR change %s", pr_change)
                submit_pr(pr_change, args.branch, pr_text_content, meterian_pdf_report_path, record_prs, opened_prs, pr_infos_by_dep)

        if len(opened_prs) > 0:
            print("New pull requests opened:")
            for pr_change in opened_prs:
                dep = pr_change.dependencies[0]
                print("- " + pr_change.pr.get_url() + " - " + "fixes " + dep.language + "/" + dep.name)
        else:
            print("No pull requests were opened")
        print()

        if record_prs == True:
            if meterian_project_id:
                open_prs_links = []
                for prs in remote_repo.get_open_pulls(base=args.branch):
                    open_prs_links.append(prs.get_url())

                record_pr_info_on_report(meterian_project_id, pr_infos_by_dep, open_prs_links)
            else:
                log.error("Unexpected: report ID is unknown, no PR information can be recorded")
    

    if "ISSUE" == args.action:
        issue_submitter = IssueSubmitter(vcsPlatform, remote_repo)

        meterian_report = None
        if args.json_report:
            meterian_json_report_path = os.path.abspath(args.json_report)
            if os.path.exists(meterian_json_report_path) is False:
                sys.stderr.write("Meterian JSON report not found @ " + str(meterian_json_report_path) + "\n")
                sys.stderr.write("\n")
                sys.exit(-1)
            else:
                try:
                    meterian_report = open(meterian_json_report_path)
                    meterian_json_report = json.load(meterian_report)
                    meterian_report.close()
                except:
                    sys.stderr.write("Unable to load Meterian JSON report at %s \n" % str(meterian_json_report_path))
                    sys.stderr.write("Ensure it is a valid JSON report\n")
                    sys.stderr.write("\n")
                    sys.exit(-1)
        else:
            sys.stderr.write("Unable to open issue, Meterian JSON report at not provided\n")
            sys.stderr.write("\n")
            sys.exit(-1)

        issue_text_content = generate_contribution_content(gitbot_msg_generator, meterian_json_report, {
            GitbotMessageGenerator.ISSUE_OPT_KEY: True,
            GitbotMessageGenerator.AUTOFIX_OPT_KEY: False,
            GitbotMessageGenerator.REPORT_OPT_KEY: False,
        })
        if not issue_text_content:
            sys.stderr.write("Unable to generate the text content for the issue\n")
            sys.stderr.write("\n")
            sys.exit(-1)

        issue_submitter.submit(issue_text_content)



