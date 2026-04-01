import os
import subprocess
import argparse
def have_llm():
    return bool(os.getenv("OPENAI_API_BASE"))

def comby(pattern, rewrite, globs):
    cmd = ["comby", pattern, rewrite, "-in-place"] + globs
    subprocess.run(cmd, check=False)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", default="ops/codemods/todo_plan.yaml")
    ap.parse_args()

    if have_llm():
        print("LLM mode: drafting codemods via local server …")
        # TODO: implement; use your preferred SDK pointing at OPENAI_API_BASE
    else:
        print("Vacuum mode: structural codemods (comby/tree-sitter)")
        # Example: remove console logs safely
        comby('console.log(:[x]);', '/* removed log */', ["**/*.ts", "**/*.tsx"])

if __name__ == "__main__":
    main()