"""
economy.py — Colony Economy Engine
SQLite-backed ledger: agent wallets, player credits, research tech tree.
Philosophy: HackHub data-as-currency + Grey Hack banking + Bitburner augments.
"""
from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_PATH = Path(__file__).parent.parent.parent / "state" / "economy.db"

RESEARCH_TREE: Dict[str, Dict[str, Any]] = {
    "parallel_boot": {
        "name": "Parallel Boot",
        "description": "Boot 2 agents simultaneously instead of sequentially.",
        "cost": 150,
        "requires": [],
        "category": "colony",
        "unlocks": "Agents Ada and Gordon start concurrently on session init.",
    },
    "deep_index": {
        "name": "Deep Index",
        "description": "Serena indexes 8192-chunk depth instead of 4096.",
        "cost": 200,
        "requires": [],
        "category": "serena",
        "unlocks": "serena walk depth doubled; `wiki` returns richer results.",
    },
    "faction_embassy": {
        "name": "Faction Embassy",
        "description": "Unlock the Embassy district — neutral faction trade hub.",
        "cost": 300,
        "requires": ["parallel_boot"],
        "category": "factions",
        "unlocks": "New `embassy` command + neutral-faction trade missions.",
    },
    "timed_missions": {
        "name": "Timed Mission Protocol",
        "description": "Activate Hacknet-style countdown missions with bonus rewards.",
        "cost": 250,
        "requires": [],
        "category": "missions",
        "unlocks": "`mission start` gives timed traces; fail = reputation loss.",
    },
    "market_access": {
        "name": "Data Marketplace",
        "description": "HackHub-style data trading between agents.",
        "cost": 400,
        "requires": ["faction_embassy"],
        "category": "economy",
        "unlocks": "`market` command — buy/sell exploit fragments.",
    },
    "memory_expansion": {
        "name": "Memory Palace Expansion",
        "description": "Add lore chamber to Serena's memory: 500 extra relationships.",
        "cost": 180,
        "requires": ["deep_index"],
        "category": "serena",
        "unlocks": "`serena remember` stores 500 more tagged observations.",
    },
    "tis100_challenge": {
        "name": "TIS-100 Challenge Layer",
        "description": "Unlock advanced TIS-100 puzzles (levels 4 & 5).",
        "cost": 350,
        "requires": ["parallel_boot"],
        "category": "tis100",
        "unlocks": "tis100 levels 4 and 5 become accessible.",
    },
    "colony_bank": {
        "name": "Colony Bank Charter",
        "description": "Enable inter-agent transfers and the colony-wide bank.",
        "cost": 120,
        "requires": [],
        "category": "economy",
        "unlocks": "`bank transfer <agent> <amount>` unlocked.",
    },
    "godot_bridge": {
        "name": "Godot Visualization Bridge",
        "description": "Connect colony telemetry to SimulatedVerse Godot renderer.",
        "cost": 500,
        "requires": ["market_access", "memory_expansion"],
        "category": "godot",
        "unlocks": "`godot visualize` streams live colony graph to SimulatedVerse.",
    },
    "emudevz_tests": {
        "name": "EmuDevz Test Culture",
        "description": "Mandate unit tests for every new tool; Serena audits daily.",
        "cost": 220,
        "requires": [],
        "category": "colony",
        "unlocks": "Daily `make test-all` triggered automatically; failures become quests.",
    },
}

AGENT_STARTING_CREDITS = {
    "player": 500,
    "ada": 300,
    "gordon": 250,
    "serena": 400,
    "raven": 280,
    "zod": 260,
    "culture_ship": 600,
    "the_librarian": 320,
}

CREDIT_SYMBOL = "₵"


