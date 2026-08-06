import pytest
from tests.extraction_ops.mock_toolbelt import TestToolBelt


@pytest.fixture
def test_toolbelt():
    return TestToolBelt
