
import argparse
import json
import sys
import logging
import http.client
import os
import shutil

from vcs.IssueSubmitter import IssueSubmitter
from vcs.GitCli import GitCli
from vcs.VcsHubFactory import VcsHubFactory
from vcs.github.GithubRepo import GithubRepo
from vcs.gitlab.GitlabProject import GitlabProject
from vcs.PullRequestSubmitter import PullRequestSubmitter
from gitbot.GitbotMessageGenerator import GitbotMessageGenerator
from vcs.CommitAuthor import CommitAuthor
from pathlib import Path

VCS_PLATFORMS = [ "github", "gitlab" ] #, "bitbucket" ]

DEFAULT_AUTHORS_BY_PLATFORM = {
    "github": GithubRepo.DEFAULT_COMMITTER,
    "gitlab": GitlabProject.DEFAULT_COMMITTER
    # ,"bitbucket": BitbucketRepo.DEFAULT_COMMITTER_DATA
}

ACTIONS = [ "PR", "ISSUE" ]

WORK_DIR = None

VERSION = "1.1.3"

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
    parser.add_argument("report", help="The path to the Meterian JSON report")
    parser.add_argument("repository", help="The name of the remote repository\n (i.e. aws/aws-cli)")
    parser.add_argument("branch", help="The name of the current branch (must be a branch available remotely)")

    parser.add_argument(
        "-v",
        "--vcs",
        default="github",
        metavar="VCS",
        help="The version control system where your repository is hosted\n (i.e. github) (default is github) (supported: " + str(VCS_PLATFORMS) + ")"
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

def generate_contribution_content(gitbot: GitbotMessageGenerator, meterian_json_report: dict, options: dict) -> dict:
    content = gitbot.genMessage(meterian_json_report, options)
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

if __name__ ==  "__main__":
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

    meterian_json_report_path = os.path.abspath(args.report)
    if os.path.exists(meterian_json_report_path) is False:
        sys.stderr.write("Path for meterian JSON report " + args.report + " does not exists, impossible to load autofix results\n")
        sys.stderr.write("\n")
        sys.exit(-1)
    else:
        try:
            meterian_report = open(meterian_json_report_path)
            meterian_json_report = json.load(meterian_report)
            meterian_report.close()
        except:
            sys.stderr.write("Unable to load Meterian JSON report at %s \n" % meterian_json_report_path)
            sys.stderr.write("Ensure it is a valid JSON report\n")
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

    vcsPlatform = VcsHubFactory(args.vcs).create()
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
        sys.stderr.write("Repository %s was not found on %s\n" % (args.repository, args.vcs))
        sys.stderr.write("\n")
        sys.exit(-1)
    

    gitbot_msg_generator = GitbotMessageGenerator()

    if "PR" == args.action:
        if "autofix" in meterian_json_report:
            git = GitCli(str(WORK_DIR))
            changes = git.get_changes()
            if changes is None:
                sys.stderr.write("Change detection failed\n")
                sys.exit(-1)

            if len(changes) == 0:
                print("No changes were made in your repository therefore no pull request will be opened")
                sys.exit(0)

        author = get_commit_author_details(args)
        pr_submitter = PullRequestSubmitter(WORK_DIR, remote_repo, author)

        pr_text_content = generate_contribution_content(gitbot_msg_generator, meterian_json_report, {
            GitbotMessageGenerator.AUTOFIX_OPT_KEY: True,
            GitbotMessageGenerator.REPORT_OPT_KEY: bool(args.with_pdf_report),
            GitbotMessageGenerator.ISSUE_OPT_KEY: False
        })
        if not pr_text_content:
            sys.stderr.write("Unable to generate the text content for the pull request\n")
            sys.stderr.write("\n")
            sys.exit(-1)
    
        pr_submitter.submit(pr_text_content, changes, args.branch, meterian_pdf_report_path)

    
    if "ISSUE" == args.action:
        issue_submitter = IssueSubmitter(vcsPlatform, remote_repo)

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



