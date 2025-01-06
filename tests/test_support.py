import tempfile
import unittest
from unittest.mock import MagicMock, mock_open, patch, call

from qelp.support import ArchiveExtractor, FileWrapper, Parser, Timeliner
from qelp.esxi_to_csv import LogIdentifier
from pathlib import Path
import re


class TestArchiveExtractor(unittest.TestCase):
    @patch("pathlib.Path.mkdir")
    def test_extract_zip_file(self, mock_mkdir):
        archive_file = "archive.zip"
        archive_path = Path("/path/to") / archive_file

        mock_mkdir.return_value = None

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "output_dir"
            extractor = ArchiveExtractor([])
            extractor._ArchiveExtractor__extract_zip_file = MagicMock(return_value=None)

            extractor.extract_archive(archive_path, output_dir)

            extractor._ArchiveExtractor__extract_zip_file.assert_called_once_with(
                archive_path, output_dir / f"{archive_file}_results" / "Extracted_logs"
            )

    @patch("pathlib.Path.mkdir")
    def test_extract_tar_file(self, mock_mkdir):
        archive_file = "archive.tar"
        archive_path = Path("/path/to") / archive_file

        mock_mkdir.return_value = None

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "output_dir"
            extractor = ArchiveExtractor([])
            extractor._ArchiveExtractor__extract_tar_file = MagicMock(return_value=None)

            extractor.extract_archive(archive_path, output_dir)

            extractor._ArchiveExtractor__extract_tar_file.assert_called_once_with(
                archive_path, output_dir / f"{archive_file}_results" / "Extracted_logs"
            )

    def test_extract_archive_unsupported_file(self):
        archive_path = Path("/path/to/archive.rar")
        output_dir = Path("/path/to/output_dir")
        extractor = ArchiveExtractor([])

        with patch("qelp.support.logger") as mock_logger:
            extractor.extract_archive(archive_path, output_dir)

            mock_logger.warning.assert_called_once_with(
                "Unsupported file %s", archive_path
            )

    def test_get_all_filename_patterns_re(self):
        log_identifiers = [
            MagicMock(filename_pattern=".*.log"),
            MagicMock(filename_pattern=".*.txt"),
        ]
        extractor = ArchiveExtractor(log_identifiers)

        expected_pattern = ".*.log|.*.txt"
        actual_pattern = extractor._ArchiveExtractor__get_all_filename_patterns_re(
            log_identifiers
        ).pattern

        self.assertEqual(expected_pattern, actual_pattern)

    @patch("pathlib.Path.mkdir")
    def test_configure_extraction_paths(self, mock_mkdir):
        archive_path = Path("/path/to/archive.zip")
        output_dir = Path("/path/to/output")
        expected_extraction_dir = output_dir / (archive_path.name + "_results")
        expected_logs_extraction_dir = expected_extraction_dir / "Extracted_logs"

        extraction_dir, logs_extraction_dir = (
            ArchiveExtractor._ArchiveExtractor__configure_extraction_paths(
                archive_path, output_dir
            )
        )

        mock_mkdir.assert_any_call(exist_ok=False)
        mock_mkdir.assert_any_call()
        self.assertEqual(extraction_dir, expected_extraction_dir)
        self.assertEqual(logs_extraction_dir, expected_logs_extraction_dir)


class TestFileWrapper(unittest.TestCase):
    @patch("builtins.open", new_callable=mock_open, read_data="line1\nline2\nline3\n")
    def test_iter_lines_plain_file(self, mock_file):
        instance = FileWrapper(mock_file)
        instance.file = MagicMock(suffix="")

        lines = list(instance.iter_lines())

        self.assertEqual(lines, ["line1", "line2", "line3"])
        mock_file.assert_called_once_with(instance.file)

    @patch("gzip.open", new_callable=mock_open, read_data="line1\nline2\nline3\n")
    def test_iter_lines_gz_file(self, mock_gzip_file):
        instance = FileWrapper(mock_gzip_file)
        instance.file = MagicMock(suffix=".gz")

        lines = list(instance.iter_lines())

        self.assertEqual(lines, ["line1", "line2", "line3"])


