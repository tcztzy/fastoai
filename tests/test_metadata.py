from fastoai.models.user import WithMetadata


def test_metadata_mixin():
    assert WithMetadata().model_dump(exclude_none=True) == {}
    assert WithMetadata(metadata={"key": "value"}).model_dump(by_alias=True) == {
        "metadata": {"key": "value"}
    }
