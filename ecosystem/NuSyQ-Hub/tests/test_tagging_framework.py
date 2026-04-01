from src.tagging.tagging_framework import TaggingFramework, TaggingFrameworkConfig


def test_process_files_generates_expected_tags_and_categories() -> None:
    config = TaggingFrameworkConfig(
        rules_path="docs/Core/megatag_specifications.md",
        default_category="Operational",
    )
    framework = TaggingFramework(config)
    sample_files = [
        "README.md",
        "src/module_alpha.py",
        "config/settings.json",
        "tests/unit/test_module.py",
    ]

    framework.process_files(sample_files)

    summary = framework.summarize()
    assert summary["README.md"] == 1
    assert summary["src/module_alpha.py"] == 1
    assert summary["config/settings.json"] == 1
    assert summary["tests/unit/test_module.py"] == 1

    results = framework.display_results(as_dict=True)
    assert "tags" in results and "categories" in results
    assert "Configuration" in results["categories"]
    assert "Testing" in results["categories"]


def test_get_category_falls_back_to_default() -> None:
    config = TaggingFrameworkConfig(rules_path="docs/Core/megatag_specifications.md")
    framework = TaggingFramework(config)

    category = framework.get_category("misc/notes.txt")
    assert category == config.default_category
