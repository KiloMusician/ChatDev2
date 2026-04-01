#!/usr/bin/env python3
"""Validate Kubernetes YAML manifests for syntax correctness."""

import sys
from pathlib import Path

import yaml


def validate_yaml_file(file_path: Path) -> tuple[bool, str]:
    """Validate a single YAML file.

    Returns:
        (is_valid, error_message)
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            # Load all documents in the file (handles multi-doc YAML)
            list(yaml.safe_load_all(f))
        return True, ""
    except yaml.YAMLError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Unexpected error: {e}"


def main():
    """Main validation logic."""
    k8s_dir = Path(__file__).parent.parent / "deploy" / "k8s"

    files_to_check = [
        "rbac.yaml",
        "deployment.yaml",
        "postgres.yaml",
        "redis.yaml",
        "ollama.yaml",
        "kustomization.yaml",
        "namespace.yaml",
        "configmap.yaml",
        "service.yaml",
    ]

    print("🔍 Validating Kubernetes manifests...\n")

    all_valid = True
    for filename in files_to_check:
        file_path = k8s_dir / filename
        if not file_path.exists():
            print(f"⚠️  {filename:30s} - FILE NOT FOUND")
            continue

        is_valid, error = validate_yaml_file(file_path)

        if is_valid:
            print(f"✅ {filename:30s} - VALID")
        else:
            print(f"❌ {filename:30s} - INVALID")
            print(f"   Error: {error}")
            all_valid = False

    print("\n" + "=" * 60)
    if all_valid:
        print("✅ All manifests are syntactically valid!")
        return 0
    else:
        print("❌ Some manifests have errors - see above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
