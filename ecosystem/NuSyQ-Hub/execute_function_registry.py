"""🔍 Execute Complete Function Registry
Direct execution with visible output

OmniTag: {
    "purpose": "Execute function registry with visible output",
    "dependencies": ["complete_function_registry"],
    "context": "Function analysis and undefined call detection",
    "evolution_stage": "v1.0"
}
"""

import sys
import traceback
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))


def execute_function_registry():
    """Execute the complete function registry with error handling"""
    print("🔍 Executing Complete Function Registry")
    print("=" * 60)

    try:
        # Import and create registry
        from complete_function_registry import CompleteFunctionRegistry

        print("📁 Creating function registry...")
        registry = CompleteFunctionRegistry()

        print("🔍 Scanning repository for functions...")
        scan_results = registry.scan_repository()

        print("📊 Scan Results:")
        print(f"   Total files scanned: {scan_results['total_files']}")
        print(f"   Python files analyzed: {scan_results['python_files']}")
        print(f"   Total functions found: {scan_results['total_functions']}")
        print(f"   Total function calls: {scan_results['total_calls']}")
        print(f"   Potentially undefined calls: {scan_results['undefined_calls']}")

        print("\n📂 Functions by category:")
        for category, count in scan_results["functions_by_category"].items():
            print(f"   {category}: {count} functions")

        print("\n📄 Generating comprehensive function reference...")
        reference_path = registry.generate_function_reference()
        print(f"✅ Function reference generated: {reference_path}")

        print("\n📄 Generating JSON data export...")
        json_path = registry.export_json_data()
        print(f"✅ JSON data exported: {json_path}")

        # Show some sample functions
        print("\n🔍 Sample function definitions (first 10):")
        functions = scan_results.get("all_functions", [])
        for i, func in enumerate(functions[:10]):
            print(f"   {i + 1}. {func['name']} ({func['file']}:{func['line']})")

        # Show undefined calls if any
        undefined_calls = scan_results.get("potentially_undefined", [])
        if undefined_calls:
            print("\n⚠️ Potentially undefined function calls (first 10):")
            for i, call in enumerate(undefined_calls[:10]):
                print(f"   {i + 1}. {call['call']} in {call['file']}:{call['line']}")
        else:
            print("\n✅ No potentially undefined function calls detected!")

        return True

    except Exception as e:
        print(f"❌ Error executing function registry: {e}")
        print("📋 Full traceback:")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = execute_function_registry()

    if success:
        print("\n🎉 Function registry execution completed successfully!")
        print("📄 Check the generated files for complete function reference")
    else:
        print("\n💥 Function registry execution failed")

    print("\n🏁 Execution complete!")
