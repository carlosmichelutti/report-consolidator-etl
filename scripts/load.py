from pathlib import Path

import pandas as pd

from database import PostgresDatabase

ROOT_DIR = Path(__file__).resolve().parents[1]


def verify_output_folder() -> Path:
    """
    Ensure that the local output directory exists.

    Returns:
        Path: Absolute path to the ``data/output`` directory.
    """
    output_data_path = ROOT_DIR / 'data' / 'output'

    output_data_path.mkdir(
        parents=True,
        exist_ok=True
    )

    return output_data_path


def export_consolidated_dataframe(
    dataframe: pd.DataFrame,
    output_data_path: Path
) -> Path:
    """
    Export the consolidated DataFrame to a local XLSX file.

    Args:
        dataframe (pd.DataFrame): Consolidated data produced by the transform
            step.
        output_data_path (Path): Existing directory where the consolidated XLSX file
            will be written.

    Returns:
        Path: Path to the exported ``consolidated_clients.xlsx`` file.
    """
    output_file = output_data_path / 'consolidated_clients.xlsx'

    dataframe.to_excel(output_file, index=False)

    print(
        f'[LOAD] - Exported {len(dataframe)} rows to "{output_file}".'
    )

    return output_file


def persist_dataframe_to_database(
    dataframe: pd.DataFrame,
    table_name: str = 'clientes'
) -> int:
    """
    Persist the consolidated DataFrame in PostgreSQL.

    Args:
        dataframe (pd.DataFrame): Consolidated data produced by the transform
            step.
        table_name (str): Destination table, created automatically when absent.

    Returns:
        int: Number of rows submitted for insertion.
    """
    with PostgresDatabase() as database:
        inserted_rows = database.insert_dataframe(
            dataframe=dataframe,
            table_name=table_name,
            if_exists='replace'
        )

    print(
        f'[LOAD] - Inserted {inserted_rows} rows into table "{table_name}".'
    )

    return inserted_rows


def run_load(
    dataframe: pd.DataFrame,
    table_name: str = 'clientes'
) -> None:
    """
    Persist transformed data locally and in PostgreSQL.

    Args:
        dataframe (pd.DataFrame): Consolidated data received from the transform
            layer.
        table_name (str): Destination PostgreSQL table.

    Returns:
        None: This function coordinates both persistence operations and does
            not return a value.
    """
    output_data_path = verify_output_folder()

    export_consolidated_dataframe(
        dataframe=dataframe,
        output_data_path=output_data_path
    )

    persist_dataframe_to_database(
        dataframe=dataframe,
        table_name=table_name
    )
