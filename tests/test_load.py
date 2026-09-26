import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pandas as pd
from pandas.testing import assert_frame_equal

from scripts.load import (
    export_consolidated_dataframe,
    persist_dataframe_to_database,
    run_load,
    verify_output_folder,
)


class VerifyOutputFolderTests(unittest.TestCase):
    def test_creates_and_returns_output_directory(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            root_directory = Path(temporary_directory)

            with patch('scripts.load.ROOT_DIR', root_directory):
                result = verify_output_folder()

            self.assertEqual(result, root_directory / 'data' / 'output')
            self.assertTrue(result.is_dir())


class ExportConsolidatedDataframeTests(unittest.TestCase):
    def test_exports_dataframe_to_output_directory(self) -> None:
        dataframe = pd.DataFrame(
            {'id_cliente': ['CLI-001'], 'nome_cliente': ['MARIA']}
        )

        with TemporaryDirectory() as temporary_directory:
            output_directory = Path(temporary_directory)
            output_file = output_directory / 'clientes_consolidado.xlsx'

            result = export_consolidated_dataframe(
                dataframe=dataframe,
                output_data_path=output_directory,
            )
            exported_dataframe = pd.read_excel(output_file)

        self.assertEqual(result, output_file)
        assert_frame_equal(exported_dataframe, dataframe)


class PersistDataframeToDatabaseTests(unittest.TestCase):
    @patch('scripts.load.PostgresDatabase')
    def test_inserts_dataframe_using_database_context(self, database_class) -> None:
        database = database_class.return_value.__enter__.return_value
        database.insert_dataframe.return_value = 2
        dataframe = pd.DataFrame({'id_cliente': ['CLI-001', 'CLI-002']})

        inserted_rows = persist_dataframe_to_database(
            dataframe=dataframe,
            table_name='clientes',
        )

        self.assertEqual(inserted_rows, 2)
        database_class.assert_called_once_with()
        database.insert_dataframe.assert_called_once_with(
            dataframe=dataframe,
            table_name='clientes',
            if_exists='replace',
        )


class RunLoadTests(unittest.TestCase):
    @patch('scripts.load.persist_dataframe_to_database')
    @patch('scripts.load.export_consolidated_dataframe')
    @patch('scripts.load.verify_output_folder')
    def test_coordinates_local_and_database_persistence(
        self,
        verify_output,
        export_dataframe,
        persist_dataframe,
    ) -> None:
        dataframe = pd.DataFrame({'id_cliente': ['CLI-001']})
        output_directory = Path('data/output')
        verify_output.return_value = output_directory

        result = run_load(
            dataframe=dataframe,
            table_name='clientes',
        )

        self.assertIsNone(result)
        verify_output.assert_called_once_with()
        export_dataframe.assert_called_once_with(
            dataframe=dataframe,
            output_data_path=output_directory,
        )
        persist_dataframe.assert_called_once_with(
            dataframe=dataframe,
            table_name='clientes',
        )


if __name__ == '__main__':
    unittest.main()
