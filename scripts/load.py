from pathlib import Path

import pandas as pd

from database import PostgresDatabase

ROOT_DIR = Path(__file__).resolve().parents[1]


def verify_output_folder() -> Path:
    """
    Ensure that the local output directory exists.

    The directory is created with all missing parent directories. Calling this
    function when the directory already exists has no effect.

    Returns:
        Path: Absolute path to the ``data/output`` directory.

    Raises:
        OSError: If the directory cannot be created or an existing filesystem
            entry prevents its creation.
    """
    output_path = ROOT_DIR / 'data' / 'output'

    output_path.mkdir(
        parents=True,
        exist_ok=True
    )

    return output_path


def export_consolidated_dataframe(
    dataframe: pd.DataFrame,
    output_dir: Path
) -> Path:
    """
    Export the consolidated DataFrame to a local XLSX file.

    The destination directory must already exist. An existing file at the same
    path is replaced with the current consolidated data.

    Args:
        dataframe (pd.DataFrame): Consolidated data produced by the transform
            step.
        output_dir (Path): Existing directory where the consolidated XLSX file
            will be written.

    Returns:
        Path: Path to the exported ``clientes_consolidado.xlsx`` file.

    Raises:
        OSError: If the destination directory does not exist or the file cannot
            be written.
        ValueError: If the DataFrame contains values unsupported by the Excel
            writer.
        ImportError: If no compatible Excel writer engine is installed.
    """
    output_file = output_dir / 'clientes_consolidado.xlsx'

    dataframe.to_excel(output_file, index=False)

    print(
        f'[LOAD] Exported {len(dataframe)} rows to "{output_file}".'
    )

    return output_file


def persist_dataframe_to_database(
    dataframe: pd.DataFrame,
    table_name: str = 'clientes'
) -> int:
    """
    Persist the consolidated DataFrame in PostgreSQL.

    The destination table is created when absent. When it already exists, it is
    replaced so that it always represents the latest consolidated dataset.

    Args:
        dataframe (pd.DataFrame): Consolidated data produced by the transform
            step.
        table_name (str): Destination table, created automatically when absent.

    Returns:
        int: Number of rows submitted for insertion.

    Raises:
        ValueError: If ``table_name`` is empty.
        sqlalchemy.exc.SQLAlchemyError: If PostgreSQL cannot be reached or the
            table replacement or insertion fails.
    """
    with PostgresDatabase() as database:
        inserted_rows = database.insert_dataframe(
            dataframe=dataframe,
            table_name=table_name,
            if_exists='replace'
        )

    print(
        f'[LOAD] Inserted {inserted_rows} rows into table "{table_name}".'
    )

    return inserted_rows


def run_load(
    dataframe: pd.DataFrame,
    table_name: str = 'clientes'
) -> None:
    """
    Persist transformed data locally and in PostgreSQL.

    The local XLSX file and the PostgreSQL table are replaced with the latest
    consolidated dataset.

    Args:
        dataframe (pd.DataFrame): Consolidated data received from the transform
            layer.
        table_name (str): Destination PostgreSQL table.

    Returns:
        None: This function coordinates both persistence operations and does
            not return a value.

    Raises:
        OSError: If the output directory or XLSX file cannot be created.
        ValueError: If ``table_name`` is empty or the DataFrame cannot be
            exported to Excel.
        ImportError: If no compatible Excel writer engine is installed.
        sqlalchemy.exc.SQLAlchemyError: If PostgreSQL cannot be reached or the
            table replacement or insertion fails.
    """
    output_path = verify_output_folder()

    export_consolidated_dataframe(
        dataframe=dataframe,
        output_dir=output_path
    )

    persist_dataframe_to_database(
        dataframe=dataframe,
        table_name=table_name
    )
