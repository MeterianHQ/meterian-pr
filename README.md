# Meterian-pr

Automatically open pull requests and issues on your repository as a result of the [Meterian Client autofix](https://docs.meterian.io/the-client/command-line-parameters/advanced-options).

## Installation

Installing `meterian-pr` is fairly easy, simply download the packaged tool from the [releases page](https://github.com/MeterianHQ/meterian-pr/releases) to your machine and add it to your PATH.

```

$ wget -q -O meterian-pr_linux.tar.gz https://github.com/MeterianHQ/meterian-pr/releases/latest/download/meterian-pr_linux.tar.gz
$ tar -xzf meterian-pr_linux.tar.gz -C /path/to/meterian-pr
$ export PATH=$PATH:/path/to/meterian-pr/bin

```

## Prerequisites

### SCM access tokens

As `meterian-pr` supports opening pull requests and issues on GitHub and GitLab repositories you will need to export a valid access token in the respective environment variables `GITHUB_TOKEN` and `GITLAB_TOKEN`

```
$ export GITHUB_TOKEN="ghp_1B4a2e7783***"
$ export GITLAB_TOKEN="glpat-q12-Wc***"
```

### Meterian JSON report

As mentioned earlier, `meterian-pr` uses the results of the Meterian autofix to open PRs and issues. These results are captured in JSON reports that the meterian client generates. According to what action you need to perform with `meterian-pr` different report are used.

To generate the JSON reports needed to open pull requests scan your project as shown below

```
$ cd /path/to/project
$ meterian-docker --autofix --pullreqs
```
This will generate a PR report summary `.pr_summary.json` and set of JSON reports prefixed with `.pr_report` for each updated manifest file found in your codebase to aid opening pull requests. 

To open an issue a single JSON report is needed and it can be generated by scanning your project as shown below

```
$ cd /path/to/project
$ meterian-docker --autofix --report-json=report.json
```
Note: the above examples use the Meterian Dockerized CLI. Learn more about it [here](https://docs.meterian.io/the-meterian-client-dockerized/basic-usage).

## Usage

Assuming that you have ran the Meterian autofix on your project and generated the required JSON report(s) containing the results, invoke `meterian-pr` to open a PR accordingly as shown below

```
$ meterian-pr /path/to/your/project PR my-org/my-project main

New pull requests opened:
- https://github.com/my-org/my-project/pull/1
- https://github.com/my-org/my-project/pull/2
```

You will be linked to all new pull requests opened authored by the user associated to the authorization token used

![Pull Request example](media/images/pr_example.png)

Should you wish to open pull requests capturing all changes in the projects listed in the .sln file of a .NET project add the --group-by-sln

```
$ meterian-pr --group-by-sln /path/to/your/.net/project PR my-org/my-dot-project main

New pull requests opened:
- https://github.com/my-org/my-dotnet-project/pull/3
- https://github.com/my-org/my-dotnet-project/pull/4
```

To open an issue instead

```
$ meterian-pr /path/to/your/.net/project --json-report report.json ISSUE my-org/my-dot-project main

A new issue has been opened, view it here:
- https://github.com/my-org/my-dotnet-project/issues/1
```


## Help

Here is an overview of the available commands (the help page):

```
$ meterian-pr --help
usage: meterian-pr [-h] [-v PLATFORM] [--api-base-url URL] [--record-prs] [--group-by-sln] [--json-report PATH] [--with-pdf-report PATH]
               [--commit-author-username USERNAME] [--commit-author-email EMAIL] [-l LOGLEVEL] [--version]
               workdir action repository branch

positional arguments:
  workdir               The path to the work directory
  action                The action you want to perform as a result of the autofix results (i.e. PR: open a pull request on the a repository; ISSUE: open an issue on
                        a repository)
  repository            The name of the remote repository (i.e. aws/aws-cli)
  branch                The name of the current branch (must be a branch available remotely)

optional arguments:
  -h, --help            show this help message and exit
  -v PLATFORM, --vcs PLATFORM
                        The version control system platform where your repository is hosted (i.e. github) (default is github) (supported: ['github', 'gitlab'])
  --api-base-url URL    Allows to override the API base URL for the chosen version control system platform
  --record-prs          Allows to record information about pull requests opened on the Meterian report (note: a valid Meterian authentication token must be set in
                        the environment)
  --group-by-sln        Allows to open PRs capturing all the changes applied to all the projects listed in your .NET .sln files
  --json-report PATH    Allows to specify the path to the Meterian JSON report. This option is required if 'ISSUE' is the action being used (view help for more
                        details on actions)
  --with-pdf-report PATH
                        Allows to specify the path to the Meterian PDF report to add as part of the pull request if any are opened. This option is considered only
                        if 'PR' is the action being used (view help for more details on actions)
  --commit-author-username USERNAME
                        Allows to specify a different commit author username to use (by default the Meterian bot username is used)
  --commit-author-email EMAIL
                        Allows to specify a different commit author email address to use (by default the Meterian bot email address is used)
  -l LOGLEVEL, --log LOGLEVEL
                        Sets the logging level (default is warning)
  --version             Show version and exit


```