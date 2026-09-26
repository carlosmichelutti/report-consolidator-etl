from pathlib import Path
from typing import TypedDict

import pandas as pd

ROOT_DIR = Path(__file__).parents[1]
DATA_DIR = ROOT_DIR / 'data' / 'input'


class ReportData(TypedDict):
    """
    Represent an XLSX report loaded into memory.
    """

    name_report: str
    data_report: pd.DataFrame


def list_reports(input_data_path: Path) -> list[Path]:
    """
    List XLSX report files from an input directory.

    Args:
        input_data_path (Path): Directory containing the source report files.

    Returns:
        list[Path]: Paths to the XLSX reports, sorted alphabetically.

    Raises:
        NotADirectoryError: If ``input_data_path`` is not an existing
            directory.
    """
    if not input_data_path.is_dir():
        raise NotADirectoryError(
            f'Input data directory not found: "{input_data_path}".'
        )

    return sorted(
        report_path
        for report_path in input_data_path.glob('*.xlsx')
        if report_path.is_file()
    )


def read_reports(reports_list: list[Path]) -> list[ReportData]:
    """
    Read XLSX reports and return their names and tabular data.

    Args:
        reports_list (list[Path]): Paths to the XLSX reports to be read.

    Returns:
        list[ReportData]: Report dictionaries containing ``name_report`` with
            the source file name and ``data_report`` with its pandas DataFrame.
    """
    reports_data: list[ReportData] = []
    for report_path in reports_list:
        report_dataframe = pd.read_excel(report_path)
        number_rows, number_columns = report_dataframe.shape
        reports_data.append(
            {
                'name_report': report_path.name,
                'data_report': report_dataframe
            }
        )

        print(
            f'[EXTRACT] Loaded report "{report_path.name}" | '
            f'Rows: {number_rows} | Columns: {number_columns}'
        )

    return reports_data


def run_extract() -> list[ReportData]:
    """
    Load every XLSX report from the configured input directory.

    Returns:
        list[ReportData]: Reports loaded from ``DATA_DIR``.

    Raises:
        ValueError: If the input directory contains no XLSX report files.
    """
    reports_list = list_reports(input_data_path=DATA_DIR)

    if not reports_list:
        raise ValueError(f'No XLSX report files found in "{DATA_DIR}" folder')

    reports_data = read_reports(reports_list=reports_list)
    return reports_data
