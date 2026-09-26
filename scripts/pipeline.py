import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, ROOT_DIR.as_posix())

from scripts.extract import run_extract
from scripts.load import run_load
from scripts.transform import run_transform


def run_pipeline() -> None:
    """
    Run the complete ETL pipeline in dependency order.

    Returns:
        None: The pipeline performs its work through the side effects of the
            load stage and does not return a value.
    """
    reports_data = run_extract()
    dataframe = run_transform(
        reports_data=reports_data
    )
    run_load(
        dataframe=dataframe,
        table_name='clientes'
    )


if __name__ == '__main__':
    run_pipeline()
