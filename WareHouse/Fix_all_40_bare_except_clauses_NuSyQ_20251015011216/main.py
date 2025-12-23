import os
import re
import logging
# Set up logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
def fix_bare_except(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    # Regular expression to find bare except clauses
    pattern = r'except:\s*'
    if not re.search(pattern, content):
        logging.info(f"No bare except clauses found in {file_path}")
        return
    # Replace bare except with specific exception types
    new_content = re.sub(pattern, 'except requests.RequestException as e:', content)
    # Add timeout parameters where needed (example for requests library)
    new_content = re.sub(r'requests.get\((.*?)\)', r'requests.get(\1, timeout=5)', new_content)
    new_content = re.sub(r'requests.post\((.*?)\)', r'requests.post(\1, timeout=5)', new_content)
    # Add logging
    new_content = re.sub(r'except requests.RequestException as e:', 'except requests.RequestException as e:\n    logging.error(f"Error: {e}")', new_content)
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(new_content)
    logging.info(f"Bare except clauses fixed in {file_path}")
def process_directory(directory):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                fix_bare_except(file_path)
if __name__ == "__main__":
    codebase_path = r'c:\Users\keath\Desktop\Legacy\NuSyQ-Hub'
    process_directory(codebase_path)