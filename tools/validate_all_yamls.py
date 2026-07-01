"""
Validate All YAML Workflow Configurations

This tool performs strict validation on all YAML workflow configuration files
in the yaml_instance/ directory. It ensures configuration integrity and prevents
runtime errors by catching issues early in the development process.

Purpose:
- Validates YAML syntax and schema compliance for all workflow configurations
- Prevents invalid configurations from causing runtime failures
- Essential for CI/CD pipelines to ensure code quality
- Provides detailed error reporting for debugging

Usage:
    python tools/validate_all_yamls.py
    # or via Makefile:
    make validate-yamls
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from entity.configs.edge.edge_condition import (
    FunctionEdgeConditionConfig,
    KeywordEdgeConditionConfig,
)
from entity.configs.edge.edge_processor import (
    FunctionEdgeProcessorConfig,
    RegexEdgeProcessorConfig,
)
from entity.configs.node.agent import AgentConfig
from entity.configs.node.human import HumanConfig
from entity.configs.node.literal import LiteralNodeConfig
from entity.configs.node.loop_counter import LoopCounterConfig
from entity.configs.node.memory import (
    BlackboardMemoryConfig,
    FileMemoryConfig,
    SimpleMemoryConfig,
)
from entity.configs.node.passthrough import PassthroughConfig
from entity.configs.node.python_runner import PythonRunnerConfig
from entity.configs.node.subgraph import (
    SubgraphConfig,
    SubgraphFileConfig,
    SubgraphInlineConfig,
    iter_subgraph_source_registrations,
    register_subgraph_source,
)
from entity.configs.node.thinking import ReflectionThinkingConfig
from check.check_workflow import check_workflow_structure
from check.check_yaml import validate_design
from schema_registry import (
    iter_edge_condition_schemas,
    iter_edge_processor_schemas,
    iter_memory_store_schemas,
    iter_model_provider_schemas,
    iter_node_schemas,
    iter_thinking_schemas,
    register_edge_condition_schema,
    register_edge_processor_schema,
    register_memory_store_schema,
    register_model_provider_schema,
    register_node_schema,
    register_thinking_schema,
)
from utils.io_utils import read_yaml


def _ensure_validation_registries_populated() -> None:
    node_schemas = {
        "agent": AgentConfig,
        "human": HumanConfig,
        "subgraph": SubgraphConfig,
        "python": PythonRunnerConfig,
        "passthrough": PassthroughConfig,
        "literal": LiteralNodeConfig,
        "loop_counter": LoopCounterConfig,
    }
    for name, config_cls in node_schemas.items():
        if name not in iter_node_schemas():
            register_node_schema(name, config_cls=config_cls)

    memory_schemas = {
        "simple": SimpleMemoryConfig,
        "file": FileMemoryConfig,
        "blackboard": BlackboardMemoryConfig,
    }
    for name, config_cls in memory_schemas.items():
        if name not in iter_memory_store_schemas():
            register_memory_store_schema(name, config_cls=config_cls)

    if "reflection" not in iter_thinking_schemas():
        register_thinking_schema("reflection", config_cls=ReflectionThinkingConfig)

    if "openai" not in iter_model_provider_schemas():
        register_model_provider_schema("openai", label="OpenAI")
    if "gemini" not in iter_model_provider_schemas():
        register_model_provider_schema("gemini", label="Google Gemini")

    edge_condition_schemas = {
        "function": FunctionEdgeConditionConfig,
        "keyword": KeywordEdgeConditionConfig,
    }
    for name, config_cls in edge_condition_schemas.items():
        if name not in iter_edge_condition_schemas():
            register_edge_condition_schema(name, config_cls=config_cls)

    edge_processor_schemas = {
        "regex_extract": RegexEdgeProcessorConfig,
        "function": FunctionEdgeProcessorConfig,
    }
    for name, config_cls in edge_processor_schemas.items():
        if name not in iter_edge_processor_schemas():
            register_edge_processor_schema(name, config_cls=config_cls)

    if not iter_subgraph_source_registrations():
        register_subgraph_source("config", config_cls=SubgraphInlineConfig, description="Inline subgraph definition")
        register_subgraph_source("file", config_cls=SubgraphFileConfig, description="External YAML subgraph file")


def validate_all():
    base_dir = Path("yaml_instance")
    if not base_dir.exists():
        print(f"Directory {base_dir} not found.")
        sys.exit(1)

    # Recursive search for all .yaml files
    files = sorted(list(base_dir.rglob("*.yaml")))

    if not files:
        print("No YAML files found.")
        return

    _ensure_validation_registries_populated()

    print(f"Found {len(files)} YAML files. Running schema and workflow validation...\n")

    passed = 0
    failed = 0
    failed_files = []

    for yaml_file in files:
        # Use relative path for cleaner output
        try:
            rel_path = yaml_file.relative_to(Path.cwd())
        except ValueError:
            rel_path = yaml_file

        try:
            raw_data = read_yaml(yaml_file)
            design_errors = validate_design(raw_data)
            workflow_errors = [] if design_errors else check_workflow_structure(raw_data)

            if design_errors or workflow_errors:
                print(f"{rel_path}")
                for err in design_errors:
                    print(f"  Schema Error: {err}")
                for err in workflow_errors:
                    print(f"  Workflow Error: {err}")
                failed += 1
                failed_files.append(str(rel_path))
                continue

            print(f"{rel_path}")
            passed += 1
        except Exception as exc:
            print(f"{rel_path}")
            print(f"  Error: {exc}")
            failed += 1
            failed_files.append(str(rel_path))

    print("\n" + "=" * 40)
    print(f"YAML Validation Summary")
    print("=" * 40)
    print(f"Total Files: {len(files)}")
    print(f"Passed:      {passed}")
    print(f"Failed:      {failed}")

    if failed > 0:
        print("\nFailed Files:")
        for f in failed_files:
            print(f"- {f}")

    # Overall validation status
    print("\n" + "=" * 40)
    print("Overall Validation Status")
    print("=" * 40)

    if failed > 0:
        print("YAML validation: FAILED")
        sys.exit(1)
    else:
        print("All validations passed successfully.")
        sys.exit(0)


if __name__ == "__main__":
    validate_all()
