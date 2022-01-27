import os
import logging

from .VcsHubInterface import VcsHubInterface
from .github.Github import Github
from github import Github as PyGitHub

class VcsHubFactory:

    PLATFORMS_AND_ENVVARS = {
        "github": "GITHUB_TOKEN"
    }

    __log = logging.getLogger("VcsHubFactory")

    def __init__(self, platform: str):
        self.platform = platform

    def create(self) -> VcsHubInterface:
        if self.platform == "github":
            self.__log.debug("Requested creation of an instance of GitHub")

            envvar = self.PLATFORMS_AND_ENVVARS[self.platform]
            self.__log.debug("Getting auth token on the current environment with env var %s", envvar)
            if envvar in os.environ:
                pyGithub = PyGitHub(os.environ[envvar])
                self.__log.debug("Currently authenticated as %s", pyGithub.get_user().login)
                vcshub = Github(pyGithub)
                self.__log.debug("Created instace of GitHub %s", vcshub)
                return vcshub
            else:
                self.__log.debug("Github token not found in environment, no instance will be created")
        
        return None