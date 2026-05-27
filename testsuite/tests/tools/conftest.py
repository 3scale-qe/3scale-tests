"""Tools conftest"""

import json

import pytest

from testsuite.utils import get_results_dir_path


def save_as_json(data, path):
    """
    Save data to the file specified by path in json format.
    It creates the dirs on the road.
    Args:
         :param data: Data to be stored
         :param path: path to the file
    """
    path.parents[0].mkdir(exist_ok=True)
    with open(path, "w", encoding="utf-8") as f_handler:
        json.dump(data, f_handler, indent=4)
        f_handler.write("\n")


@pytest.hookimpl(trylast=True)
def pytest_metadata(metadata):
    """Saves metadata to the attachments directory in json format"""
    # path to resultsdir folder defaults to root of testsuite repository
    results_dir_path = get_results_dir_path()
    save_as_json(metadata, results_dir_path / "attachments" / "pytest_metadata.json")
