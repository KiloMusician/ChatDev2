import json

from src.shared.model_registry import ModelRegistry


def test_validate_and_register(tmp_path):
    registry_file = tmp_path / "registry.json"
    reg = ModelRegistry(path=registry_file)

    # missing required fields -> validation fails
    valid, errors = reg.validate_metadata({"name": "no-path"})
    assert not valid
    assert "missing" in errors[0]

    # valid metadata
    meta = {
        "path": "/models/gpt-oss-20b.gguf",
        "name": "gpt-oss-20b",
        "source": "lmstudio",
        "format": "gguf",
        "size_bytes": 123456,
    }
    valid, errors = reg.validate_metadata(meta)
    assert valid
    assert errors == []

    # dry-run should return False and not create file
    assert reg.register_model(meta, apply=False) is False
    assert not registry_file.exists()

    # apply should persist
    assert reg.register_model(meta, apply=True) is True
    assert registry_file.exists()

    # read back
    data = json.loads(registry_file.read_text(encoding="utf-8"))
    assert isinstance(data, list)
    assert any(item.get("path") == meta["path"] for item in data)

    # update existing
    meta2 = {
        "path": "/models/gpt-oss-20b.gguf",
        "name": "gpt-oss-20b",
        "source": "lmstudio",
        "format": "gguf",
        "size_bytes": 999999,
    }
    assert reg.register_model(meta2, apply=True) is True
    data2 = json.loads(registry_file.read_text(encoding="utf-8"))
    assert any(item.get("size_bytes") == 999999 for item in data2)