class TestTimeliner(unittest.TestCase):
    @patch("builtins.open", new_callable=mock_open)
    @patch("csv.writer")
    def test_init(self, mock_csv_writer, mock_open):
        mock_file = mock_open.return_value
        mock_writer = mock_csv_writer.return_value

        Timeliner("test_timeline.csv")

        mock_open.assert_called_once_with("test_timeline.csv", "w", newline="")
        mock_csv_writer.assert_called_once_with(mock_file)
        mock_writer.writerow.assert_called_once_with(
            ["Timestamp", "Description", "Access Type", "Source CSV"]
        )

    def test_add(self):
        timeliner = Timeliner("test_timeline.csv")
        group_dict = {"Timestamp": "2023-01-01T00:00:00Z", "Access Type": "read", "Description": "Test event"}
        csv_file = "test.csv"

        timeliner.add(group_dict, csv_file)
        expected_row = ["2023-01-01T00:00:00Z", "Test event", "read", "test.csv"]
        self.assertEqual([expected_row], timeliner.rows)
        

class TestParser(unittest.TestCase):
    def setUp(self) -> None:
        self.log_identifiers = [
            MagicMock(filename_pattern=".*.log"),
            MagicMock(filename_pattern=".*.txt"),
        ]

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="Sample log content\nAnother log line",
    )
    def test_match_patterns_to_logs(self, mock_open):
        instance = FileWrapper(mock_open)
        instance.file = MagicMock(name="test_file.txt")
        parser = Parser("test_file.txt", self.log_identifiers)
        log_path = Path("test_log.txt")
        filename = "foo"
        patterns = [
            MagicMock(
                regex=re.compile("(?P<Description>Sample)"),
                access_types = [
                    MagicMock(
                        access_type_name="Logon",
                        description_handlers=[
                            MagicMock(should_timeline=True, regex=re.compile("mple"))
                        ],
                    ),
                ]
            ),
            MagicMock(
                regex=re.compile("(?P<Description>line)"),
                access_types = [
                    MagicMock(
                        access_type_name="User_activity",
                        description_handlers=[
                            MagicMock(should_timeline=False, regex=re.compile("li"))
                        ],
                    ),
                ]
            )
        ]

        matches = parser.match_patterns_to_logs(log_path, filename, patterns)
        self.assertEqual(len(matches[filename]), 2)
        self.assertEqual(
            matches[filename][0][0],
            {"Description": "Sample", "Access Type": "Logon", "Source": Path("test_log.txt")},
        )
        self.assertEqual(matches[filename][0].access_type, "Logon")
        self.assertEqual(matches[filename][0].should_timeline, True)
        self.assertEqual(
            matches[filename][1][0],
            {"Description": "line", "Access Type": "User_activity", "Source": Path("test_log.txt")},
        )
        self.assertEqual(matches[filename][1].access_type, "User_activity")
        self.assertEqual(matches[filename][1].should_timeline, False)

    @patch("os.makedirs")
    @patch("builtins.open", new_callable=mock_open)
    @patch("csv.writer")
    def test_write_to_csv(self, mock_csv_writer, mock_open, mock_makedirs):
        # Arrange
        parser = Parser("test_file.txt", self.log_identifiers)
        log_key = "test_log"
        matches = [
            MagicMock(
                group_dict={"key1": "value1", "key2": "value2"},
                access_type="access_type",
                should_timeline=True,
            ),
            MagicMock(
                group_dict={"key1": "value3", "key2": "value4"},
                access_type="access_type",
                should_timeline=False,
            ),
        ]
        timeliner = MagicMock()
        output_directory = Path("/fake/dir")
        csv_file = output_directory / f"{log_key}.csv"

        parser.extraction_dir = Path("/fake/dir")

        parser.write_to_csv(log_key, matches, timeliner)

        mock_makedirs.assert_called_once_with(output_directory, exist_ok=True)
        mock_open.assert_called_once_with(csv_file, "w", newline="")

        mock_csv_writer_instance = mock_csv_writer.return_value
        written_rows = [
            list(call[0][0])
            for call in mock_csv_writer_instance.writerow.call_args_list
        ]
        expected_rows = [["key1", "key2"], ["value1", "value2"], ["value3", "value4"]]
        self.assertEqual(written_rows, expected_rows)

        timeliner.add.assert_called_once_with(
            {"key1": "value1", "key2": "value2"}, csv_file
        )
