import os
import unittest

from src.vcs.VcsHubFactory import VcsHubFactory
from src.vcs.github.Github import Github
from src.vcs.gitlab.Gitlab import Gitlab

class VcsHubFactoryTest(unittest.TestCase):

    def setUp(self) -> None:
        self.factory = None
        self.environ_backup = os.environ

    def tearDown(self) -> None:
        if self.environ_backup:
            os.environ = self.environ_backup

    def test_should_not_create_instance_of_GitHub_when_access_token_not_found_in_environment(self):
        del os.environ["GITHUB_TOKEN"]
        self.factory = VcsHubFactory("github")

        result = self.factory.create()

        self.assertIsNone(result)

    def test_should_not_create_no_VcsHub_instance_when_platform_is_unrecognised(self):
        result = VcsHubFactory("FooHub").create()
        self.assertIsNone(result)

    def disabled_test_should_create_instance_of_GitHub(self):
        self.factory = VcsHubFactory("github")

        result = self.factory.create()

        self.assertTrue(isinstance(result, Github))

    def test_should_create_instance_of_Gitlab(self):
        self.factory = VcsHubFactory("gitlab")

        result = self.factory.create()

        self.assertTrue(isinstance(result, Gitlab))

    def test_should_not_create_instance_of_Gitlab_when_token_env_var_is_unset(self):
        del os.environ["GITLAB_TOKEN"]
        self.factory = VcsHubFactory("gitlab")

        self.assertIsNone(self.factory.create())

if __name__ == "__main__":
    unittest.main()