import unittest
from unittest.mock import Mock, call, patch

import pandas as pd

from scripts.pipeline import run_pipeline


class RunPipelineTests(unittest.TestCase):
    @patch('scripts.pipeline.run_load')
    @patch('scripts.pipeline.run_transform')
    @patch('scripts.pipeline.run_extract')
    def test_passes_each_stage_result_to_the_next_stage(
        self,
        run_extract,
        run_transform,
        run_load,
    ) -> None:
        reports_data = [
            {
                'name_report': 'report.xlsx',
                'data_report': pd.DataFrame({'id_cliente': ['CLI-001']}),
            }
        ]
        dataframe = pd.DataFrame({'id_cliente': ['CLI-001']})
        run_extract.return_value = reports_data
        run_transform.return_value = dataframe
        stage_order = Mock()
        stage_order.return_value = None
        run_extract.side_effect = lambda: (
            stage_order('extract') or reports_data
        )
        run_transform.side_effect = lambda **kwargs: (
            stage_order('transform') or dataframe
        )
        run_load.side_effect = lambda **kwargs: stage_order('load')

        result = run_pipeline()

        self.assertIsNone(result)
        run_extract.assert_called_once_with()
        run_transform.assert_called_once_with(reports_data=reports_data)
        run_load.assert_called_once_with(
            dataframe=dataframe,
            table_name='clientes',
        )
        self.assertEqual(
            stage_order.call_args_list,
            [call('extract'), call('transform'), call('load')],
        )


if __name__ == '__main__':
    unittest.main()
