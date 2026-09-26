from typing import Literal

import pandas as pd
from sqlalchemy import Engine

IfExists = Literal['fail', 'replace', 'append']


def insert_dataframe(
    engine: Engine,
    dataframe: pd.DataFrame,
    table_name: str,
    *,
    schema: str | None = None,
    if_exists: IfExists = 'append',
    index: bool = False,
    chunksize: int = 1_000
) -> int:
    """
    Insert a DataFrame into PostgreSQL in a single transaction.

    The destination table is created automatically when it does not exist.
    Rows are submitted in batches controlled by ``chunksize``.

    Args:
        engine (Engine): SQLAlchemy engine used to open the transaction.
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
    if not table_name.strip():
        raise ValueError('table_name cannot be empty.')
    if chunksize <= 0:
        raise ValueError('chunksize must be greater than zero.')

    with engine.begin() as connection:
        dataframe.to_sql(
            name=table_name,
            con=connection,
            schema=schema,
            if_exists=if_exists,
            index=index,
            chunksize=chunksize
        )

    return len(dataframe)
