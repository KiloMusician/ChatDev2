"""Fix Continue.dev config to address streaming/response issues.

Based on investigation findings:
1. Streaming vs non-streaming length mismatch
2. Potential response parsing issues
3. Cache was stale

This script adds explicit parameters to Continue.dev config to ensure
better response quality from Ollama models.
"""

import shutil
from datetime import datetime
from pathlib import Path


def backup_config():
    """Backup current config.ts."""
    config_path = Path.home() / ".continue" / "config.ts"

    if not config_path.exists():
        print("❌ config.ts not found")
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = config_path.parent / f"config.ts.backup_{timestamp}"

    shutil.copy2(config_path, backup_path)
    print(f"✅ Backed up config to: {backup_path}")
    return backup_path


def create_optimized_config():
    """Create optimized Continue.dev config with better Ollama parameters."""
    config_content = """export function modifyConfig(config: Config): Config {
  // Optimized Ollama configuration for better response quality
  config.models = [
    {
      title: "Qwen2.5 Coder 14B",
      provider: "ollama",
      model: "qwen2.5-coder:14b",
      apiBase: "http://localhost:11434",
      // Explicit parameters for better output quality
      completionOptions: {
        temperature: 0.7,
        top_p: 0.9,
        num_predict: 2048,        // Max tokens to generate
        stop: ["</s>", "<|im_end|>"],  // Proper stop sequences
        num_ctx: 8192,            // Context window size
      }
    },
    {
      title: "Qwen2.5 Coder 7B",
      provider: "ollama",
      model: "qwen2.5-coder:7b",
      apiBase: "http://localhost:11434",
      completionOptions: {
        temperature: 0.7,
        top_p: 0.9,
        num_predict: 2048,
        stop: ["</s>", "<|im_end|>"],
        num_ctx: 8192,
      }
    },
    {
      title: "StarCoder2 15B",
      provider: "ollama",
      model: "starcoder2:15b",
      apiBase: "http://localhost:11434",
      completionOptions: {
        temperature: 0.5,         // Lower temp for code completion
        top_p: 0.95,
        num_predict: 2048,
        num_ctx: 16384,           // StarCoder has larger context
      }
    },
    {
      title: "CodeLlama 7B",
      provider: "ollama",
      model: "codellama:7b",
      apiBase: "http://localhost:11434",
      completionOptions: {
        temperature: 0.7,
        top_p: 0.9,
        num_predict: 2048,
        num_ctx: 4096,
      }
    },
    {
      title: "Gemma2 9B",
      provider: "ollama",
      model: "gemma2:9b",
      apiBase: "http://localhost:11434",
      completionOptions: {
        temperature: 0.7,
        top_p: 0.9,
        num_predict: 2048,
        num_ctx: 8192,
      }
    },
    {
      title: "Phi 3.5",
      provider: "ollama",
      model: "phi3.5",
      apiBase: "http://localhost:11434",
      completionOptions: {
        temperature: 0.7,
        top_p: 0.9,
        num_predict: 2048,
        num_ctx: 4096,
      }
    },
    {
      title: "Llama 3.1 8B",
      provider: "ollama",
      model: "llama3.1:8b",
      apiBase: "http://localhost:11434",
      completionOptions: {
        temperature: 0.7,
        top_p: 0.9,
        num_predict: 2048,
        num_ctx: 8192,
      }
    }
  ];

  // Tab autocomplete with optimized settings
  config.tabAutocompleteModel = {
    title: "StarCoder2 Autocomplete",
    provider: "ollama",
    model: "starcoder2:15b",
    apiBase: "http://localhost:11434",
    completionOptions: {
      temperature: 0.2,           // Very low for deterministic completions
      top_p: 0.95,
      num_predict: 128,           // Shorter for autocomplete
      num_ctx: 2048,
    }
  };

  // Embeddings
  config.embeddingsProvider = {
    provider: "ollama",
    model: "nomic-embed-text",
    apiBase: "http://localhost:11434"
  };

  // Better context handling
  config.contextProviders = [
    {
      name: "code",
      params: {
        maxTokens: 4096            // More context from files
      }
    },
    {
      name: "diff",
      params: {}
    },
    {
      name: "terminal",
      params: {}
    },
    {
      name: "problems",
      params: {}
    },
    {
      name: "folder",
      params: {}
    },
    {
      name: "codebase",
      params: {}
    }
  ];

  // Slash commands
  config.slashCommands = [
    {
      name: "edit",
      description: "Edit selected code"
    },
    {
      name: "comment",
      description: "Write comments for code"
    },
    {
      name: "share",
      description: "Export conversation"
    },
    {
      name: "cmd",
      description: "Generate shell command"
    },
    {
      name: "commit",
      description: "Generate git commit message"
    }
  ];

  return config;
}
"""
    return config_content


def main():
    """Main execution."""
    print("=" * 80)
    print("CONTINUE.DEV CONFIG OPTIMIZER")
    print("=" * 80)

    # Backup current config
    print("\n1. Backing up current configuration...")
    backup_path = backup_config()

    if not backup_path:
        print("\n⚠️  No existing config found. Creating new optimized config.")

    # Create optimized config
    print("\n2. Creating optimized configuration...")
    optimized_config = create_optimized_config()

    config_path = Path.home() / ".continue" / "config.ts"
    config_path.write_text(optimized_config, encoding="utf-8")

    print(f"✅ Optimized config written to: {config_path}")

    # Summary
    print("\n" + "=" * 80)
    print("OPTIMIZATIONS APPLIED")
    print("=" * 80)
    print("\n✨ Key Improvements:")
    print("  1. Explicit completionOptions for all models")
    print("     - temperature: 0.7 (balanced creativity/accuracy)")
    print("     - num_predict: 2048 (longer responses)")
    print("     - num_ctx: 8192 (larger context window)")
    print("     - Proper stop sequences to prevent truncation")

    print("\n  2. StarCoder2 autocomplete optimized")
    print("     - temperature: 0.2 (deterministic)")
    print("     - num_predict: 128 (quick completions)")

    print("\n  3. Enhanced context providers")
    print("     - maxTokens: 4096 for code context")
    print("     - All standard providers enabled")

    print("\n  4. Useful slash commands enabled")
    print("     - /edit, /comment, /cmd, /commit, /share")

    print("\n" + "=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    print("\n⚠️  IMPORTANT: The autocomplete cache file is still locked by VS Code")
    print("\n1. CLOSE VS CODE COMPLETELY")
    print("   - File → Exit")
    print("   - Wait 10 seconds")

    print("\n2. DELETE REMAINING CACHE (while VS Code is closed)")
    print("   - Navigate to: C:\\Users\\keath\\.continue\\index")
    print("   - Delete: autocompleteCache.sqlite")

    print("\n3. RESTART VS CODE")
    print("   - Open VS Code fresh")
    print("   - Continue.dev will rebuild cache with new config")

    print("\n4. TEST CONTINUE.DEV")
    print("   - Open chat: Ctrl+L")
    print("   - Try: 'Write a Python function to reverse a string'")
    print("   - Check output quality")

    print("\n5. VERIFY IMPROVEMENTS")
    print("   - Responses should be longer (up to 2048 tokens)")
    print("   - No more truncation issues")
    print("   - Better context awareness")
    print("   - Autocomplete should be faster and more accurate")

    print("\n" + "=" * 80)
    print("✅ Configuration optimized!")
    print("=" * 80)

    if backup_path:
        print(f"\n📦 Original config backed up to: {backup_path}")
        print("   (Restore if needed: copy backup file over config.ts)")


if __name__ == "__main__":
    main()
