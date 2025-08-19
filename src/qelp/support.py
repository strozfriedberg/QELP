import csv
from datetime import datetime
import os
import re
import zipfile
import tarfile
import gzip
import logging
from pathlib import Path
from typing import Any, Dict, Generator, List, Tuple
import argparse
from collections import defaultdict, namedtuple
import art
from colorama import init, Fore
from concurrent.futures import ThreadPoolExecutor
from .local_logger import logger


class ArchiveExtractor:
    def __init__(self, log_identifiers) -> None:
        self.filename_patterns_re = self.__get_all_filename_patterns_re(log_identifiers)

    def extract_archive(self, archive_path: Path, output_dir: Path) -> Path:
        SUPPORTED_PATHS = [".zip", ".tar", ".gz", ".tgz"]
        if archive_path.suffix.lower() not in SUPPORTED_PATHS:
            logger.warning("Unsupported file %s", archive_path)
            return None

        extraction_dir, logs_extraction_dir = self.__configure_extraction_paths(
            archive_path, output_dir
        )
        if archive_path.suffix.lower() == ".zip":
            self.__extract_zip_file(archive_path, logs_extraction_dir)
        else:
            self.__extract_tar_file(archive_path, logs_extraction_dir)

        return extraction_dir

    def __extract_tar_file(self, archive_path: Path, logs_extraction_dir: Path) -> None:
        try:
            with tarfile.open(archive_path, "r:*", errors="ignore") as tar_log_file:
                for member in tar_log_file:
                    member.name = os.path.basename(member.name)
                    if self.filename_patterns_re.match(member.name):
                        tar_log_file.extract(member, path=logs_extraction_dir)
        except (
            KeyError,
            FileNotFoundError,
            tarfile.TarError,
            tarfile.ReadError,
            tarfile.ExtractError,
            tarfile.EmptyHeaderError,
        ) as e:
            logger.exception("Unhandled error extracting %s", archive_path, exc_info=e)
            logger.error(
                "A file in the archive may be empty or the archive is corrupt, still check the output directory for results."
            )

    @staticmethod
    def __get_all_filename_patterns_re(
        log_identifiers: List["LogIdentifier"],
    ) -> re.Pattern:
        filename_patterns = [
            log_identifier.filename_pattern for log_identifier in log_identifiers
        ]
        return re.compile("|".join(filename_patterns), re.IGNORECASE)

    def __extract_zip_file(self, archive_path: Path, logs_extraction_dir: Path) -> None:
        try:
            with zipfile.ZipFile(archive_path, "r") as zip_log_file:
                for member in zip_log_file.namelist():
                    if self.filename_patterns_re.finditer(member):
                        zip_log_file.extract(member, path=logs_extraction_dir)
        except zipfile.BadZipFile as e:
            logger.exception("Unhandled error extracting %s", archive_path, exc_info=e)

    @staticmethod
    def __configure_extraction_paths(
        archive_path: Path, output_dir: Path
    ) -> Tuple[Path, Path]:
        file_name = Path(archive_path).name + "_results"
        extraction_dir = output_dir / file_name
        extraction_dir.mkdir(exist_ok=False)
        logs_extraction_dir = extraction_dir / "Extracted_logs"
        logs_extraction_dir.mkdir()
        return extraction_dir, logs_extraction_dir


class FileWrapper:
    def __init__(self, file: Path) -> None:
        self.file = file

    def iter_lines(self) -> Generator[str, None, None]:
        if self.file.suffix == ".gz":
            file = gzip.open(self.file, "rt")
        else:
            file = open(self.file, errors='ignore')

        for line in file:
            yield line.strip()

        file.close()


class Timeliner:
    def __init__(self, timeline_path: str):
        self.timeline_path = timeline_path
        self.timeline_fields = ["Timestamp", "Description", "Access Type", "Source CSV"]
        self.timeline_file = open(timeline_path, "w", newline="")
        self.timeline_writer = csv.writer(self.timeline_file)
        self.timeline_writer.writerow(self.timeline_fields)
        self.rows = []

    def __del__(self):
        self.timeline_file.close()

    def add(self, group_dict: Dict[str, Any], csv_file: str) -> None:
        row = [group_dict[key] for key in self.timeline_fields if key in group_dict]
        row.extend([csv_file])
        self.rows.append(row)

    def parse_date(record):
        if re.match(r".*\.\d+Z", record[0]):
            return datetime.strptime(record[0], '%Y-%m-%dT%H:%M:%S.%fZ')
        else:
            return datetime.strptime(record[0], '%Y-%m-%dT%H:%M:%SZ')

    def sort_timeline(self):
        sorted_records = sorted(self.rows, key=Timeliner.parse_date)
        for record in sorted_records:
            self.timeline_writer.writerow(record)

