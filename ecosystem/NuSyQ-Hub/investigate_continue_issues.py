"""Comprehensive investigation of Continue.dev "wonky output" issues.

Investigates:
1. Continue.dev extension cache
2. Model context window size
3. Prompt formatting (how Continue.dev modifies prompts)
4. Response parsing (truncation/reformatting)
"""

import json
from pathlib import Path
from typing import Any

import requests

# Constants
CONTINUE_DIR_NAME = ".continue"
DEFAULT_MODEL = "qwen2.5-coder:7b"
OLLAMA_URL = "http://localhost:11434"
REQUEST_TIMEOUT = 30  # seconds
ACTIVE_STATUS = "✅ ACTIVE"
SEPARATOR_LINE = "=" * 80


class ContinueDevInvestigator:
    """Investigates Continue.dev integration issues with Ollama."""

    def __init__(self):
        self.ollama_url = OLLAMA_URL
        self.continue_config = Path.home() / CONTINUE_DIR_NAME / "config.ts"
        self.continue_dir = Path.home() / CONTINUE_DIR_NAME

    def check_extension_cache(self) -> dict[str, Any]:
        """Check Continue.dev cache files for issues."""
        print(f"\n{SEPARATOR_LINE}")
        print("1. INVESTIGATING CONTINUE.DEV EXTENSION CACHE")
        print(SEPARATOR_LINE)

        cache_results: dict[str, Any] = {
            "cache_dir": str(self.continue_dir),
            "cache_files": [],
            "total_size_mb": 0,
            "recommendations": [],
        }

        if not self.continue_dir.exists():
            cache_results["status"] = "not_found"
            cache_results["recommendations"].append("Continue.dev config directory not found")
            return cache_results

        # Find all cache-related files
        for item in self.continue_dir.rglob("*"):
            if item.is_file():
                size_mb = item.stat().st_size / (1024 * 1024)
                cache_results["cache_files"].append(
                    {"path": str(item.relative_to(self.continue_dir)), "size_mb": round(size_mb, 2)}
                )
                cache_results["total_size_mb"] += size_mb

        results["total_size_mb"] = round(results["total_size_mb"], 2)
        results["file_count"] = len(results["cache_files"])

        # Check for suspicious cache sizes
        if results["total_size_mb"] > 100:
            results["recommendations"].append(
                f"Large cache detected ({results['total_size_mb']} MB). Consider clearing."
            )

        # Look for session/index files that might be corrupted
        cache_patterns = ["index", "session", "cache", ".db", ".sqlite"]
        for cache_file in results["cache_files"]:
            if any(pattern in cache_file["path"].lower() for pattern in cache_patterns):
                results["recommendations"].append(
                    f"Cache file found: {cache_file['path']} ({cache_file['size_mb']} MB)"
                )

        print(f"Cache directory: {results['cache_dir']}")
        print(f"Total cache size: {results['total_size_mb']} MB")
        print(f"Files found: {results['file_count']}")

        if results["recommendations"]:
            print("\n⚠️  Cache Issues:")
            for rec in results["recommendations"]:
                print(f"  - {rec}")
        else:
            print("\n✅ Cache appears normal")

        return results

    def check_context_window_settings(self) -> dict[str, Any]:
        """Check model context window sizes."""
        print(f"\n{SEPARATOR_LINE}")
        print("2. INVESTIGATING MODEL CONTEXT WINDOW SETTINGS")
        print(SEPARATOR_LINE)

        context_results: dict[str, Any] = {"models": [], "issues": []}

        # Get model info from Ollama
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=REQUEST_TIMEOUT)
            models = response.json().get("models", [])

            for model in models:
                model_name = model["name"]

                # Get detailed model info
                show_response = requests.post(
                    f"{self.ollama_url}/api/show",
                    json={"name": model_name},
                    timeout=REQUEST_TIMEOUT,
                )

                if show_response.status_code == 200:
                    model_info = show_response.json()

                    # Extract context window size from modelfile or parameters
                    modelfile = model_info.get("modelfile", "")
                    parameters = model_info.get("parameters", "")

                    # Parse context size
                    context_size = None
                    for line in (modelfile + "\n" + parameters).split("\n"):
                        if "num_ctx" in line.lower():
                            try:
                                context_size = int(line.split()[-1])
                            except (ValueError, IndexError):
                                pass

                    model_data = {
                        "name": model_name,
                        "context_window": context_size or "unknown",
                        "size": model["size"] // (1024**3),  # GB
                        "family": model.get("details", {}).get("family", "unknown"),
                    }

                    context_results["models"].append(model_data)

                    # Check for small context windows
                    if context_size and context_size < 2048:
                        context_results["issues"].append(
                            f"{model_name}: Small context window ({context_size} tokens)"
                        )

            print(f"Models analyzed: {len(context_results['models'])}")
            print("\nContext Window Sizes:")
            for model in context_results["models"]:
                ctx = model["context_window"]
                ctx_str = f"{ctx} tokens" if isinstance(ctx, int) else ctx
                print(f"  {model['name']:<30} {ctx_str}")

            if context_results["issues"]:
                print("\n⚠️  Context Window Issues:")
                for issue in context_results["issues"]:
                    print(f"  - {issue}")
            else:
                print("\n✅ All context windows appear adequate")

        except requests.RequestException as e:
            context_results["error"] = str(e)
            print(f"\n❌ Error checking models: {e}")

        return context_results

    def test_prompt_formatting(self) -> dict[str, Any]:
        """Test how prompts are formatted when sent to Ollama."""
        print("\n" + "=" * 80)
        print("3. INVESTIGATING PROMPT FORMATTING")
        print("=" * 80)

        results: dict[str, Any] = {"tests": [], "issues": []}

        test_prompts = [
            "Write a Python function to calculate factorial:",
            "def fibonacci(n):",
            "Explain the concept of recursion in programming",
        ]

        for prompt in test_prompts:
            print(f"\n📝 Testing prompt: '{prompt[:50]}...'")

            # Test 1: Direct Ollama API
            try:
                response = requests.post(
                    f"{self.ollama_url}/api/generate",
                    json={"model": DEFAULT_MODEL, "prompt": prompt, "stream": False},
                )

                if response.status_code == 200:
                    ollama_response = response.json()
                    output = ollama_response.get("response", "")

                    test_result = {
                        "prompt": prompt,
                        "output_length": len(output),
                        "output_preview": output[:200],
                        "contains_code": "```" in output or "def " in output,
                        "appears_truncated": len(output) < 50,
                    }

                    results["tests"].append(test_result)

                    print(f"  ✅ Output length: {len(output)} chars")
                    print(f"  ✅ Contains code: {test_result['contains_code']}")
                    print(f"  Preview: {output[:100]}...")

                    if test_result["appears_truncated"]:
                        results["issues"].append(f"Suspiciously short response for: '{prompt}'")
                        print("  ⚠️  Response seems truncated!")

            except requests.RequestException as e:
                print(f"  ❌ Error: {e}")
                results["issues"].append(f"Failed to test prompt: {e!s}")

        if not results["issues"]:
            print("\n✅ All prompts generated good responses")
        else:
            print("\n⚠️  Prompt Issues Found:")
            for issue in results["issues"]:
                print(f"  - {issue}")

        return results

    def test_response_parsing(self) -> dict[str, Any]:
        """Test if responses are being truncated or reformatted."""
        print("\n" + "=" * 80)
        print("4. INVESTIGATING RESPONSE PARSING")
        print("=" * 80)

        results: dict[str, Any] = {"streaming_test": {}, "non_streaming_test": {}, "issues": []}

        test_prompt = "Write a detailed Python class with multiple methods:"

        # Test streaming vs non-streaming
        print("\n📊 Testing streaming vs non-streaming responses...")

        # Non-streaming
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={"model": DEFAULT_MODEL, "prompt": test_prompt, "stream": False},
                timeout=REQUEST_TIMEOUT,
            )

            if response.status_code == 200:
                data = response.json()
                results["non_streaming_test"] = {
                    "length": len(data.get("response", "")),
                    "total_duration_ms": data.get("total_duration", 0) // 1_000_000,
                    "eval_count": data.get("eval_count", 0),
                    "done": data.get("done", False),
                }
                print(f"  Non-streaming: {results['non_streaming_test']['length']} chars")
                print(f"  Tokens generated: {results['non_streaming_test']['eval_count']}")

        except Exception as e:
            results["issues"].append(f"Non-streaming test failed: {e}")
            print(f"  ❌ Non-streaming error: {e}")

        # Streaming (collect all chunks)
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={"model": DEFAULT_MODEL, "prompt": test_prompt, "stream": True},
                stream=True,
                timeout=REQUEST_TIMEOUT,
            )

            if response.status_code == 200:
                full_response = ""
                chunk_count = 0

                for line in response.iter_lines():
                    if line:
                        chunk = json.loads(line)
                        full_response += chunk.get("response", "")
                        chunk_count += 1

                results["streaming_test"] = {"length": len(full_response), "chunks": chunk_count}
                print(
                    f"  Streaming: {results['streaming_test']['length']} chars in {chunk_count} chunks"
                )

        except Exception as e:
            results["issues"].append(f"Streaming test failed: {e}")
            print(f"  ❌ Streaming error: {e}")

        # Compare lengths
        if results["streaming_test"] and results["non_streaming_test"]:
            stream_len = results["streaming_test"]["length"]
            non_stream_len = results["non_streaming_test"]["length"]

            if abs(stream_len - non_stream_len) > 100:
                results["issues"].append(
                    f"Streaming vs non-streaming length mismatch: {stream_len} vs {non_stream_len}"
                )
                print("\n  ⚠️  Length discrepancy detected!")
            else:
                print("\n  ✅ Streaming and non-streaming produce similar lengths")

        return results

    def check_vscode_extension_logs(self) -> dict[str, Any]:
        """Check VS Code extension output logs."""
        print("\n" + "=" * 80)
        print("5. CHECKING VS CODE EXTENSION LOGS")
        print("=" * 80)

        results: dict[str, Any] = {"log_locations": [], "found_logs": False, "recommendations": []}

        # Common VS Code extension log locations
        possible_log_dirs = [
            Path.home() / "AppData" / "Roaming" / "Code" / "logs",
            Path.home() / ".vscode" / "logs",
            Path.home() / ".continue" / "logs",
        ]

        for log_dir in possible_log_dirs:
            if log_dir.exists():
                results["log_locations"].append(str(log_dir))
                results["found_logs"] = True

        print(f"Log directories found: {len(results['log_locations'])}")

        if results["found_logs"]:
            print("\n📁 Check these locations for Continue.dev logs:")
            for loc in results["log_locations"]:
                print(f"  - {loc}")
            results["recommendations"].append(
                "Open VS Code, then Help → Toggle Developer Tools → Console"
            )
            results["recommendations"].append(
                "Check Output panel → Select 'Continue' from dropdown"
            )
        else:
            print("\n⚠️  No log directories found")
            results["recommendations"].append(
                "Enable VS Code logging: File → Preferences → Settings → 'log level'"
            )

        if results["recommendations"]:
            print("\n💡 Recommendations:")
            for rec in results["recommendations"]:
                print(f"  - {rec}")

        return results

    def generate_final_report(self, all_results: dict[str, Any]) -> str:
        """Generate comprehensive final report."""
        print("\n" + "=" * 80)
        print("FINAL INVESTIGATION REPORT")
        print("=" * 80)

        report = []
        report.append("\n## Summary of Findings\n")

        # Cache issues
        cache_results = all_results.get("cache", {})
        if cache_results.get("recommendations"):
            report.append("### ⚠️  Cache Issues Detected")
            for rec in cache_results["recommendations"]:
                report.append(f"- {rec}")
        else:
            report.append("### ✅ Cache: Normal")

        # Context window issues
        context_results = all_results.get("context_window", {})
        if context_results.get("issues"):
            report.append("\n### ⚠️  Context Window Issues")
            for issue in context_results["issues"]:
                report.append(f"- {issue}")
        else:
            report.append("\n### ✅ Context Windows: Adequate")

        # Prompt formatting issues
        prompt_results = all_results.get("prompt_formatting", {})
        if prompt_results.get("issues"):
            report.append("\n### ⚠️  Prompt Formatting Issues")
            for issue in prompt_results["issues"]:
                report.append(f"- {issue}")
        else:
            report.append("\n### ✅ Prompt Formatting: Working")

        # Response parsing issues
        response_results = all_results.get("response_parsing", {})
        if response_results.get("issues"):
            report.append("\n### ⚠️  Response Parsing Issues")
            for issue in response_results["issues"]:
                report.append(f"- {issue}")
        else:
            report.append("\n### ✅ Response Parsing: Working")

        # Action items
        report.append("\n## Recommended Actions\n")
        report.append("1. **Reload VS Code Window**")
        report.append("   - Press Ctrl+Shift+P")
        report.append("   - Type 'Developer: Reload Window'")
        report.append("   - Press Enter")

        if cache_results.get("recommendations"):
            report.append("\n2. **Clear Continue.dev Cache**")
            report.append(f"   - Delete contents of: {cache_results.get('cache_dir')}")
            report.append("   - Keep config.ts, delete session/cache files")

        report.append("\n3. **Check Continue.dev Extension Output**")
        report.append("   - Open VS Code")
        report.append("   - View → Output")
        report.append("   - Select 'Continue' from dropdown")
        report.append("   - Look for error messages")

        report.append("\n4. **Test Different Models**")
        report.append("   - Try starcoder2:15b (may have different behavior)")
        report.append("   - Try codellama:7b")
        report.append("   - Compare outputs to identify model-specific issues")

        report.append("\n5. **Compare Side-by-Side**")
        report.append("   - Test same prompt in Continue.dev chat")
        report.append("   - Test same prompt via direct Ollama API")
        report.append("   - Document any differences in formatting/quality")

        report_text = "\n".join(report)
        print(report_text)

        # Save report
        report_file = Path("continue_dev_investigation_report.md")
        report_file.write_text(report_text, encoding="utf-8")
        print(f"\n📄 Report saved to: {report_file.absolute()}")

        return report_text

    def run_full_investigation(self):
        """Run complete investigation."""
        print("\n" + "🔍" * 40)
        print(" CONTINUE.DEV 'WONKY OUTPUT' INVESTIGATION")
        print("🔍" * 40)

        all_results: dict[str, Any] = {}

        # Run all checks
        all_results["cache"] = self.check_extension_cache()
        all_results["context_window"] = self.check_context_window_settings()
        all_results["prompt_formatting"] = self.test_prompt_formatting()
        all_results["response_parsing"] = self.test_response_parsing()
        all_results["vscode_logs"] = self.check_vscode_extension_logs()

        # Generate final report
        self.generate_final_report(all_results)

        return all_results


if __name__ == "__main__":
    investigator = ContinueDevInvestigator()
    results = investigator.run_full_investigation()
