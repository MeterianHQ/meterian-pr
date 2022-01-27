import unittest
import os
import json
from src.gitbot.GitbotMessageGenerator import GitbotMessageGenerator
from pathlib import Path


class GitbotMessageGeneratorTest(unittest.TestCase):

    RESOURCES_PATH = str(Path(os.path.dirname(os.path.realpath(__file__))).parent) + "/resources/"

    def setUp(self) -> None:
        self.msg_generator = GitbotMessageGenerator()

    def test_should_generate_message_when_given_a_report(self):
        with open(self.RESOURCES_PATH + 'report.json') as report_json:
            report = json.load(report_json)
        options = {"autofix": True, "issue": False, "report": False}

        message = self.msg_generator.genMessage(report, options)

        self.assertIsNotNone(message, "Expected message dictionary but is None")
        self.assertIsNotNone(message["title"], "Expected title but is None")
        self.assertIsNotNone(message["message"], "Expected message but is None")
        self.assertTrue(message["title"] != "", "Title is empty")
        self.assertTrue(message["message"] != "", "Message is empty")
        print("\n### test_should_generate_message_when_given_a_report\n\n%s" % message)

    def test_should_perfect_report_generate_message_empty_title(self):
        with open(self.RESOURCES_PATH + 'report.perfect.json') as report_json:
            report = json.load(report_json)
        options = {"autofix": False, "issue": True, "report": False}

        message = self.msg_generator.genMessage(report, options)

        self.assertIsNotNone(message, "Expected message dictionary but is None")
        self.assertIsNotNone(message["title"], "Expected title but is None")
        self.assertIsNotNone(message["message"], "Expected message but is None")
        self.assertTrue(message["title"] == "", "Expected empty title")
        self.assertTrue(message["message"] != "", "Message is empty")
        print("\n### test_should_perfect_report_generate_message_missing_title\n\n%s" % message)

if __name__ == '__main__':
    unittest.main()