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
        'customer_id': [' cust-001 '],
        'customer_name': [' James Smith '],
        'identifier': [' id-000123 '],
        'birth_date': ['1990-05-10'],
        'registration_date': ['2026-09-25T10:30:45'],
        'email': [' JAMES.SMITH@EXAMPLE.COM '],
        'status': [' active '],
        'extra_column': ['remove me'],
    }
    data.update({key: [value] for key, value in overrides.items()})
    return pd.DataFrame(data)


class ValidateRequiredColumnsTests(unittest.TestCase):
    def test_accepts_report_with_all_required_columns(self) -> None:
        validate_required_columns('report.xlsx', make_dataframe())

    def test_lists_every_missing_column_in_schema_order(self) -> None:
        dataframe = make_dataframe().drop(columns=['customer_name', 'email'])

        with self.assertRaisesRegex(
            MissingRequiredColumnsError,
            r'report\.xlsx.*"customer_name", "email"',
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
    def test_preserves_generic_identifiers_without_country_specific_padding(self) -> None:
        for value, expected in [(' 000123 ', '000123'), (12345, '12345')]:
            with self.subTest(identifier=value):
                result = transform_dataframe(
                    'report.xlsx', make_dataframe(identifier=value),
                )

                self.assertEqual(result.at[0, 'identifier'], expected)

    def test_normalizes_values_columns_and_types_without_mutating_source(self) -> None:
        source = make_dataframe()
        source_before = source.copy(deep=True)

        result = transform_dataframe('report.xlsx', source)

        self.assertEqual(list(result.columns), list(CUSTOMERS_COLUMNS))
        self.assertEqual(result.at[0, 'customer_id'], 'CUST-001')
        self.assertEqual(result.at[0, 'customer_name'], 'JAMES SMITH')
        self.assertEqual(result.at[0, 'identifier'], 'id-000123')
        self.assertEqual(result.at[0, 'email'], 'james.smith@example.com')
        self.assertEqual(result.at[0, 'status'], 'ACTIVE')
        self.assertEqual(result.at[0, 'birth_date'], datetime(1990, 5, 10))
        assert_frame_equal(source, source_before)

    def test_identifies_report_and_column_when_date_is_invalid(self) -> None:
        dataframe = make_dataframe(registration_date='not-a-date')

        with self.assertRaisesRegex(
            ValueError,
            r'registration_date.*report\.xlsx.*Invalid date',
        ):
            transform_dataframe('report.xlsx', dataframe)


class UnifyDataframesTests(unittest.TestCase):
    def test_appends_rows_and_resets_index(self) -> None:
        first = transform_dataframe('first.xlsx', make_dataframe())
        second = transform_dataframe(
            'second.xlsx',
            make_dataframe(customer_id='CUST-002'),
        )

        result = unify_dataframes('second.xlsx', first, second)

        self.assertEqual(len(result), 2)
        self.assertEqual(result.index.tolist(), [0, 1])
        self.assertEqual(result['customer_id'].tolist(), ['CUST-001', 'CUST-002'])


class RunTransformTests(unittest.TestCase):
    def test_transforms_and_consolidates_extracted_reports(self) -> None:
        reports_data = [
            {
                'name_report': 'first.xlsx',
                'data_report': make_dataframe(customer_id='cust-001'),
            },
            {
                'name_report': 'second.xlsx',
                'data_report': make_dataframe(customer_id='cust-002'),
            },
        ]

        result = run_transform(reports_data=reports_data)

        self.assertEqual(len(result), 2)
        self.assertEqual(list(result.columns), list(CUSTOMERS_COLUMNS))
        self.assertEqual(result['customer_id'].tolist(), ['CUST-001', 'CUST-002'])


if __name__ == '__main__':
    unittest.main()
