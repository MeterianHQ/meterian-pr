import os
import unittest

from src.vcs.VcsHubFactory import VcsHubFactory
from src.vcs.github.Github import Github
from src.vcs.gitlab.Gitlab import Gitlab
from github import MainClass
from gitlab.const import DEFAULT_URL

class VcsHubFactoryTest(unittest.TestCase):

    def setUp(self) -> None:
        self.factory = None
        self.environ_backup = os.environ

    def tearDown(self) -> None:
        if self.environ_backup:
            os.environ = self.environ_backup

    def test_should_not_create_instance_of_GitHub_when_access_token_not_found_in_environment(self):
        self.__unset_env_var("GITHUB_TOKEN")
        self.factory = VcsHubFactory("github", MainClass.DEFAULT_BASE_URL)

        result = self.factory.create()

        self.assertIsNone(result)

    def test_should_not_create_no_VcsHub_instance_when_platform_is_unrecognised(self):
        result = VcsHubFactory("FooHub", "https://foohub.com").create()
        self.assertIsNone(result)

    def disabled_test_should_create_instance_of_GitHub(self):
        self.factory = VcsHubFactory("github", MainClass.DEFAULT_BASE_URL)

        result = self.factory.create()

        self.assertTrue(isinstance(result, Github))

    def disabled_test_should_create_instance_of_Gitlab(self):
        self.factory = VcsHubFactory("gitlab", DEFAULT_URL)

        result = self.factory.create()

        self.assertTrue(isinstance(result, Gitlab))

    def test_should_not_create_instance_of_Gitlab_when_token_env_var_is_unset(self):
        self.__unset_env_var("GITLAB_TOKEN")
        self.factory = VcsHubFactory("gitlab", DEFAULT_URL)

        self.assertIsNone(self.factory.create())

    def test_should_fail_to_create_instance_of_Github_when_invalid_token_is_used(self):
        os.environ["GITHUB_TOKEN"] = "an_invalid_token"
        self.factory = VcsHubFactory("github", MainClass.DEFAULT_BASE_URL)

        self.assertIsNone(self.factory.create())

    def test_should_fail_to_create_instance_of_Gitlab_when_invalid_token_is_used(self):
        os.environ["GITLAB_TOKEN"] = "an_invalid_token"
        self.factory = VcsHubFactory("gitlab", DEFAULT_URL)

        self.assertIsNone(self.factory.create())

    def __unset_env_var(self, name: str):
        if name in os.environ:
            del os.environ[name]

if __name__ == "__main__":
    unittest.main()