class Parser:
    def __init__(
        self, extraction_dir: Path, log_identifiers: List["LogIdentifier"]
    ) -> None:
        self.extraction_dir = extraction_dir
        self.log_identifiers = log_identifiers
        self.Matches = namedtuple(
            "Matches", ["group_dict", "access_type", "should_timeline"]
        )

    def read_parse_logs(self):
        log_file_name_patterns = [
            log_identifiers.filename_pattern for log_identifiers in self.log_identifiers
        ]

        # Searching logs based on the log_file_name_patterns
        matching_logs = []
        for root, _dirs, files in os.walk(self.extraction_dir):
            for log in files:
                for log_file_name_pattern in log_file_name_patterns:
                    if re.fullmatch(log_file_name_pattern, log):
                        matching_logs.append(Path(root) / log)

        # Read files and search for patterns in parallel
        results = self.search_patterns_in_log(matching_logs)

        # Write the results to CSV files in respective directories
        self.create_out_dir_write_csvs(results)

    # Seaching for patterns in the matched logs files
    def search_log(self, log_path: str):
        base_name = os.path.basename(log_path)

        for log_identifier in self.log_identifiers:
            if base_name.startswith(log_identifier.filename_start):
                patterns = log_identifier.content_patterns
                break
        return self.match_patterns_to_logs(log_path, log_identifier.filename_start, patterns)

    def match_patterns_to_logs(self, log_path: str, file_name: str, patterns: List[str]) -> None:
        matches = defaultdict(list)
        
        try:
            file_wrapper = FileWrapper(log_path)

            # Iterate over lines and match patterns
            for line in file_wrapper.iter_lines():
                for content_pattern in patterns:
                    if match := content_pattern.regex.search(line):
                        self.process_match(content_pattern, match, log_path, file_name, matches)

        except Exception as e:
            logger.error("Unhandled error reading file %s: %s", log_path, e)
        
        return matches

    # Process a match by iterating over access types and description handlers.
    def process_match(self, content_pattern, match, log_path, file_name, matches):
        description = match.group("Description")
        
        for access_type in content_pattern.access_types:
            for description_handler in access_type.description_handlers:
                if description_handler.regex.search(description):
                    self.add_match_to_results(match, access_type, description_handler, log_path, file_name, matches)

    def add_match_to_results(self, match, access_type, description_handler, log_path, file_name, matches):
        group_dict = match.groupdict()
        group_dict["Access Type"] = access_type.access_type_name
        group_dict["Source"] = log_path
        
        match_obj = self.Matches(
            group_dict,
            access_type.access_type_name,
            description_handler.should_timeline
        )
        
        matches[file_name].append(match_obj)

    def search_patterns_in_log(self, matching_logs: Dict[str, List[str]]) -> None:
        results = defaultdict(list)
        with ThreadPoolExecutor() as executor:
            future_to_file = {
                executor.submit(self.search_log, log): log for log in matching_logs
            }
            for future in future_to_file:
                log_matches = future.result()
                for key in log_matches:
                    results[key].extend(log_matches[key])
        return results

    # Function to write matches to CSV files
    def write_to_csv(self, log_key: str, matches: List[Any], timeliner: Timeliner):
        if match := matches[0]:
            headers = matches[0].group_dict.keys()
            
            output_directory = self.extraction_dir
            csv_file = output_directory / f"{log_key}.csv"
            os.makedirs(output_directory, exist_ok=True)
            with open(csv_file, "w", newline="") as csvfile:
                csvwriter = csv.writer(csvfile)
                csvwriter.writerow(headers)
                for match in matches:
                    csvwriter.writerow(match.group_dict.values())
                    if match.should_timeline:
                        timeliner.add(match.group_dict, csv_file)

    def create_out_dir_write_csvs(self, results: List[Dict[str, Any]]) -> None:
        timeliner = Timeliner(self.extraction_dir / "Timeline.csv")
        for log_key, matches in results.items():
            self.write_to_csv(log_key, matches, timeliner)

        timeliner.sort_timeline()


class Configure:
    def __init__(self):
        args = self.configure_cli_arguments()
        self.setup_logging(logger, args.log)
        self.input_dir, self.output_dir = self.validate_file_paths(args)

    @staticmethod
    def path(possible_file: str) -> Path:
        return Path(possible_file)
        
    def configure_cli_arguments(self):
        ascii_art_main = art.text2art("QELP",chr_ignore=True, space=1)
        ascii_art_sub = art.text2art("- by Stroz Friedberg",font="slant")
        ascii_art = f"{Fore.CYAN}{ascii_art_main}\n{Fore.CYAN}{ascii_art_sub}"
        parser = argparse.ArgumentParser(
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description=f"{ascii_art}\nQuick ESXi Log Parser parses ESXi logs & produces results in csv format",
        )
        parser.add_argument(
            "input_dir",
            type=self.path,
            help="The input directory containing .zip, .tar.gz, .tgz, or .tar files",
        )
        parser.add_argument(
            "output_dir",
            type=self.path,
            help="The directory where extracted and parsed logs will be stored",
        )
        parser.add_argument(
            "-l",
            "--log",
            help="Path to log file",
            default="qelp.log",
        )
        args = parser.parse_args()
        return args

    def validate_file_paths(self, args: argparse.Namespace) -> tuple[Path, Path]:
        input_dir: Path = args.input_dir
        output_dir: Path = args.output_dir

        if not input_dir.exists() or not input_dir.is_dir():
            raise NotADirectoryError(f"{input_dir} either does not exist or is not a directory; please provide a valid directory path")

        if output_dir.exists():
            if not output_dir.is_dir():
                raise NotADirectoryError(f"{output_dir} is not a directory; please provide a valid directory path")
        
        else:
            output_dir.mkdir()     

        return input_dir, output_dir

    def setup_logging(
        self, logging_obj: logging.Logger, log_file: str, verbose: bool = False
    ) -> None:
        logging_obj.setLevel(logging.DEBUG)

        log_format = logging.Formatter(
            "%(asctime)s %(filename)s %(levelname)s %(module)s "
            "%(funcName)s %(lineno)d %(message)s"
        )

        stderr_handle = logging.StreamHandler()
        if verbose:
            stderr_handle.setLevel(logging.DEBUG)
        else:
            stderr_handle.setLevel(logging.INFO)
        stderr_handle.setFormatter(log_format)

        file_handle = logging.FileHandler(log_file, "a")
        file_handle.setLevel(logging.DEBUG)
        file_handle.setFormatter(log_format)

        logging_obj.addHandler(stderr_handle)
        logging_obj.addHandler(file_handle)
