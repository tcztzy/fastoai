from pathlib import Path

import fsspec
import pytest
import yaml


@pytest.fixture
def openapi():
    with fsspec.open(
        "filecache::github://openai:openai-openapi@master/openapi.yaml",
        filecache={"cache_storage": str(Path(__file__).parent)},
    ) as f:
        return yaml.safe_load(f)
