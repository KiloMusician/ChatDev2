"""
services/mod_audit/scanner.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Parse incoming mod data sent by the C# LocalModScanner.

The C# side sends:
  {
    "mod_ids":   ["packageId1", "packageId2", ...],
    "about_xmls": {"packageId": "<xml string>", ...}   (optional)
  }

We normalise the About.xml data and return a list of ModInfo dicts.
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from typing import Any


def _text(el: ET.Element | None, tag: str, default: str = "") -> str:
    if el is None:
        return default
    node = el.find(tag)
    return (node.text or "").strip() if node is not None else default


def _li_list(el: ET.Element | None, tag: str) -> list[str]:
    """Return all <li> texts under <tag> as a normalised list."""
    if el is None:
        return []
    container = el.find(tag)
    if container is None:
        return []
    return [
        li.text.strip().lower()
        for li in container.findall("li")
        if li.text and li.text.strip()
    ]


def parse_about_xml(xml_src: str) -> dict[str, Any]:
    """Parse a single About.xml string → metadata dict."""
    try:
        root = ET.fromstring(xml_src)
    except ET.ParseError:
        return {}

    return {
        "package_id":          _text(root, "packageId").lower(),
        "display_name":        _text(root, "name"),
        "author":              _text(root, "author"),
        "supported_versions":  _li_list(root, "supportedVersions"),
        "load_after":          _li_list(root, "loadAfter"),
        "load_before":         _li_list(root, "loadBefore"),
        "incompatible_with":   _li_list(root, "incompatibleWith"),
        "dependencies":        _li_list(root, "modDependencies"),
        "url":                 _text(root, "url"),
        "description":         _text(root, "description")[:300],
    }


def build_mod_list(mod_ids: list[str],
                   about_xmls: dict[str, str] | None = None) -> list[dict[str, Any]]:
    """
    Merge the ordered mod list with any About.xml metadata supplied.
    Returns a list of ModInfo dicts in load-order position.
    """
    about_xmls = about_xmls or {}
    mods: list[dict[str, Any]] = []

    for pos, raw_id in enumerate(mod_ids):
        pid = raw_id.strip().lower()
        info: dict[str, Any] = {
            "package_id":        pid,
            "display_name":      pid,
            "author":            "",
            "load_position":     pos,
            "supported_versions": [],
            "load_after":        [],
            "load_before":       [],
            "incompatible_with": [],
            "dependencies":      [],
            "url":               "",
            "description":       "",
        }

        xml_src = about_xmls.get(raw_id) or about_xmls.get(pid)
        if xml_src:
            parsed = parse_about_xml(xml_src)
            info.update({k: v for k, v in parsed.items() if v})
            if not info["package_id"]:
                info["package_id"] = pid

        mods.append(info)

    return mods


def detect_duplicates(mod_ids: list[str]) -> list[dict[str, Any]]:
    """Return list of {package_id, positions} for duplicate entries."""
    seen: dict[str, list[int]] = {}
    for i, mid in enumerate(mod_ids):
        key = mid.strip().lower()
        seen.setdefault(key, []).append(i)
    return [
        {"package_id": k, "positions": v}
        for k, v in seen.items()
        if len(v) > 1
    ]
