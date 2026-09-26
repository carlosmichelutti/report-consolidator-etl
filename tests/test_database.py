import unittest
from unittest.mock import MagicMock, patch

import pandas as pd
from pydantic import ValidationError

from database import DatabaseSettings, PostgresDatabase, insert_dataframe


class DatabaseConfigTests(unittest.TestCase):
    @patch.dict(
        'os.environ',
        {
            'DATABASE_HOST': 'db.internal',
            'DATABASE_PORT': '5434',
            'DATABASE_NAME': 'analytics',
            'DATABASE_USER': 'etl+user',
            'DATABASE_PASSWORD': 'secret@word',
        },
        clear=True,
    )
    def test_builds_an_encoded_database_url_from_environment(self) -> None:
        config = DatabaseSettings(_env_file=None)

        self.assertEqual(config.host, 'db.internal')
        self.assertEqual(config.port, 5434)
        self.assertEqual(
            config.database_url,
            'postgresql+psycopg2://etl%2Buser:secret%40word@db.internal:5434/analytics',
        )

    @patch.dict(
        'os.environ',
        {
            'DATABASE_HOST': 'localhost',
            'DATABASE_PORT': 'invalid',
            'DATABASE_NAME': 'postgres',
            'DATABASE_USER': 'postgres',
            'DATABASE_PASSWORD': 'password',
        },
        clear=True,
    )
    def test_rejects_an_invalid_port(self) -> None:
        with self.assertRaises(ValidationError):
            DatabaseSettings(_env_file=None)


class PostgresDatabaseTests(unittest.TestCase):
    def test_checks_connection_with_a_simple_query(self) -> None:
        engine = MagicMock()
        connection = engine.connect.return_value.__enter__.return_value

        PostgresDatabase(engine=engine).check_connection()

        engine.connect.assert_called_once_with()
        executed_statement = connection.execute.call_args.args[0]
        self.assertEqual(str(executed_statement), 'SELECT 1')

    def test_inserts_dataframe_inside_a_transaction(self) -> None:
        engine = MagicMock()
        connection = engine.begin.return_value.__enter__.return_value
        dataframe = pd.DataFrame({'id': [1, 2]})

        with patch.object(dataframe, 'to_sql') as to_sql:
            inserted_rows = PostgresDatabase(engine=engine).insert_dataframe(
                dataframe,
                'customers',
                schema='public',
                chunksize=500,
            )

        self.assertEqual(inserted_rows, 2)
        engine.begin.assert_called_once_with()
        to_sql.assert_called_once_with(
            name='customers',
            con=connection,
            schema='public',
            if_exists='append',
            index=False,
            chunksize=500,
        )

    def test_rejects_an_empty_table_name_before_connecting(self) -> None:
        engine = MagicMock()

        with self.assertRaisesRegex(ValueError, 'table_name'):
            PostgresDatabase(engine=engine).insert_dataframe(
                pd.DataFrame({'id': [1]}),
                '   ',
            )

        engine.begin.assert_not_called()

    @patch('database.PostgresDatabase')
    def test_public_insert_helper_disposes_its_database(
        self,
        database_class,
    ) -> None:
        database = database_class.return_value.__enter__.return_value
        database.insert_dataframe.return_value = 2
        dataframe = pd.DataFrame({'id': [1, 2]})

        inserted_rows = insert_dataframe(
            dataframe,
            'customers',
            chunksize=250,
        )

        self.assertEqual(inserted_rows, 2)
        database_class.assert_called_once_with()
        database.insert_dataframe.assert_called_once_with(
            dataframe=dataframe,
            table_name='customers',
            schema=None,
            if_exists='append',
            index=False,
            chunksize=250,
        )


if __name__ == '__main__':
    unittest.main()
