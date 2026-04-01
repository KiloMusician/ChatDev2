#!/usr/bin/env python
"""Fix file encoding issues in the codebase."""

import argparse
import os
import subprocess
import sys
from pathlib import Path

import chardet


def fix_file_encoding(filepath: str) -> bool:
    """Fix encoding issues in a single file."""
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return False

    print(f"🔧 Fixing {filepath}...")
    raw_data = Path(filepath).read_bytes()

    detection = chardet.detect(raw_data)
    detected_encoding = detection["encoding"]
    confidence = detection["confidence"]

    print(f"   Detected: {detected_encoding} (confidence: {confidence:.2f})")

    try:
        if detected_encoding and confidence > 0.7:
            content = raw_data.decode(detected_encoding)
        else:
            for encoding in ["utf-8", "latin-1", "cp1252"]:
                try:
                    content = raw_data.decode(encoding)
                    detected_encoding = encoding
                    break
                except UnicodeDecodeError:
                    continue
            else:
                print("   ❌ Could not decode file")
                return False
    except Exception as e:
        print(f"   ❌ Decode error: {e}")
        return False

    original_content = content

    if content.startswith("\ufeff"):
        content = content[1:]
        print("   Removed UTF-8 BOM")

    content = content.replace("\r\n", "\n").replace("\r", "\n")

    lines = content.split("\n")
    fixed_lines = []
    for i, line in enumerate(lines, 1):
        if "\t" in line:
            fixed_line = line.replace("\t", "    ")
            if fixed_line != line:
                print(f"   Fixed tabs in line {i}")
            fixed_lines.append(fixed_line)
        else:
            fixed_lines.append(line)

    content = "\n".join(fixed_lines)

    lines = content.split("\n")
    fixed_lines = []
    for i, line in enumerate(lines, 1):
        stripped = line.rstrip()
        if stripped != line:
            print(f"   Removed trailing whitespace in line {i}")
        fixed_lines.append(stripped)

    content = "\n".join(fixed_lines)

    if content and not content.endswith("\n"):
        content += "\n"
        print("   Added missing newline at EOF")

    if content == original_content:
        print("   ✅ No changes needed")
        return True

    try:
        Path(filepath).write_text(content, encoding="utf-8")
        print("   ✅ Fixed and saved as UTF-8")
        return True
    except Exception as e:
        print(f"   ❌ Write error: {e}")
        return False


def check_python_syntax(filepath: str) -> bool:
    """Check if a Python file has syntax errors."""
    try:
        content = Path(filepath).read_text(encoding="utf-8")
        compile(content, filepath, "exec")
        print("   ✅ Syntax OK")
        return True
    except SyntaxError as e:
        print(f"   ❌ Syntax error: {e}")
        lines = content.split("\n")
        if e.lineno:
            start = max(0, e.lineno - 3)
            end = min(len(lines), e.lineno + 2)
            print(f"   Context (lines {start + 1}-{end}):")
            for i in range(start, end):
                marker = ">>>" if i == e.lineno - 1 else "   "
                print(f"   {i + 1:3}{marker} {lines[i]}")
        return False
    except Exception as e:
        print(f"   ⚠️  Check error: {e}")
        return False


def scan_for_encoding_issues(directory: str = ".") -> list[str]:
    """Scan directory for files with encoding issues."""
    issues = []
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ["__pycache__", "node_modules", "venv"]]
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                print(f"\n📄 {filepath}")
                encoding_ok = check_file_encoding(filepath)
                syntax_ok = check_python_syntax(filepath)
                if not encoding_ok or not syntax_ok:
                    issues.append(filepath)
    return issues


def check_file_encoding(filepath: str) -> bool:
    """Check a file's encoding."""
    try:
        raw_data = Path(filepath).read_bytes()
        try:
            raw_data.decode("utf-8")
            return True
        except UnicodeDecodeError:
            pass
        detection = chardet.detect(raw_data)
        if detection["encoding"] and detection["confidence"] > 0.7:
            print(f"   ⚠️  Non-UTF-8 encoding: {detection['encoding']}")
            return False
        else:
            print(f"   ⚠️  Unknown encoding (confidence: {detection['confidence']:.2f})")
            return False
    except Exception as e:
        print(f"   ❌ Error checking encoding: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Fix file encoding issues")
    parser.add_argument("files", nargs="*", help="Files to fix (default: all .py files)")
    parser.add_argument("--scan", action="store_true", help="Scan for encoding issues without fixing")
    parser.add_argument("--check-only", action="store_true", help="Check files without fixing")
    parser.add_argument("--fix-all", action="store_true", help="Fix all Python files in the codebase")
    args = parser.parse_args()

    if args.scan:
        print("🔍 Scanning for encoding issues...")
        issues = scan_for_encoding_issues()
        if issues:
            print(f"\n❌ Found {len(issues)} files with issues:")
            for issue in issues:
                print(f"  - {issue}")
            sys.exit(1)
        else:
            print("✅ No encoding issues found")
            sys.exit(0)

    if args.fix_all:
        files = []
        for root, dirs, filenames in os.walk("."):
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            for filename in filenames:
                if filename.endswith(".py"):
                    files.append(os.path.join(root, filename))
    elif args.files:
        files = args.files
    else:
        files = ["scripts/check_file_encoding.py"]

    print(f"🔧 Processing {len(files)} file(s)...")
    fixed_count = 0
    for filepath in files:
        if args.check_only:
            print(f"\n📄 {filepath}")
            check_file_encoding(filepath)
            check_python_syntax(filepath)
        else:
            if fix_file_encoding(filepath):
                fixed_count += 1

    if not args.check_only:
        print(f"\n📊 Fixed {fixed_count}/{len(files)} files")

    if "scripts/check_file_encoding.py" in files or args.fix_all:
        print("\n🧪 Testing check_file_encoding.py...")
        test_result = subprocess.run(
            [sys.executable, "scripts/check_file_encoding.py", "scripts/check_file_encoding.py"],
            capture_output=True,
            text=True,
        )
        if test_result.returncode == 0:
            print("✅ check_file_encoding.py works correctly")
        else:
            print(f"❌ check_file_encoding.py failed: {test_result.stderr}")


if __name__ == "__main__":
    main()
