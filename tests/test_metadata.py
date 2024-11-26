from fastoai.models import WithMetadata


def test_metadata_mixin():
    assert WithMetadata().model_dump(exclude_none=True) == {}
    assert WithMetadata(metadata={"key": "value"}).model_dump(by_alias=True) == {
        "metadata": {"key": "value"}
    }
    assert WithMetadata.model_json_schema(by_alias=True) == {
        "title": "WithMetadata",
        "type": "object",
        "properties": {
            "metadata": {"type": "object", "default": None, "title": "Metadata"}
        },
    }
