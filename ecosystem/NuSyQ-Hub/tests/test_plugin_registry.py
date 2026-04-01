"""Tests for src/plugins/plugin_registry.py — PluginRegistry."""

import pytest


class TestPluginRegistryBasic:
    """Tests for PluginRegistry register/get/list lifecycle."""

    @pytest.fixture
    def registry(self):
        from src.plugins.plugin_registry import PluginRegistry
        return PluginRegistry()

    def test_instantiation(self, registry):
        assert registry is not None

    def test_empty_on_init(self, registry):
        assert registry.list_plugins() == []

    def test_register_and_get(self, registry):
        registry.register("my_plugin", {"version": "1.0"})
        result = registry.get("my_plugin")
        assert result == {"version": "1.0"}

    def test_get_missing_returns_none(self, registry):
        assert registry.get("nonexistent") is None

    def test_list_after_register(self, registry):
        registry.register("a", 1)
        registry.register("b", 2)
        plugins = registry.list_plugins()
        assert "a" in plugins
        assert "b" in plugins
        assert len(plugins) == 2

    def test_register_duplicate_raises(self, registry):
        registry.register("dup", "first")
        with pytest.raises(ValueError, match="already registered"):
            registry.register("dup", "second")

    def test_register_duplicate_with_override(self, registry):
        registry.register("dup", "first")
        registry.register("dup", "second", override=True)
        assert registry.get("dup") == "second"

    def test_register_various_types(self, registry):
        registry.register("int_plugin", 42)
        registry.register("list_plugin", [1, 2, 3])
        registry.register("dict_plugin", {"key": "value"})
        assert registry.get("int_plugin") == 42
        assert registry.get("list_plugin") == [1, 2, 3]
        assert registry.get("dict_plugin") == {"key": "value"}


class TestPluginRegistryFactory:
    """Tests for PluginRegistry factory registration."""

    @pytest.fixture
    def registry(self):
        from src.plugins.plugin_registry import PluginRegistry
        return PluginRegistry()

    def test_register_factory_and_create(self, registry):
        call_count = [0]

        def make_plugin():
            call_count[0] += 1
            return {"created": True, "count": call_count[0]}

        registry.register_factory("my_factory", make_plugin)
        result = registry.create("my_factory")
        assert result["created"] is True
        assert call_count[0] == 1

    def test_factory_called_each_time(self, registry):
        instances = []

        def make_plugin():
            obj = object()
            instances.append(obj)
            return obj

        registry.register_factory("fresh", make_plugin)
        r1 = registry.create("fresh")
        r2 = registry.create("fresh")
        assert r1 is not r2
        assert len(instances) == 2

    def test_create_missing_factory_raises(self, registry):
        with pytest.raises(ValueError, match="No factory registered"):
            registry.create("nonexistent")

    def test_register_factory_duplicate_raises(self, registry):
        registry.register_factory("f", lambda: None)
        with pytest.raises(ValueError, match="already registered"):
            registry.register_factory("f", lambda: None)

    def test_register_factory_duplicate_with_override(self, registry):
        registry.register_factory("f", lambda: "first")
        registry.register_factory("f", lambda: "second", override=True)
        result = registry.create("f")
        assert result == "second"

    def test_factory_not_listed_in_plugins(self, registry):
        registry.register_factory("f", lambda: None)
        # Factories are separate from plugins
        assert "f" not in registry.list_plugins()


class TestPluginRegistryImport:
    """Verify package-level import works."""

    def test_import(self):
        from src.plugins.plugin_registry import PluginRegistry
        assert PluginRegistry is not None
