from datetime import datetime
from typing import Literal

import pandas as pd

from scripts.extract import ReportData

CUSTOMERS_COLUMNS = (
    'id_cliente',
    'nome_cliente',
    'cpf',
    'data_nascimento',
    'data_registro',
    'email',
    'status',
)

DATE_FORMATS = (
    '%Y-%m-%d %H:%M:%S',
    '%Y-%m-%dT%H:%M:%S',
    '%Y-%m-%d',
)


class MissingRequiredColumnsError(ValueError):
    """
    Raised when a report does not contain every required column.
    """


def validate_required_columns(name_report: str, dataframe: pd.DataFrame) -> None:
    """
    Ensure that a report contains all columns required by the output schema.

    Args:
        name_report (str): Name of the report being validated, used in error
            messages.
        dataframe (pd.DataFrame): Report data whose columns will be validated.

    Returns:
        None: This function only validates the report and does not return a
            value.

    Raises:
        MissingRequiredColumnsError: If one or more required columns are
            missing from the report.
    """
    missing_columns = [
        column for column in CUSTOMERS_COLUMNS if column not in dataframe.columns
    ]

    if missing_columns:
        columns = ', '.join(f'"{column}"' for column in missing_columns)
        raise MissingRequiredColumnsError(
            f'Report "{name_report}" is missing required columns: {columns}.'
        )


def parse_date(date: str | datetime) -> datetime:
    """
    Parse a supported date string, preserving values already parsed as dates.

    Args:
        date (str | datetime): Date value to parse. Strings must use one of the
            formats declared in ``DATE_FORMATS``.

    Returns:
        datetime: Parsed date, or the original value when it is already a
            ``datetime`` instance.

    Raises:
        TypeError: If ``date`` is neither a string nor a ``datetime``.
        ValueError: If a string does not match any supported date format.
    """
    if isinstance(date, datetime):
        return date

    if not isinstance(date, str):
        raise TypeError(
            f'Date must be a string or datetime, got {type(date)}.'
        )

    normalized_date = date.strip()
    for date_format in DATE_FORMATS:
        try:
            return datetime.strptime(
                normalized_date,
                date_format
            )
        except ValueError:
            continue

    supported_formats = ', '.join(DATE_FORMATS)
    raise ValueError(
        f'Invalid date "{date}". Supported formats: {supported_formats}.'
    )


def normalize_text(
    text: str,
    case: Literal['upper', 'lower', 'capitalize']
) -> str:
    """
    Trim leading and trailing whitespace and normalize the text casing.

    Args:
        text (str): Text value to trim and normalize.
        case (Literal['upper', 'lower', 'capitalize']): Casing transformation
            to apply to the normalized text.

    Returns:
        str: Text without surrounding whitespace and with the requested casing.
    """
    normalized_text = text.strip()

    if case == 'upper':
        return normalized_text.upper()
    if case == 'lower':
        return normalized_text.lower()
    return normalized_text.capitalize()


def remove_unnecessary_columns(
    name_report: str,
    dataframe: pd.DataFrame
) -> pd.DataFrame:
    """
    Remove non-required columns and enforce the canonical column order.

    Args:
        name_report (str): Name of the report, used in the transformation log.
        dataframe (pd.DataFrame): Report data from which unnecessary columns
            will be removed.

    Returns:
        pd.DataFrame: Copy containing only the required columns, ordered as
            defined in ``CUSTOMERS_COLUMNS``.
    """
    remove_columns = [
        column for column in dataframe.columns if column not in CUSTOMERS_COLUMNS
    ]

    if remove_columns:
        print(
            f'[TRANSFORM] - Removing unnecessary columns {remove_columns} '
            f'from report "{name_report}".'
        )

    dataframe = dataframe.loc[:, list(CUSTOMERS_COLUMNS)].copy()

    return dataframe


def transform_dataframe(
    name_report: str,
    dataframe: pd.DataFrame
) -> pd.DataFrame:
    """
    Validate and normalize a single customer report.

    Args:
        name_report (str): Name of the report being transformed, used in logs
            and error messages.
        dataframe (pd.DataFrame): Extracted report data to validate and
            normalize.

    Returns:
        pd.DataFrame: New DataFrame containing only the required columns with
            normalized text, CPF and date values.

    Raises:
        MissingRequiredColumnsError: If the report does not contain every
            required column.
        ValueError: If a value from a date column cannot be parsed.
    """
    validate_required_columns(
        name_report=name_report,
        dataframe=dataframe
    )

    transformed = remove_unnecessary_columns(
        name_report=name_report,
        dataframe=dataframe
    )

    transformed['id_cliente'] = transformed['id_cliente'].map(normalize_text, case='upper')
    transformed['nome_cliente'] = transformed['nome_cliente'].map(normalize_text, case='upper')
    transformed['cpf'] = transformed['cpf'].astype(str).str.strip().str.zfill(11)
    transformed['email'] = transformed['email'].map(normalize_text, case='lower')
    transformed['status'] = transformed['status'].map(normalize_text, case='upper')

    for column in ('data_nascimento', 'data_registro'):
        try:
            transformed[column] = transformed[column].map(parse_date, na_action='ignore')
        except (TypeError, ValueError) as error:
            raise ValueError(
                f'Could not parse column "{column}" from report "{name_report}": '
                f'{error}'
            )

    return transformed


def unify_dataframes(
    name_report: str,
    dataframe_unified: pd.DataFrame,
    dataframe: pd.DataFrame
) -> pd.DataFrame:
    """
    Append a transformed report to the consolidated DataFrame.

    Args:
        name_report (str): Name of the report being appended, used in the
            consolidation log.
        dataframe_unified (pd.DataFrame): DataFrame containing reports already
            consolidated.
        dataframe (pd.DataFrame): Transformed report to append.

    Returns:
        pd.DataFrame: Consolidated DataFrame containing the previous and newly
            appended rows, with a reset sequential index.
    """
    rows_before = len(dataframe_unified)

    dataframe_unified = pd.concat(
        [dataframe_unified, dataframe],
        axis=0,
        ignore_index=True
    )

    print(
        f'[TRANSFORM] - Merging report "{name_report}" into consolidated DataFrame | '
        f'Rows before: {rows_before} | Rows after: {len(dataframe_unified)}'
    )

    return dataframe_unified


def run_transform(reports_data: list[ReportData]) -> pd.DataFrame:
    """
    Transform and consolidate the reports received from the extract layer.

    Args:
        reports_data (list[ReportData]): Reports extracted from the source
            files. Each item contains the report name and its DataFrame.

    Returns:
        pd.DataFrame: Consolidated DataFrame containing the normalized rows
            from every input report.

    Raises:
        ValueError: If a report contains an invalid date value.
        MissingRequiredColumnsError: If any report does not contain every
            required column.
    """
    dataframe_unified = pd.DataFrame(columns=CUSTOMERS_COLUMNS)

    for report_data in reports_data:
        dataframe = transform_dataframe(
            name_report=report_data['name_report'],
            dataframe=report_data['data_report']
        )

        dataframe_unified = unify_dataframes(
            name_report=report_data['name_report'],
            dataframe_unified=dataframe_unified,
            dataframe=dataframe
        )

    return dataframe_unified
