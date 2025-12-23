#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ChatDev with Ollama Integration
================================

Enhanced ChatDev launcher that uses local Ollama models instead of OpenAI API.
Provides fully local, privacy-preserving AI-powered software development.

Features:
    - Automatic Ollama connection and model validation
    - OpenAI API compatibility layer for Ollama
    - Model selection and fallback handling
    - Performance optimization for local inference
    - Comprehensive error handling and logging

Usage:
    python run_ollama.py --task "Create a calculator app" --name "Calculator"

    # With specific model
    python run_ollama.py --task "..." --name "..." --model qwen2.5-coder:14b

    # With config override
    python run_ollama.py --task "..." --config "Human" --model qwen2.5-coder:7b

Author: NuSyQ Development Team
Version: 1.0.0
"""

import argparse
import os
import sys

# Fix Windows console encoding for Unicode emoji support
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
import sys
import requests
import json
from typing import Optional, List

# Add ChatDev to path
root = os.path.dirname(__file__)
sys.path.append(root)


class OllamaConfig:
    """Ollama configuration and validation"""

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.api_url = f"{base_url}/v1"  # OpenAI-compatible endpoint
        self.available_models: List[str] = []

        # HTTP timeout configuration (seconds). If not set, default to 15s for health checks.
        http_timeout = os.getenv('OLLAMA_HTTP_TIMEOUT_SECONDS')
        try:
            self.http_timeout = int(http_timeout) if http_timeout and http_timeout.isdigit() else 15
        except (ValueError, TypeError):
            self.http_timeout = 15

    def check_connection(self) -> bool:
        """Check if Ollama is running and accessible"""
        try:
            # Use configured HTTP timeout for health checks
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=self.http_timeout
            )
            if response.status_code == 200:
                data = response.json()
                self.available_models = [m['name'] for m in data.get('models', [])]
                return True
            return False
        except requests.RequestException as e:
            print(f"❌ Cannot connect to Ollama at {self.base_url}")
            print(f"   Error: {e}")
            print("\n   Please ensure Ollama is running:")
            print("   - Start Ollama service")
            print("   - Or run: ollama serve")
            return False

    def validate_model(self, model_name: str) -> bool:
        """Check if specified model is available"""
        if model_name in self.available_models:
            return True
        print(f"⚠️  Model '{model_name}' not found in Ollama")
        print(f"   Available models: {', '.join(self.available_models)}")
        print(f"\n   Pull model with: ollama pull {model_name}")
        return False

    def get_recommended_model(self) -> Optional[str]:
        """Get best available coding model"""
        # Priority order: larger qwen2.5-coder > codellama > any coder model
        priority = [
            "qwen2.5-coder:14b",
            "qwen2.5-coder:7b",
            "deepseek-coder-v2:16b",
            "codellama:13b",
            "codellama:7b",
            "starcoder2:15b",
        ]

        for model in priority:
            if model in self.available_models:
                return model

        # Fallback to any available model
        if self.available_models:
            return self.available_models[0]

        return None


def setup_environment(ollama_config: OllamaConfig, model: str):
    """Configure environment variables for ChatDev to use Ollama"""

    # Set OpenAI-compatible configuration
    os.environ['OPENAI_API_KEY'] = 'ollama'  # Dummy key for compatibility
    os.environ['OPENAI_BASE_URL'] = ollama_config.api_url  # This is the key fix
    os.environ['BASE_URL'] = ollama_config.api_url

    # Store selected model for potential use
    os.environ['CHATDEV_MODEL'] = model

    print(f"✅ Environment configured:")
    print(f"   Base URL: {ollama_config.api_url}")
    print(f"   OpenAI Base URL: {ollama_config.api_url}")
    print(f"   Model: {model}")


def run_chatdev(args):
    """Execute ChatDev with provided arguments"""
    from chatdev.chat_chain import ChatChain

    # Import ModelType
    from camel.typing import ModelType

    # Parse ChatDev configuration
    config_path, config_phase_path, config_role_path = get_config(args.config)

    # Create ChatChain instance
    # Note: ChatDev will use environment variables we set above
    chat_chain = ChatChain(
        config_path=config_path,
        config_phase_path=config_phase_path,
        config_role_path=config_role_path,
        task_prompt=args.task,
        project_name=args.name,
        org_name=args.org,
        model_type=ModelType.GPT_3_5_TURBO,  # Ollama will handle translation
        code_path=args.path
    )

    # Execute software development process
    print("\n🚀 Starting ChatDev with Ollama...")
    print(f"   Task: {args.task}")
    print(f"   Project: {args.name}")
    print("-" * 60)

    chat_chain.pre_processing()
    chat_chain.make_recruitment()
    chat_chain.execute_chain()
    chat_chain.post_processing()

    print("-" * 60)
    print(f"✅ Software development complete!")
    print(f"   Output: WareHouse/{args.name}_{args.org}_<timestamp>/")


def get_config(company):
    """Get configuration paths for ChatDev"""
    config_dir = os.path.join(root, "CompanyConfig", company)
    default_config_dir = os.path.join(root, "CompanyConfig", "Default")

    config_files = {}
    for config_file in ['ChatChainConfig.json', 'PhaseConfig.json', 'RoleConfig.json']:
        company_config = os.path.join(config_dir, config_file)
        default_config = os.path.join(default_config_dir, config_file)

        if os.path.exists(company_config):
            config_files[config_file] = company_config
        else:
            config_files[config_file] = default_config

    return (
        config_files['ChatChainConfig.json'],
        config_files['PhaseConfig.json'],
        config_files['RoleConfig.json']
    )


def main():
    parser = argparse.ArgumentParser(
        description='ChatDev with Ollama - Local AI Software Development',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with auto-selected model
  python run_ollama.py --task "Create a todo app" --name "TodoApp"

  # With specific model
  python run_ollama.py --task "Create a game" --name "Game" --model qwen2.5-coder:14b

  # With custom configuration
  python run_ollama.py --task "..." --config "Human" --model qwen2.5-coder:7b

Available Models:
  - qwen2.5-coder:14b (recommended for complex projects)
  - qwen2.5-coder:7b  (fast, good for simple projects)
  - codellama:7b       (code specialist)
  - deepseek-coder-v2:16b (advanced coding)
        """
    )

    parser.add_argument('--task', type=str, required=True,
                        help='Software development task description')
    parser.add_argument('--name', type=str, required=True,
                        help='Project name')
    parser.add_argument('--org', type=str, default='NuSyQ',
                        help='Organization name (default: NuSyQ)')
    parser.add_argument('--config', type=str, default='Default',
                        help='Configuration type (Default, Human, Art, Incremental)')
    parser.add_argument('--path', type=str, default='',
                        help='Source code path for incremental development')
    parser.add_argument('--model', type=str, default=None,
                        help='Specific Ollama model to use')
    parser.add_argument('--ollama-url', type=str, default='http://localhost:11434',
                        help='Ollama server URL (default: http://localhost:11434)')

    args = parser.parse_args()

    print("=" * 60)
    print("🤖 ChatDev with Ollama Integration")
    print("=" * 60)

    # Initialize Ollama configuration
    ollama = OllamaConfig(base_url=args.ollama_url)

    # Check Ollama connection
    print("\n🔍 Checking Ollama connection...")
    if not ollama.check_connection():
        sys.exit(1)

    print(f"✅ Connected to Ollama")
    print(f"   Available models: {len(ollama.available_models)}")

    # Select model
    if args.model:
        selected_model = args.model
        if not ollama.validate_model(selected_model):
            print("\n⚠️  Using specified model anyway (may fail if not available)")
    else:
        selected_model = ollama.get_recommended_model()
        if not selected_model:
            print("❌ No suitable models found in Ollama")
            print("   Please pull a coding model:")
            print("   ollama pull qwen2.5-coder:7b")
            sys.exit(1)
        print(f"🎯 Auto-selected model: {selected_model}")

    # Configure environment
    setup_environment(ollama, selected_model)

    # Run ChatDev
    try:
        run_chatdev(args)
    except KeyboardInterrupt:
        print("\n\n⚠️  Development interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Error during development: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
