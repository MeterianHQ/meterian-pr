import unittest
from src.vcs.BranchHelper import BranchHelper

class BranchHelperTest(unittest.TestCase):

    def setUp(self) -> None:
        self.branch_helper = BranchHelper()

    def test_should_fail_to_convert_branch_name_to_ref_when_branch_name_is_invalid(self):
        branch_name = "refs/heads/"

        result = self.branch_helper.to_branch_ref(branch_name)

        self.assertIsNone(result)
    
    def test_should_fail_to_convert_branch_name_to_ref_when_branch_name_is_invalid_scenario_2(self):
        branch_name = "refs/heads/@"

        result = self.branch_helper.to_branch_ref(branch_name)

        self.assertIsNone(result)

    def test_should_convert_branch_name_to_ref_sanitizing_disallowed_characters(self):
        branch_name = "foo/bar/foo..bar~foo^bar:foo?bar*foo[bar@{foo\\bar"
        
        result = self.branch_helper.to_branch_ref(branch_name)

        self.assertIsNotNone(result)
        self.assertEqual("refs/heads/foo/bar/foo_bar_foo_bar_foo_bar_foo_bar_foo_bar", result)

    def test_should_convert_branch_name_to_ref_sanitizing_disallowed_and_control_characters(self):
        branch_name = "foo/bar/ foo     bar"
        
        result = self.branch_helper.to_branch_ref(branch_name)

        self.assertIsNotNone(result)
        self.assertEqual("refs/heads/foo/bar/foobar", result)

    def test_should_get_branch_name_from_ref(self):
        ref = "refs/heads/feature/foo"
        self.assertEqual("feature/foo", self.branch_helper.as_branch_name(ref))

    def test_should_get_ref_from_branch_name(self):
        branch_name = "feature/foo"
        self.assertEqual("refs/heads/feature/foo", self.branch_helper.as_branch_ref(branch_name))

if __name__ == '__main__':
    unittest.main()