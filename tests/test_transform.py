import unittest
from datetime import datetime

import pandas as pd
from pandas.testing import assert_frame_equal

from scripts.transform import (
    CUSTOMERS_COLUMNS,
    MissingRequiredColumnsError,
    parse_date,
    run_transform,
    transform_dataframe,
    unify_dataframes,
    validate_required_columns,
)


def make_dataframe(**overrides: object) -> pd.DataFrame:
    data: dict[str, list[object]] = {
        'id_cliente': [' cli-001 '],
        'nome_cliente': [' Maria da Silva '],
        'cpf': [1234567890],
        'data_nascimento': ['1990-05-10'],
        'data_registro': ['2026-09-25T10:30:45'],
        'email': [' MARIA@EXAMPLE.COM '],
        'status': [' ativo '],
        'coluna_extra': ['remove me'],
    }
    data.update({key: [value] for key, value in overrides.items()})
    return pd.DataFrame(data)


class ValidateRequiredColumnsTests(unittest.TestCase):
    def test_accepts_report_with_all_required_columns(self) -> None:
        validate_required_columns('report.xlsx', make_dataframe())

    def test_lists_every_missing_column_in_schema_order(self) -> None:
        dataframe = make_dataframe().drop(columns=['nome_cliente', 'email'])

        with self.assertRaisesRegex(
            MissingRequiredColumnsError,
            r'report\.xlsx.*"nome_cliente", "email"',
        ):
            validate_required_columns('report.xlsx', dataframe)


class ParseDateTests(unittest.TestCase):
    def test_parses_each_supported_string_format(self) -> None:
        expected = datetime(2026, 9, 25, 10, 30, 45)

        self.assertEqual(parse_date('2026-09-25 10:30:45'), expected)
        self.assertEqual(parse_date('2026-09-25T10:30:45'), expected)
        self.assertEqual(parse_date('2026-09-25'), datetime(2026, 9, 25))

    def test_rejects_invalid_date_instead_of_returning_none(self) -> None:
        with self.assertRaisesRegex(ValueError, 'Invalid date'):
            parse_date('25/09/2026')


class TransformDataframeTests(unittest.TestCase):
    def test_normalizes_values_columns_and_types_without_mutating_source(self) -> None:
        source = make_dataframe()
        source_before = source.copy(deep=True)

        result = transform_dataframe('report.xlsx', source)

        self.assertEqual(list(result.columns), list(CUSTOMERS_COLUMNS))
        self.assertEqual(result.at[0, 'id_cliente'], 'CLI-001')
        self.assertEqual(result.at[0, 'nome_cliente'], 'MARIA DA SILVA')
        self.assertEqual(result.at[0, 'cpf'], '01234567890')
        self.assertEqual(result.at[0, 'email'], 'maria@example.com')
        self.assertEqual(result.at[0, 'status'], 'ATIVO')
        self.assertEqual(result.at[0, 'data_nascimento'], datetime(1990, 5, 10))
        assert_frame_equal(source, source_before)

    def test_identifies_report_and_column_when_date_is_invalid(self) -> None:
        dataframe = make_dataframe(data_registro='not-a-date')

        with self.assertRaisesRegex(
            ValueError,
            r'data_registro.*report\.xlsx.*Invalid date',
        ):
            transform_dataframe('report.xlsx', dataframe)


class UnifyDataframesTests(unittest.TestCase):
    def test_appends_rows_and_resets_index(self) -> None:
        first = transform_dataframe('first.xlsx', make_dataframe())
        second = transform_dataframe(
            'second.xlsx',
            make_dataframe(id_cliente='CLI-002'),
        )

        result = unify_dataframes('second.xlsx', first, second)

        self.assertEqual(len(result), 2)
        self.assertEqual(result.index.tolist(), [0, 1])
        self.assertEqual(result['id_cliente'].tolist(), ['CLI-001', 'CLI-002'])


class RunTransformTests(unittest.TestCase):
    def test_transforms_and_consolidates_extracted_reports(self) -> None:
        reports_data = [
            {
                'name_report': 'first.xlsx',
                'data_report': make_dataframe(id_cliente='cli-001'),
            },
            {
                'name_report': 'second.xlsx',
                'data_report': make_dataframe(id_cliente='cli-002'),
            },
        ]

        result = run_transform(reports_data=reports_data)

        self.assertEqual(len(result), 2)
        self.assertEqual(list(result.columns), list(CUSTOMERS_COLUMNS))
        self.assertEqual(result['id_cliente'].tolist(), ['CLI-001', 'CLI-002'])


if __name__ == '__main__':
    unittest.main()
