"""This is licensed under the GPLv3

Also, this was generated by ChatGPT"""
import unittest
from unittest.mock import mock_open, patch
from helpful_modules.the_documentation_file_loader import (
    DocumentationFileLoader,
    DocumentationNotFound,
    DocumentationFileNotFound,
)


class TestDocumentationFileLoader(unittest.TestCase):
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data='{"file_name": "test.json", "contents": [{"title": "TestTitle", "contents": "TestContents"}]}',
    )
    def test_load_documentation_into_readable_files(self, mock_open):
        loader = DocumentationFileLoader()
        documentation = loader.load_documentation_into_readable_files()

        # Ensure that the file is opened with the correct path
        mock_open.assert_called_once_with("docs/documentation.json", "r")

        # Check that the loaded documentation matches the expected structure
        self.assertEqual(
            documentation,
            [
                {
                    "file_name": "test.json",
                    "contents": [{"title": "TestTitle", "contents": "TestContents"}],
                }
            ],
        )

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data='{"file_name": "test.json", "contents": []}',
    )
    def test_get_documentation(self, mock_open):
        loader = DocumentationFileLoader()

        # Test successful retrieval
        documentation = loader.get_documentation("test.json", "TestTitle")
        self.assertEqual(documentation, "TestContents")

        # Test file not found
        with self.assertRaises(DocumentationFileNotFound):
            loader.get_documentation("nonexistent.json", "TestTitle")

        # Test item not found
        with self.assertRaises(DocumentationNotFound):
            loader.get_documentation("test.json", "NonexistentTitle")


if __name__ == "__main__":
    unittest.main()