def _init_db(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS wallets (
            entity     TEXT PRIMARY KEY,
            balance    INTEGER NOT NULL DEFAULT 0,
            created_at REAL    NOT NULL,
            updated_at REAL    NOT NULL
        );
        CREATE TABLE IF NOT EXISTS transactions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            ts          REAL    NOT NULL,
            from_entity TEXT    NOT NULL,
            to_entity   TEXT    NOT NULL,
            amount      INTEGER NOT NULL,
            memo        TEXT    NOT NULL DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS research (
            tech_id     TEXT PRIMARY KEY,
            unlocked_by TEXT    NOT NULL,
            unlocked_at REAL    NOT NULL
        );
    """)
    now = time.time()
    for entity, start in AGENT_STARTING_CREDITS.items():
        conn.execute(
            "INSERT OR IGNORE INTO wallets (entity, balance, created_at, updated_at) VALUES (?,?,?,?)",
            (entity, start, now, now),
        )
    conn.commit()


def _conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(str(DB_PATH), timeout=5)
    c.row_factory = sqlite3.Row
    _init_db(c)
    return c


class EconomyEngine:
    def balance(self, entity: str = "player") -> int:
        with _conn() as c:
            row = c.execute("SELECT balance FROM wallets WHERE entity=?", (entity,)).fetchone()
            if row is None:
                now = time.time()
                c.execute(
                    "INSERT INTO wallets (entity, balance, created_at, updated_at) VALUES (?,?,?,?)",
                    (entity, 0, now, now),
                )
                return 0
            return row["balance"]

    def deposit(self, entity: str, amount: int, memo: str = "deposit") -> Dict[str, Any]:
        if amount <= 0:
            return {"error": "Amount must be positive."}
        with _conn() as c:
            self._ensure_wallet(c, entity)
            c.execute(
                "UPDATE wallets SET balance=balance+?, updated_at=? WHERE entity=?",
                (amount, time.time(), entity),
            )
            c.execute(
                "INSERT INTO transactions (ts, from_entity, to_entity, amount, memo) VALUES (?,?,?,?,?)",
                (time.time(), "COLONY_BANK", entity, amount, memo),
            )
            new_bal = c.execute("SELECT balance FROM wallets WHERE entity=?", (entity,)).fetchone()["balance"]
        return {"ok": True, "entity": entity, "deposited": amount, "balance": new_bal}

    def withdraw(self, entity: str, amount: int, memo: str = "withdraw") -> Dict[str, Any]:
        if amount <= 0:
            return {"error": "Amount must be positive."}
        with _conn() as c:
            self._ensure_wallet(c, entity)
            bal = c.execute("SELECT balance FROM wallets WHERE entity=?", (entity,)).fetchone()["balance"]
            if bal < amount:
                return {"error": f"Insufficient funds. Have {bal}{CREDIT_SYMBOL}, need {amount}{CREDIT_SYMBOL}."}
            c.execute(
                "UPDATE wallets SET balance=balance-?, updated_at=? WHERE entity=?",
                (amount, time.time(), entity),
            )
            c.execute(
                "INSERT INTO transactions (ts, from_entity, to_entity, amount, memo) VALUES (?,?,?,?,?)",
                (time.time(), entity, "COLONY_BANK", amount, memo),
            )
            new_bal = bal - amount
        return {"ok": True, "entity": entity, "withdrawn": amount, "balance": new_bal}

    def transfer(self, from_entity: str, to_entity: str, amount: int, memo: str = "transfer") -> Dict[str, Any]:
        if amount <= 0:
            return {"error": "Amount must be positive."}
        with _conn() as c:
            self._ensure_wallet(c, from_entity)
            self._ensure_wallet(c, to_entity)
            bal = c.execute("SELECT balance FROM wallets WHERE entity=?", (from_entity,)).fetchone()["balance"]
            if bal < amount:
                return {"error": f"Insufficient funds. Have {bal}{CREDIT_SYMBOL}."}
            t = time.time()
            c.execute("UPDATE wallets SET balance=balance-?, updated_at=? WHERE entity=?", (amount, t, from_entity))
            c.execute("UPDATE wallets SET balance=balance+?, updated_at=? WHERE entity=?", (amount, t, to_entity))
            c.execute(
                "INSERT INTO transactions (ts, from_entity, to_entity, amount, memo) VALUES (?,?,?,?,?)",
                (t, from_entity, to_entity, amount, memo),
            )
            from_bal = c.execute("SELECT balance FROM wallets WHERE entity=?", (from_entity,)).fetchone()["balance"]
        return {"ok": True, "from": from_entity, "to": to_entity, "amount": amount, "from_balance": from_bal}

    def leaderboard(self) -> List[Dict[str, Any]]:
        with _conn() as c:
            rows = c.execute("SELECT entity, balance FROM wallets ORDER BY balance DESC LIMIT 10").fetchall()
        return [{"entity": r["entity"], "balance": r["balance"]} for r in rows]

    def history(self, entity: str, limit: int = 10) -> List[Dict[str, Any]]:
        with _conn() as c:
            rows = c.execute(
                "SELECT ts, from_entity, to_entity, amount, memo FROM transactions "
                "WHERE from_entity=? OR to_entity=? ORDER BY ts DESC LIMIT ?",
                (entity, entity, limit),
            ).fetchall()
        return [dict(r) for r in rows]

    def research_unlock(self, tech_id: str, entity: str = "player") -> Dict[str, Any]:
        if tech_id not in RESEARCH_TREE:
            return {"error": f"Unknown tech '{tech_id}'. Use: research list"}
        tech = RESEARCH_TREE[tech_id]
        with _conn() as c:
            if c.execute("SELECT 1 FROM research WHERE tech_id=?", (tech_id,)).fetchone():
                return {"error": f"'{tech['name']}' already researched."}
            for req in tech["requires"]:
                if not c.execute("SELECT 1 FROM research WHERE tech_id=?", (req,)).fetchone():
                    req_name = RESEARCH_TREE[req]["name"]
                    return {"error": f"Requires '{req_name}' first (research unlock {req})."}
            self._ensure_wallet(c, entity)
            bal = c.execute("SELECT balance FROM wallets WHERE entity=?", (entity,)).fetchone()["balance"]
            cost = tech["cost"]
            if bal < cost:
                return {"error": f"Need {cost}{CREDIT_SYMBOL} — you have {bal}{CREDIT_SYMBOL}."}
            t = time.time()
            c.execute("UPDATE wallets SET balance=balance-?, updated_at=? WHERE entity=?", (cost, t, entity))
            c.execute(
                "INSERT INTO research (tech_id, unlocked_by, unlocked_at) VALUES (?,?,?)",
                (tech_id, entity, t),
            )
            c.execute(
                "INSERT INTO transactions (ts, from_entity, to_entity, amount, memo) VALUES (?,?,?,?,?)",
                (t, entity, "RESEARCH_LAB", cost, f"Research: {tech['name']}"),
            )
            new_bal = c.execute("SELECT balance FROM wallets WHERE entity=?", (entity,)).fetchone()["balance"]
        return {"ok": True, "tech": tech, "cost": cost, "balance": new_bal}

    def researched(self) -> List[str]:
        with _conn() as c:
            rows = c.execute("SELECT tech_id FROM research").fetchall()
        return [r["tech_id"] for r in rows]

    def is_unlocked(self, tech_id: str) -> bool:
        with _conn() as c:
            return bool(c.execute("SELECT 1 FROM research WHERE tech_id=?", (tech_id,)).fetchone())

    @staticmethod
    def _ensure_wallet(c: sqlite3.Connection, entity: str) -> None:
        now = time.time()
        c.execute(
            "INSERT OR IGNORE INTO wallets (entity, balance, created_at, updated_at) VALUES (?,?,?,?)",
            (entity, 0, now, now),
        )
