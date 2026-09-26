import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pandas as pd

from scripts.extract import list_reports, read_reports


class ListReportsTests(unittest.TestCase):
    def test_returns_only_xlsx_files_in_alphabetical_order(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            input_directory = Path(temporary_directory)
            expected_paths = [
                input_directory / 'report_b.xlsx',
                input_directory / 'report_a.xlsx',
                input_directory / 'report_c.XLSX',
            ]
            for report_path in expected_paths:
                report_path.touch()

            (input_directory / 'report.csv').touch()
            (input_directory / 'notes.txt').touch()
            (input_directory / 'not_a_file.xlsx').mkdir()

            result = list_reports(input_data_path=input_directory)

        self.assertEqual(result, sorted(expected_paths))

    def test_rejects_a_path_that_is_not_an_existing_directory(self) -> None:
        missing_directory = Path('directory_that_does_not_exist')

        with self.assertRaisesRegex(
            NotADirectoryError,
            'Input data directory not found',
        ):
            list_reports(input_data_path=missing_directory)


class ReadReportsTests(unittest.TestCase):
    @patch('scripts.extract.pd.read_excel')
    def test_returns_each_report_name_and_dataframe(self, read_excel) -> None:
        report_paths = [Path('report_a.xlsx'), Path('report_b.xlsx')]
        dataframes = [
            pd.DataFrame({'id': [1, 2]}),
            pd.DataFrame({'id': [3]}),
        ]
        read_excel.side_effect = dataframes

        output = StringIO()
        with redirect_stdout(output):
            result = read_reports(reports_list=report_paths)

        self.assertEqual(
            [report['name_report'] for report in result],
            ['report_a.xlsx', 'report_b.xlsx'],
        )
        self.assertIs(result[0]['data_report'], dataframes[0])
        self.assertIs(result[1]['data_report'], dataframes[1])
        self.assertEqual(read_excel.call_args_list[0].args, (report_paths[0],))
        self.assertEqual(read_excel.call_args_list[1].args, (report_paths[1],))
        self.assertIn(
            '[EXTRACT] - Loaded report "report_a.xlsx" | Rows: 2 | Columns: 1',
            output.getvalue(),
        )


if __name__ == '__main__':
    unittest.main()
