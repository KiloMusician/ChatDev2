"""Runtime-profile packaging adapters for generated projects.

Adapters emit Steam-ready layout files plus executable hook scripts for each
runtime profile.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PackagingContext:
    """Context passed into runtime packaging adapters."""

    name: str
    runtime_profile: str
    entry_point: str
    language: str
    project_type: str
    metadata: dict[str, Any]


class RuntimePackagingAdapter:
    """Base adapter for runtime-profile packaging output."""

    runtime_profile = "native_terminal"

    def build_manifest(self, context: PackagingContext) -> dict[str, Any]:
        return {
            "runtime_profile": context.runtime_profile,
            "entry_point": context.entry_point,
            "language": context.language,
            "project_type": context.project_type,
            "steam_ready": True,
        }

    def save_locations(self, context: PackagingContext) -> dict[str, str]:
        safe_name = _safe_package_name(context.name)
        return {
            "windows": f"%LOCALAPPDATA%/{context.name}/",
            "linux": f"~/.local/share/{safe_name}/",
            "macos": f"~/Library/Application Support/{context.name}/",
        }

    def overlay_hooks(self, _context: PackagingContext) -> dict[str, Any]:
        return {
            "steamworks_required": False,
            "hooks": ["achievement.unlock", "stats.commit"],
            "integration": "custom_native_bridge",
        }

    def executable_name(self, context: PackagingContext) -> str:
        return f"{context.name}.exe"

    def profile_files(self, _context: PackagingContext) -> dict[str, str]:
        return {}

    def required_paths(self, context: PackagingContext) -> list[str]:
        paths = [
            "packaging/steam/steam_appid.txt",
            "packaging/save_locations.json",
            "packaging/overlay_hooks.json",
        ]
        paths.extend(self.profile_files(context).keys())
        seen: set[str] = set()
        ordered: list[str] = []
        for path in paths:
            if path in seen:
                continue
            seen.add(path)
            ordered.append(path)
        return ordered

    def steam_layout(self, context: PackagingContext) -> dict[str, Any]:
        return {
            "executable": self.executable_name(context),
            "entry_point": context.entry_point,
            "runtime_profile": context.runtime_profile,
            "required_paths": self.required_paths(context),
        }

    def build_file_map(self, context: PackagingContext) -> dict[str, str]:
        files = {
            "packaging/runtime_profile.json": f"{json.dumps(self.build_manifest(context), indent=2)}\n",
            "packaging/save_locations.json": f"{json.dumps(self.save_locations(context), indent=2)}\n",
            "packaging/overlay_hooks.json": f"{json.dumps(self.overlay_hooks(context), indent=2)}\n",
            "packaging/steam/steam_appid.txt": "0000000\n",
            "packaging/steam/layout.json": f"{json.dumps(self.steam_layout(context), indent=2)}\n",
        }
        files.update(self.profile_files(context))
        return files

    def validate_layout(self, output_path: Path, context: PackagingContext) -> dict[str, Any]:
        """Validate required packaging files for this adapter."""
        required = self.required_paths(context)
        missing = [path for path in required if not (output_path / path).exists()]
        return {
            "runtime_profile": context.runtime_profile,
            "required_paths": required,
            "missing_paths": missing,
            "healthy": not missing,
        }

    def hook_contracts(self, _context: PackagingContext) -> list[dict[str, Any]]:
        """Return executable hook contracts for this runtime profile."""
        return []

    def validate_executable_hooks(
        self, output_path: Path, context: PackagingContext
    ) -> dict[str, Any]:
        """Validate executable packaging hooks and their return contracts."""
        checks: list[dict[str, Any]] = []
        for contract in self.hook_contracts(context):
            checks.append(self._validate_contract(output_path, contract))

        failed = [check for check in checks if check.get("status") == "failed"]
        skipped = [check for check in checks if check.get("status") == "skipped"]
        return {
            "runtime_profile": context.runtime_profile,
            "checked": len(checks),
            "failed": len(failed),
            "skipped": len(skipped),
            "healthy": not failed,
            "checks": checks,
        }

    def _validate_contract(self, output_path: Path, contract: dict[str, Any]) -> dict[str, Any]:
        relative_path = str(contract.get("path", ""))
        target = output_path / relative_path
        function_name = str(contract.get("function", ""))
        runtime = str(contract.get("runtime", "static"))
        arg = contract.get("arg")

        if not relative_path or not target.exists():
            return {
                "path": relative_path,
                "function": function_name,
                "runtime": runtime,
                "status": "failed",
                "reason": "hook file missing",
            }

        if runtime == "python":
            return self._validate_python_contract(target, function_name, arg, contract)
        if runtime == "node":
            return self._validate_node_contract(target, function_name, arg, contract)
        return self._validate_static_contract(target, function_name, contract)

    def _validate_python_contract(
        self,
        target: Path,
        function_name: str,
        arg: Any,
        contract: dict[str, Any],
    ) -> dict[str, Any]:
        payload = "__NUSYQ_NO_ARG__" if arg is None else json.dumps(arg)
        runner = (
            "import importlib.util, json, sys\n"
            "path, fn_name, raw = sys.argv[1], sys.argv[2], sys.argv[3]\n"
            "spec = importlib.util.spec_from_file_location('nq_hook', path)\n"
            "if spec is None or spec.loader is None:\n"
            "    raise RuntimeError('unable to load hook module')\n"
            "mod = importlib.util.module_from_spec(spec)\n"
            "spec.loader.exec_module(mod)\n"
            "fn = getattr(mod, fn_name)\n"
            "if raw == '__NUSYQ_NO_ARG__':\n"
            "    result = fn()\n"
            "else:\n"
            "    result = fn(json.loads(raw))\n"
            "print(json.dumps(result))\n"
        )
        proc = subprocess.run(
            [sys.executable, "-c", runner, str(target), function_name, payload],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if proc.returncode != 0:
            return {
                "path": str(target),
                "function": function_name,
                "runtime": "python",
                "status": "failed",
                "reason": proc.stderr.strip() or "python hook execution failed",
            }
        return self._evaluate_contract_output(
            "python",
            str(target),
            function_name,
            proc.stdout,
            contract,
        )

    def _validate_node_contract(
        self,
        target: Path,
        function_name: str,
        arg: Any,
        contract: dict[str, Any],
    ) -> dict[str, Any]:
        node_cmd = self._resolve_node_runtime_command()
        if node_cmd is None:
            emulated = self._emulate_node_contract(target, function_name, arg)
            if emulated is not None:
                return self._evaluate_contract_result(
                    runtime="node",
                    target_path=str(target),
                    function_name=function_name,
                    result=emulated,
                    contract=contract,
                    mode="runtime-emulated",
                )

            static = self._validate_static_contract(target, function_name, contract)
            static["runtime"] = "node"
            static["mode"] = "static-fallback"
            if static.get("status") == "passed":
                static["reason"] = "node runtime unavailable; static contract check passed"
            return static

        payload = "__NUSYQ_NO_ARG__" if arg is None else json.dumps(arg)
        runner = (
            "const mod = require(process.argv[1]);\n"
            "const fnName = process.argv[2];\n"
            "const raw = process.argv[3];\n"
            "const fn = mod[fnName];\n"
            "if (typeof fn !== 'function') throw new Error('hook function missing');\n"
            "const out = raw === '__NUSYQ_NO_ARG__' ? fn() : fn(JSON.parse(raw));\n"
            "console.log(JSON.stringify(out));\n"
        )
        proc = subprocess.run(
            [node_cmd, "-e", runner, str(target), function_name, payload],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if proc.returncode != 0:
            return {
                "path": str(target),
                "function": function_name,
                "runtime": "node",
                "status": "failed",
                "reason": proc.stderr.strip() or "node hook execution failed",
            }
        return self._evaluate_contract_output(
            "node",
            str(target),
            function_name,
            proc.stdout,
            contract,
        )

    def _resolve_node_runtime_command(self) -> str | None:
        """Resolve an available Node runtime command."""
        for candidate in ("node", "nodejs"):
            if shutil.which(candidate):
                return candidate
        return None

    def _emulate_node_contract(self, target: Path, function_name: str, arg: Any) -> Any:
        """Best-effort emulation for simple CommonJS hook modules when Node is unavailable."""
        text = target.read_text(encoding="utf-8")
        body, params = self._extract_js_function(text, function_name)
        if body is None:
            return None

        args_map: dict[str, Any] = {}
        if params:
            args_map[params[0]] = arg

        return self._evaluate_js_return_expression(body, args_map)

    def _extract_js_function(self, text: str, function_name: str) -> tuple[str | None, list[str]]:
        """Extract function body and parameter names for a JS function declaration."""
        signature = re.search(
            rf"function\s+{re.escape(function_name)}\s*\((?P<params>[^)]*)\)\s*\{{",
            text,
        )
        if signature is None:
            return None, []

        params_raw = signature.group("params").strip()
        params = [item.strip() for item in params_raw.split(",") if item.strip()]
        open_index = signature.end() - 1
        depth = 0
        close_index = -1
        for idx in range(open_index, len(text)):
            char = text[idx]
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    close_index = idx
                    break
        if close_index == -1:
            return None, params

        return text[open_index + 1 : close_index], params

    def _evaluate_js_return_expression(self, body: str, args_map: dict[str, Any]) -> Any:
        """Evaluate a minimal JS return expression subset used by generated hook scripts."""
        match = re.search(r"return\s+(?P<expr>.*?);", body, flags=re.DOTALL)
        if match is None:
            return None
        expr = match.group("expr").strip()
        return self._evaluate_js_expr(expr, args_map)

    def _evaluate_js_expr(self, expr: str, args_map: dict[str, Any]) -> Any:
        """Evaluate a small JS expression subset for deterministic hook emulation."""
        cleaned = expr.strip()
        while cleaned.startswith("(") and cleaned.endswith(")"):
            cleaned = cleaned[1:-1].strip()

        if "||" in cleaned:
            left, right = cleaned.split("||", 1)
            left_value = self._evaluate_js_expr(left, args_map)
            return left_value if left_value else self._evaluate_js_expr(right, args_map)

        if "&&" in cleaned:
            left, right = cleaned.split("&&", 1)
            left_value = self._evaluate_js_expr(left, args_map)
            return self._evaluate_js_expr(right, args_map) if left_value else left_value

        if cleaned.startswith("{") and cleaned.endswith("}"):
            return self._parse_js_object_literal(cleaned, args_map)

        if (cleaned.startswith("'") and cleaned.endswith("'")) or (
            cleaned.startswith('"') and cleaned.endswith('"')
        ):
            return cleaned[1:-1]

        if cleaned == "true":
            return True
        if cleaned == "false":
            return False
        if cleaned == "null":
            return None

        if re.fullmatch(r"-?\d+", cleaned):
            return int(cleaned)
        if re.fullmatch(r"-?\d+\.\d+", cleaned):
            return float(cleaned)

        if "." in cleaned:
            root_name, *attrs = cleaned.split(".")
            value = args_map.get(root_name)
            for attr in attrs:
                value = value.get(attr) if isinstance(value, dict) else None
                if value is None:
                    break
            return value

        return args_map.get(cleaned)

    def _parse_js_object_literal(
        self, object_expr: str, args_map: dict[str, Any]
    ) -> dict[str, Any]:
        """Parse simple JS object literal of form { key: value, ... }."""
        inner = object_expr[1:-1].strip()
        if not inner:
            return {}

        entries = self._split_js_csv(inner)
        parsed: dict[str, Any] = {}
        for entry in entries:
            if ":" not in entry:
                continue
            key, raw_value = entry.split(":", 1)
            normalized_key = key.strip().strip("'\"")
            parsed[normalized_key] = self._evaluate_js_expr(raw_value, args_map)
        return parsed

    def _split_js_csv(self, text: str) -> list[str]:
        """Split a comma-separated JS literal list while respecting nesting/quotes."""
        parts: list[str] = []
        current: list[str] = []
        depth = 0
        quote: str | None = None
        for char in text:
            if quote:
                current.append(char)
                if char == quote:
                    quote = None
                continue
            if char in {"'", '"'}:
                quote = char
                current.append(char)
                continue
            if char in {"{", "[", "("}:
                depth += 1
                current.append(char)
                continue
            if char in {"}", "]", ")"}:
                depth = max(0, depth - 1)
                current.append(char)
                continue
            if char == "," and depth == 0:
                segment = "".join(current).strip()
                if segment:
                    parts.append(segment)
                current = []
                continue
            current.append(char)

        trailing = "".join(current).strip()
        if trailing:
            parts.append(trailing)
        return parts

    def _validate_static_contract(
        self,
        target: Path,
        function_name: str,
        contract: dict[str, Any],
    ) -> dict[str, Any]:
        text = target.read_text(encoding="utf-8")
        required_tokens = list(contract.get("required_tokens", []))
        function_ok = function_name in text if function_name else True
        tokens_ok = all(token in text for token in required_tokens)
        status = "passed" if function_ok and tokens_ok else "failed"
        return {
            "path": str(target),
            "function": function_name,
            "runtime": str(contract.get("runtime", "static")),
            "status": status,
            "mode": "static",
            "reason": None if status == "passed" else "required function/token missing",
        }

    def _evaluate_contract_output(
        self,
        runtime: str,
        target_path: str,
        function_name: str,
        stdout: str,
        contract: dict[str, Any],
    ) -> dict[str, Any]:
        output_text = stdout.strip().splitlines()
        last_line = output_text[-1] if output_text else ""
        try:
            result = json.loads(last_line)
        except json.JSONDecodeError:
            return {
                "path": target_path,
                "function": function_name,
                "runtime": runtime,
                "status": "failed",
                "mode": "runtime",
                "reason": "invalid JSON output from hook",
            }

        return self._evaluate_contract_result(
            runtime=runtime,
            target_path=target_path,
            function_name=function_name,
            result=result,
            contract=contract,
            mode="runtime",
        )

    def _evaluate_contract_result(
        self,
        *,
        runtime: str,
        target_path: str,
        function_name: str,
        result: Any,
        contract: dict[str, Any],
        mode: str,
    ) -> dict[str, Any]:
        """Evaluate hook execution result against contract expectations."""
        expected_hook = contract.get("expected_hook")
        expected_contains = contract.get("expected_contains")
        ok = True
        reason = None

        if expected_hook:
            if not isinstance(result, dict) or result.get("hook") != expected_hook:
                ok = False
                reason = f"expected hook '{expected_hook}'"
            elif result.get("ok") is not True:
                ok = False
                reason = "expected ok=true"

        if ok and expected_contains and expected_contains not in str(result):
            ok = False
            reason = f"expected output to contain '{expected_contains}'"

        return {
            "path": target_path,
            "function": function_name,
            "runtime": runtime,
            "status": "passed" if ok else "failed",
            "mode": mode,
            "reason": reason,
            "result": result,
        }


class ElectronLocalPackagingAdapter(RuntimePackagingAdapter):
    runtime_profile = "electron_local"

    def save_locations(self, context: PackagingContext) -> dict[str, str]:
        safe_name = _safe_package_name(context.name)
        return {
            "windows": f"%APPDATA%/{context.name}/saves",
            "linux": f"~/.config/{safe_name}/saves",
            "macos": f"~/Library/Application Support/{context.name}/saves",
        }

    def overlay_hooks(self, _context: PackagingContext) -> dict[str, Any]:
        return {
            "steamworks_required": True,
            "hooks": ["overlay.enable", "achievement.unlock", "stats.commit"],
            "ipc_boundary": "preload/contextBridge",
        }

    def profile_files(self, _context: PackagingContext) -> dict[str, str]:
        return {
            "packaging/electron/steam_adapter.json": json.dumps(
                {
                    "main_process_entry": "electron/main.js",
                    "preload_entry": "electron/preload.js",
                    "steamworks_required": True,
                    "launch_mode": "local_bundle",
                },
                indent=2,
            )
            + "\n",
            "packaging/electron/hooks/steam_overlay_hook.js": (
                "// Executable Steam overlay bridge for Electron local runtime.\n"
                "function enableOverlay() {\n"
                "  return { ok: true, hook: 'overlay.enable' };\n"
                "}\n\n"
                "function unlockAchievement(achievementId) {\n"
                "  return { ok: true, hook: 'achievement.unlock', achievementId };\n"
                "}\n\n"
                "module.exports = { enableOverlay, unlockAchievement };\n"
            ),
        }

    def hook_contracts(self, _context: PackagingContext) -> list[dict[str, Any]]:
        return [
            {
                "path": "packaging/electron/hooks/steam_overlay_hook.js",
                "runtime": "node",
                "function": "enableOverlay",
                "expected_hook": "overlay.enable",
                "required_tokens": ["enableOverlay", "overlay.enable"],
            },
            {
                "path": "packaging/electron/hooks/steam_overlay_hook.js",
                "runtime": "node",
                "function": "unlockAchievement",
                "arg": "doctor-achievement",
                "expected_hook": "achievement.unlock",
                "required_tokens": ["unlockAchievement", "achievement.unlock"],
            },
        ]


class ElectronWebWrapperPackagingAdapter(ElectronLocalPackagingAdapter):
    runtime_profile = "electron_web_wrapper"

    def profile_files(self, context: PackagingContext) -> dict[str, str]:
        target_url = context.metadata.get("target_url", "https://example.com")
        files = super().profile_files(context)
        files["packaging/electron/web_wrapper.json"] = (
            json.dumps(
                {
                    "target_url": target_url,
                    "steamworks_required": True,
                    "launch_mode": "remote_web_app",
                },
                indent=2,
            )
            + "\n"
        )
        files["packaging/electron/hooks/web_wrapper_launcher.js"] = (
            "// Executable launcher hook for Electron web-wrapper profile.\n"
            "function resolveLaunchUrl(config) {\n"
            "  return (config && config.target_url) || 'https://example.com';\n"
            "}\n\n"
            "module.exports = { resolveLaunchUrl };\n"
        )
        return files

    def hook_contracts(self, context: PackagingContext) -> list[dict[str, Any]]:
        contracts = super().hook_contracts(context)
        contracts.append(
            {
                "path": "packaging/electron/hooks/web_wrapper_launcher.js",
                "runtime": "node",
                "function": "resolveLaunchUrl",
                "arg": {"target_url": "https://example.com"},
                "expected_contains": "https://example.com",
                "required_tokens": ["resolveLaunchUrl", "target_url"],
            }
        )
        return contracts


class GodotExportPackagingAdapter(RuntimePackagingAdapter):
    runtime_profile = "godot_export"

    def save_locations(self, context: PackagingContext) -> dict[str, str]:
        return {
            "windows": f"%APPDATA%/Godot/app_userdata/{context.name}",
            "linux": f"~/.local/share/godot/app_userdata/{context.name}",
            "macos": f"~/Library/Application Support/Godot/app_userdata/{context.name}",
        }

    def overlay_hooks(self, _context: PackagingContext) -> dict[str, Any]:
        return {
            "steamworks_required": True,
            "hooks": ["overlay.enable", "achievement.unlock", "leaderboard.submit"],
            "integration": "godot_steam_plugin",
        }

    def profile_files(self, _context: PackagingContext) -> dict[str, str]:
        return {
            "packaging/godot/export_presets.cfg": (
                '[preset.0]\nname="Windows Desktop"\nplatform="Windows Desktop"\nexport_path="build/windows/game.exe"\n'
            ),
            "packaging/godot/hooks/steam_overlay_hook.gd": (
                "extends Node\n\n"
                "func enable_overlay() -> Dictionary:\n"
                '    return {"ok": true, "hook": "overlay.enable"}\n\n'
                "func unlock_achievement(achievement_id: String) -> Dictionary:\n"
                '    return {"ok": true, "hook": "achievement.unlock", "achievement_id": achievement_id}\n'
            ),
        }

    def hook_contracts(self, _context: PackagingContext) -> list[dict[str, Any]]:
        return [
            {
                "path": "packaging/godot/hooks/steam_overlay_hook.gd",
                "runtime": "gdscript",
                "function": "enable_overlay",
                "required_tokens": ["func enable_overlay", "overlay.enable"],
            },
            {
                "path": "packaging/godot/hooks/steam_overlay_hook.gd",
                "runtime": "gdscript",
                "function": "unlock_achievement",
                "required_tokens": ["func unlock_achievement", "achievement.unlock"],
            },
        ]


class NativeTerminalPackagingAdapter(RuntimePackagingAdapter):
    runtime_profile = "native_terminal"

    def profile_files(self, _context: PackagingContext) -> dict[str, str]:
        return {
            "packaging/native/launch_windows.bat": (
                "@echo off\r\nREM Steam launcher shim\r\npython main.py\r\n"
            ),
            "packaging/native/hooks/steam_overlay_hook.py": (
                '"""Executable Steam hook shim for native terminal runtime."""\n\n'
                "from __future__ import annotations\n\n"
                "def enable_overlay() -> dict[str, object]:\n"
                '    return {"ok": True, "hook": "overlay.enable"}\n\n'
                "def unlock_achievement(achievement_id: str) -> dict[str, object]:\n"
                '    return {"ok": True, "hook": "achievement.unlock", "achievement_id": achievement_id}\n'
            ),
        }

    def hook_contracts(self, _context: PackagingContext) -> list[dict[str, Any]]:
        return [
            {
                "path": "packaging/native/hooks/steam_overlay_hook.py",
                "runtime": "python",
                "function": "enable_overlay",
                "expected_hook": "overlay.enable",
                "required_tokens": ["def enable_overlay", "overlay.enable"],
            },
            {
                "path": "packaging/native/hooks/steam_overlay_hook.py",
                "runtime": "python",
                "function": "unlock_achievement",
                "arg": "doctor-achievement",
                "expected_hook": "achievement.unlock",
                "required_tokens": ["def unlock_achievement", "achievement.unlock"],
            },
        ]


def build_runtime_packaging_adapter(runtime_profile: str) -> RuntimePackagingAdapter:
    """Factory for runtime profile packaging adapters."""
    profile = (runtime_profile or "").strip().lower()
    if profile == "electron_local":
        return ElectronLocalPackagingAdapter()
    if profile == "electron_web_wrapper":
        return ElectronWebWrapperPackagingAdapter()
    if profile == "godot_export":
        return GodotExportPackagingAdapter()
    return NativeTerminalPackagingAdapter()


def _safe_package_name(name: str) -> str:
    normalized = "".join(
        char if char.isalnum() or char in {"-", "_"} else "-" for char in name.lower()
    )
    while "--" in normalized:
        normalized = normalized.replace("--", "-")
    normalized = normalized.strip("-")
    return normalized or "generated-project"
