import unittest

from scripts.quality import validate_after_edit


class ValidateAfterEditTests(unittest.TestCase):
    def test_validates_githook_changes(self) -> None:
        self.assertTrue(validate_after_edit.should_validate({".githooks/pre-commit"}))
        self.assertTrue(validate_after_edit.should_validate({".githooks/pre-push"}))
        self.assertTrue(validate_after_edit.should_validate({"tooling/hooks/hooks.json"}))

    def test_skips_unrelated_paths(self) -> None:
        self.assertFalse(validate_after_edit.should_validate({"notes/todo.txt"}))


if __name__ == "__main__":
    unittest.main()
