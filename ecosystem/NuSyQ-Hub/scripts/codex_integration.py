"""OmniTag: {
    "purpose": "file_systematically_tagged",
    "tags": ["Python", "OpenAI"],
    "category": "auto_tagged",
    "evolution_stage": "v1.0"
}
"""

import argparse
import os
import sys

import requests

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or "<YOUR_OPENAI_API_KEY>"
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

MODEL = "gpt-4o"  # Or use 'gpt-3.5-turbo', 'gpt-4', etc.


def call_codex(prompt, language="python", max_tokens=512, temperature=0.2):
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": f"You are an expert {language} developer. Generate code only.",
            },
            {"role": "user", "content": prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    response = requests.post(OPENAI_API_URL, headers=headers, json=data, timeout=30)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def main():
    parser = argparse.ArgumentParser(description="Codex/GPT code generation and refactoring tool.")
    parser.add_argument(
        "--prompt",
        required=True,
        help="Prompt describing the code or refactor you want.",
    )
    parser.add_argument("--language", default="python", help="Programming language (default: python)")
    parser.add_argument("--max_tokens", type=int, default=512)
    parser.add_argument("--temperature", type=float, default=0.2)
    args = parser.parse_args()

    if OPENAI_API_KEY == "<YOUR_OPENAI_API_KEY>":
        print("[ERROR] Please set your OpenAI API key in the OPENAI_API_KEY environment variable or in this script.")
        sys.exit(1)

    print(f"[Codex] Generating {args.language} code for prompt: {args.prompt}\n")
    try:
        result = call_codex(args.prompt, args.language, args.max_tokens, args.temperature)
        print(result)
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
