"""Module for pytest fixtures."""

import logging
from pathlib import Path

import pytest

from metakb.harvesters.base import Harvester
from metakb.harvesters.moa import MoaHarvester
from metakb.normalizers import ViccNormalizers
from metakb.repository.neo4j_repository import Neo4jRepository, get_driver
from metakb.schemas.app import SourceName
from metakb.source_data import SourceDataStore

TEST_DATA_DIR = Path(__file__).resolve().parents[0] / "data"
TEST_HARVESTERS_DIR = TEST_DATA_DIR / "harvesters"
TEST_TRANSFORMERS_DIR = TEST_DATA_DIR / "transformers"


def pytest_addoption(parser):
    """Add custom commands to pytest invocation.

    See https://docs.pytest.org/en/7.1.x/reference/reference.html#parser
    """
    parser.addoption(
        "--verbose-logs",
        action="store_true",
        default=False,
        help="show noisy module logs",
    )


def pytest_configure(config):
    """Configure pytest setup."""
    logging.getLogger(__name__).error(config.getoption("--verbose-logs"))
    if not config.getoption("--verbose-logs"):
        for lib in (
            "botocore",
            "boto3",
            "urllib3.connectionpool",
            "neo4j.pool",
            "neo4j.io",
        ):
            logging.getLogger(lib).setLevel(logging.ERROR)


@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    return TEST_DATA_DIR


@pytest.fixture
def moa_harvester(tmp_path: Path) -> MoaHarvester:
    return MoaHarvester(
        SourceDataStore(src_name=SourceName.MOA, harvested_dir=tmp_path)
    )


def check_source_harvest(harvester: Harvester):
    """Test that source harvest method works correctly"""
    harvested_data_path = harvester.harvest()
    try:
        assert harvested_data_path.exists()
        assert harvested_data_path.is_file()
    finally:
        if harvested_data_path.exists():
            harvested_data_path.unlink()
        assert not harvested_data_path.exists()


@pytest.fixture(scope="module")
def normalizers():
    """Provide normalizers to querying/transformation tests."""
    return ViccNormalizers()


@pytest.fixture
def repository():
    """Provide a new repository session"""
    driver = get_driver()
    session = driver.session()

    yield Neo4jRepository(session)

    session.close()
    driver.close()
