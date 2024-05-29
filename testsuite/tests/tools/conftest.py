"""Tools conftest"""

import json
import os
from pathlib import Path
import pytest


def get_results_dir_path():
    """Method that gives you the path to the directory where you should store test results."""
    try:
        results_dir = os.environ.get("resultsdir")
        return Path(results_dir)
    except KeyError:
        current_file = Path(__file__).resolve()
        project_dir = current_file.parents[3]
        return project_dir / "attachments"


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
    results_dir_path = get_results_dir_path()
    save_as_json(metadata, results_dir_path / "pytest_metadata.json")
