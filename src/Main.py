
import argparse
import json
import sys
import logging
import http.client
import os
import shutil

from vcs.IssueOrchestrator import IssueOrchestrator
from vcs.GitCli import GitCli
from vcs.VcsHubFactory import VcsHubFactory
from vcs.github.GithubRepo import GithubRepo
from vcs.PrOrchestrator import PrOrchestrator
from gitbot.GitbotMessageGenerator import GitbotMessageGenerator
from pathlib import Path

CODE_HOSTING_PLATFORMS = [ "github" ] #, "bitbucket" ]

DEFAULT_AUTHORS_BY_PLATFORM = {
    "github": GithubRepo.DEFAULT_COMMITTER_DATA
    # ,"bitbucket": BitbucketRepo.DEFAULT_COMMITTER_DATA
}

ACTIONS = [ "PR", "ISSUE" ]

PROJECT_DIR = Path(os.getcwd())

VERSION = "1.0.0"

log = logging.getLogger("Main")

class HelpingParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.stderr.write('\n')
        sys.exit(-1)

#TEMPORARY CHANGES FIXME
def logHttpRequests():
    # http.client.HTTPConnection.debuglevel = 1

    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.INFO)
    requests_log.propagate = True

    logging.debug('Full debug log for HTTP requests enabled')

def parse_args():
    parser = HelpingParser()
    parser.add_argument("action", help="The action you want to perform as a result of the autofix results\n (i.e. PR: open a pull request on the codebase repository; ISSUE: open an issue on the codebase repository)")
    parser.add_argument("report", help="The path to the Meterian JSON report")
    parser.add_argument("repository", help="The name of the remote repository\n (i.e. aws/aws-cli)")
    parser.add_argument("branch", help="The name of the current branch (must be a branch available remotely)")

    parser.add_argument(
        "-l",
        "--log",
        default="warning",
        metavar="LOGLEVEL",
        help="Sets the logging level (default is warning)"
    )

    parser.add_argument(
        "-v",
        "--vcshub",
        default="github",
        metavar="VCSHUB",
        help="The code hosting platform where your codebase is hosted\n (i.e. github) (default is github)"
    )

    parser.add_argument(
        "--with-pdf-report",
        metavar="PATH",
        help="Allows to specify the path to the Meterian PDF report to add as part of the pull request if any are opened. This option is considered only if 'PR' is the action being used (view help for more details on actions)"
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

    #TODO figure out what is wrong with this
    # logging.basicConfig(format='%(time)s-%(levelname)s-%(message)s')

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


if __name__ ==  "__main__":
    args = parse_args()
    initLogging(args)

    if args.vcshub not in CODE_HOSTING_PLATFORMS:
        sys.stderr.write("Invalid code hosting platform: %s\n" % args.vcshub)
        sys.stderr.write("Available code hosting platforms are: %s\n" % str(CODE_HOSTING_PLATFORMS))
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
                    if PROJECT_DIR in Path(meterian_pdf_report_path).parents:
                        log.debug("Specified PDF report %s relative to project dir %s", meterian_pdf_report_path, str(PROJECT_DIR))
                        meterian_pdf_report_path = Path(meterian_pdf_report_path).relative_to(PROJECT_DIR)
                        log.debug("Will use relative path of PDF report %s", meterian_pdf_report_path)
                    else:
                        log.warning("PDF report %s will be ignored as it's not relative to project %s", meterian_pdf_report_path, str(PROJECT_DIR))
            elif args.action == "ISSUE":
                log.warning("Unsupported option '--with-pdf-report' being used with action 'ISSUE, it will be ignored")

    vcsPlatform = VcsHubFactory(args.vcshub).create()
    if vcsPlatform is None:
        sys.stderr.write("Unable to create an instance for the " +args.vcshub.title()+ " platform, ensure appropriate access token environment variables are appropriately set\n")
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
        sys.stderr.write("Repository %s was not found on %s\n" % (args.repository, args.vcshub))
        sys.stderr.write("\n")
        sys.exit(-1)
    

    gitbot_msg_generator = GitbotMessageGenerator()

    if "PR" == args.action:
        if "autofix" in meterian_json_report:
            git = GitCli(str(PROJECT_DIR))
            changes = git.get_changes()
            if changes is None:
                sys.stderr.write("Change detection failed\n")
                sys.exit(-1)

            if len(changes) == 0:
                print("No changes were made in your repository therefore no pull request will be opened")
                sys.exit(0)

        author = DEFAULT_AUTHORS_BY_PLATFORM[args.vcshub]
        pr_orchestrator = PrOrchestrator(remote_repo, author)

        pr_text_content = generate_contribution_content(gitbot_msg_generator, meterian_json_report, {
            GitbotMessageGenerator.AUTOFIX_OPT_KEY: True,
            GitbotMessageGenerator.REPORT_OPT_KEY: bool(args.with_pdf_report),
            GitbotMessageGenerator.ISSUE_OPT_KEY: False
        })
        if not pr_text_content:
            sys.stderr.write("Unable to generate the text content for the pull request\n")
            sys.stderr.write("\n")
            sys.exit(-1)
    
        pr_orchestrator.orchestarte(pr_text_content, changes, args.branch, meterian_pdf_report_path)

    
    if "ISSUE" == args.action:
        issue_orchestrator = IssueOrchestrator(vcsPlatform, remote_repo)

        issue_text_content = generate_contribution_content(gitbot_msg_generator, meterian_json_report, {
            GitbotMessageGenerator.ISSUE_OPT_KEY: True,
            GitbotMessageGenerator.AUTOFIX_OPT_KEY: False,
            GitbotMessageGenerator.REPORT_OPT_KEY: False,
        })
        if not issue_text_content:
            sys.stderr.write("Unable to generate the text content for the issue\n")
            sys.stderr.write("\n")
            sys.exit(-1)

        issue_orchestrator.orchestrate(issue_text_content)



