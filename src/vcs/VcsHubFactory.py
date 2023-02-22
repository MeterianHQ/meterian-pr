from sys import exc_info
import os
import logging

from .VcsHubInterface import VcsHubInterface
from .github.Github import Github
from github import Github as PyGithub

from .gitlab.Gitlab import Gitlab
from gitlab import Gitlab as PyGitlab

class VcsHubFactory:

    PLATFORMS_AND_ENVVARS = {
        "github": "GITHUB_TOKEN",
        "gitlab": "GITLAB_TOKEN"
    }

    __log = logging.getLogger("VcsHubFactory")

    def __init__(self, platform: str, api_base_url: str):
        self.platform = platform
        self.api_base_url = api_base_url

    def create(self) -> VcsHubInterface:
        if self.platform == "github":
            self.__log.debug("Requested creation of an instance of GitHub")

            envvar = self.PLATFORMS_AND_ENVVARS[self.platform]
            self.__log.debug("Getting auth token on the current environment with env var %s", envvar)
            if envvar in os.environ:
                try:
                    pyGithub = PyGithub(os.environ[envvar], base_url=self.api_base_url)

                    self.__check_good_gh_credentials(pyGithub)

                    self.__log.debug("Currently authenticated as %s", str(pyGithub.get_user()))
                    vcshub = Github(pyGithub)
                    self.__log.debug("Created instace of GitHub %s", vcshub)
                    return vcshub
                except:
                    self.__log.error("Failed to create GitHub instance", exc_info=1)
            else:
                self.__log.debug("Github token not found in environment, no instance will be created")
        
        if self.platform == "gitlab":
            self.__log.debug("Requested creation of an instance of GitLab")

            envvar_name = self.PLATFORMS_AND_ENVVARS[self.platform]
            if envvar_name in os.environ:
                try:
                    pyGitlab = PyGitlab(self.api_base_url, private_token=os.environ[envvar_name])
                    pyGitlab.auth()
                    self.__log.debug("Gitlab instance created. Currently authenticated as %s", pyGitlab.user.username)
                    return Gitlab(pyGitlab)
                except:
                    self.__log.error("Failed to create GitLab instance", exc_info=1)
            else:
                self.__log.debug("The Gitlab token was not found in your environment")

        return None

    def __check_good_gh_credentials(self, gh: PyGithub):
        try:
            gh.get_user().login
        except Exception as ex:
            if "401" in str(ex):
                raise ex