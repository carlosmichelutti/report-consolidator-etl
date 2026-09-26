from types import TracebackType
from typing import Self

import pandas as pd
from sqlalchemy import Engine, create_engine, text

from database.config import settings
from database.writer import IfExists, insert_dataframe


class PostgresDatabase:
    """
    Manage PostgreSQL connections and DataFrame persistence.
    """

    def __init__(self, engine: Engine | None = None) -> None:
        """
        Initialize the database facade.

        Args:
            engine (Engine | None): Existing SQLAlchemy engine to reuse. When
                omitted, an engine is created from the application settings.
        """
        self.engine = engine if engine is not None else create_engine(
            settings.database.database_url,
            pool_pre_ping=True
        )

    def check_connection(self) -> None:
        """
        Verify that PostgreSQL answers a simple query.
        """
        with self.engine.connect() as connection:
            connection.execute(text('SELECT 1'))

    def insert_dataframe(
        self,
        dataframe: pd.DataFrame,
        table_name: str,
        *,
        schema: str | None = None,
        if_exists: IfExists = 'append',
        index: bool = False,
        chunksize: int = 1_000
    ) -> int:
        """
        Insert a DataFrame using the engine managed by this instance.

        Args:
            dataframe (pd.DataFrame): Tabular data to persist.
            table_name (str): Destination table name.
            schema (str | None): Optional destination schema. Uses the
                database default when omitted.
            if_exists (IfExists): Behavior when the destination table exists.
            index (bool): Whether to persist the DataFrame index as a column.
            chunksize (int): Maximum number of rows sent in each batch.

        Returns:
            int: Number of DataFrame rows submitted for insertion.
        """
        return insert_dataframe(
            engine=self.engine,
            dataframe=dataframe,
            table_name=table_name,
            schema=schema,
            if_exists=if_exists,
            index=index,
            chunksize=chunksize
        )

    def close(self) -> None:
        """
        Release all pooled database connections.
        """
        self.engine.dispose()

    def __enter__(self) -> Self:
        """
        Enter the managed database context.

        Returns:
            Self: This database facade instance.
        """
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None
    ) -> None:
        """
        Exit the managed context and dispose of the engine.

        Args:
            exc_type (type[BaseException] | None): Exception type raised in
                the context, if any.
            exc_value (BaseException | None): Exception instance raised in the
                context, if any.
            traceback (TracebackType | None): Associated traceback, if any.
        """
        self.close()
