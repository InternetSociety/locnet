import json
import tempfile
import unittest
from pathlib import Path

from pydantic import ValidationError

from app.main import EXAMPLES_DIRECTORY, list_example_filenames
from app.schemas.modeling import BuilderInput


class ExampleFilesTests(unittest.TestCase):
    def test_list_example_filenames_returns_sorted_json_files(self):
        with tempfile.TemporaryDirectory() as temp_directory:
            directory = Path(temp_directory)
            (directory / "philippines_example.json").write_text(
                "{}", encoding="utf-8"
            )
            (directory / "notes.txt").write_text(
                "not an example", encoding="utf-8"
            )
            (directory / "indonesia_example.json").write_text(
                "{}", encoding="utf-8"
            )
            (directory / "peru_example.json").write_text("{}", encoding="utf-8")

            self.assertEqual(
                list_example_filenames(directory),
                [
                    "indonesia_example.json",
                    "peru_example.json",
                    "philippines_example.json",
                ],
            )

    def test_all_example_files_are_valid_builder_inputs(self):
        filenames = list_example_filenames(EXAMPLES_DIRECTORY)

        self.assertTrue(filenames)
        for filename in filenames:
            with self.subTest(filename=filename):
                BuilderInput.model_validate_json(
                    (EXAMPLES_DIRECTORY / filename).read_text(encoding="utf-8")
                )

    def test_household_sizes_must_be_positive(self):
        filename = list_example_filenames(EXAMPLES_DIRECTORY)[0]
        payload = json.loads(
            (EXAMPLES_DIRECTORY / filename).read_text(encoding="utf-8")
        )

        for invalid_values in (
            {"hh_size": 0},
            {"hh_size": None, "users_per_household": 0},
        ):
            with (
                self.subTest(invalid_values=invalid_values),
                self.assertRaises(ValidationError),
            ):
                BuilderInput.model_validate(payload | invalid_values)


if __name__ == "__main__":
    unittest.main()
