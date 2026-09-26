import pandas as pd

from database.config import DatabaseSettings, settings
from database.session import PostgresDatabase
from database.writer import IfExists

__all__ = [
    'DatabaseSettings',
    'IfExists',
    'PostgresDatabase',
    'insert_dataframe',
    'settings'
]


def insert_dataframe(
    dataframe: pd.DataFrame,
    table_name: str,
    *,
    schema: str | None = None,
    if_exists: IfExists = 'append',
    index: bool = False,
    chunksize: int = 1_000
) -> int:
    """
    Insert a DataFrame using a short-lived database facade.

    Args:
        dataframe (pd.DataFrame): Tabular data to persist.
        table_name (str): Destination table name.
        schema (str | None): Optional destination schema. Uses the database
            default when omitted.
        if_exists (IfExists): Behavior when the destination table exists.
        index (bool): Whether to persist the DataFrame index as a column.
        chunksize (int): Maximum number of rows sent in each batch.

    Returns:
        int: Number of DataFrame rows submitted for insertion.

    Raises:
        ValueError: If ``table_name`` is empty or ``chunksize`` is not
            greater than zero.
    """
    with PostgresDatabase() as database:
        return database.insert_dataframe(
            dataframe=dataframe,
            table_name=table_name,
            schema=schema,
            if_exists=if_exists,
            index=index,
            chunksize=chunksize
        )
