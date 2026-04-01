from smolagents import CodeAgent, OpenAIServerModel
import os
import subprocess

base = os.getenv("OPENAI_BASE_URL", "")
key = os.getenv("OPENAI_API_KEY", "")

if base and key:
    llm = OpenAIServerModel(api_base=base, api_key=key, model_id="local/primary")
else:
    llm = None  # vacuum

def run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)

def receipts(path, content):
    with open(path, "w") as f: f.write(content)

def vacuum_fix_console():
    run("comby 'console.log(:[x])' 'logger.debug(:[x])' -matcher javascript -d . -in-place")
    receipts("ops/receipts/comby_console_to_logger.txt", "applied")

agent = CodeAgent(tools=[run], llm=llm, name="SmolMechanic")

if llm:
    agent.run("Replace all lingering TODO with better stubs and create receipts.")
else:
    vacuum_fix_console()