"""
Terminal Depths — Simulated Stock Market Engine
Fictional companies whose prices fluctuate based on player actions and world events.
"""
from __future__ import annotations

import math
import random
import time
from typing import Any, Dict, List, Optional


COMPANIES = [
    {
        "ticker": "NXCP",
        "name": "NexusCorp Industries",
        "description": "Megacorp behind the CHIMERA project. Defense, data brokerage, AI.",
        "base_price": 847.00,
        "volatility": 0.04,
        "sector": "megacorp",
    },
    {
        "ticker": "CHIM",
        "name": "Chimera Systems Ltd",
        "description": "AI infrastructure spin-off. Supplies compute to all factions.",
        "base_price": 312.50,
        "volatility": 0.06,
        "sector": "ai",
    },
    {
        "ticker": "SHDC",
        "name": "Shadow Council Holdings",
        "description": "Opaque investment arm of the underground. Untraceable assets.",
        "base_price": 199.99,
        "volatility": 0.09,
        "sector": "underground",
    },
    {
        "ticker": "RESI",
        "name": "Resistance Free Networks",
        "description": "Encrypted comms and anonymization services for dissidents.",
        "base_price": 55.00,
        "volatility": 0.12,
        "sector": "resistance",
    },
    {
        "ticker": "GHST",
        "name": "Ghost Protocol Technologies",
        "description": "Stealth security startup. Popular with black-hat contractors.",
        "base_price": 88.50,
        "volatility": 0.10,
        "sector": "security",
    },
    {
        "ticker": "ORCL",
        "name": "Oracle Data Ventures",
        "description": "Intelligence brokerage. Sells forecasts to the highest bidder.",
        "base_price": 420.00,
        "volatility": 0.05,
        "sector": "intelligence",
    },
    {
        "ticker": "WRTH",
        "name": "Watcher's Circle Research",
        "description": "Mysterious tech firm. Board members are anonymous.",
        "base_price": 1337.00,
        "volatility": 0.03,
        "sector": "mystery",
    },
    {
        "ticker": "ANON",
        "name": "Anon Industries",
        "description": "Manufactures zero-day exploits and sells them on dark markets.",
        "base_price": 147.25,
        "volatility": 0.15,
        "sector": "underground",
    },
]

COMPANY_MAP = {c["ticker"]: c for c in COMPANIES}

WORLD_EVENTS = [
    {"msg": "NexusCorp quarterly earnings beat expectations.", "affects": {"NXCP": 0.08, "CHIM": 0.03}},
    {"msg": "CHIMERA project delayed by regulatory probe.", "affects": {"NXCP": -0.12, "CHIM": -0.08}},
    {"msg": "Shadow Council shell company exposed in leak.", "affects": {"SHDC": -0.20, "GHST": 0.05}},
    {"msg": "Resistance network survives takedown attempt.", "affects": {"RESI": 0.15, "NXCP": -0.05}},
    {"msg": "Zero-day vulnerability sold for record price.", "affects": {"ANON": 0.25, "GHST": 0.10}},
    {"msg": "Oracle Data Ventures sued for data misuse.", "affects": {"ORCL": -0.18, "RESI": 0.08}},
    {"msg": "Anonymous hacker group disrupts NexusCorp grid.", "affects": {"NXCP": -0.07, "GHST": 0.12}},
    {"msg": "Watcher's Circle releases cryptic white-paper.", "affects": {"WRTH": 0.05}},
    {"msg": "Global net neutrality legislation passes.", "affects": {"RESI": 0.10, "NXCP": -0.04}},
    {"msg": "AI regulation hearing in senate freezes contracts.", "affects": {"CHIM": -0.15, "ORCL": -0.08}},
]

HACK_EFFECTS = {
    "nexuscorp_hack": {"NXCP": -0.15, "RESI": 0.05, "GHST": 0.08},
    "chimera_exploit": {"CHIM": -0.20, "ANON": 0.12},
    "shadow_council_contact": {"SHDC": 0.10},
    "data_exfil": {"ORCL": -0.05, "ANON": 0.15},
    "root_shell": {"GHST": 0.20, "NXCP": -0.05},
}


class StockMarket:
    """Simulated stock market for a player session."""

    def __init__(self):
        self._prices: Dict[str, float] = {c["ticker"]: c["base_price"] for c in COMPANIES}
        self._history: Dict[str, List[float]] = {c["ticker"]: [c["base_price"]] for c in COMPANIES}
        self._holdings: Dict[str, int] = {}
        self._cash: float = 10000.0
        self._last_tick: float = time.time()
        self._tick_count: int = 0
        self._events_log: List[str] = []
        self._pending_event: Optional[Dict] = None

    def tick(self, n: int = 1) -> List[str]:
        """Advance market by n ticks, applying random drift."""
        events_fired = []
        for _ in range(n):
            self._tick_count += 1
            for ticker, company in COMPANY_MAP.items():
                vol = company["volatility"]
                drift = random.gauss(0, vol)
                price = self._prices[ticker]
                new_price = max(1.0, round(price * (1 + drift), 2))
                self._prices[ticker] = new_price
                self._history[ticker].append(new_price)
                if len(self._history[ticker]) > 20:
                    self._history[ticker] = self._history[ticker][-20:]

            if self._tick_count % 5 == 0 and random.random() < 0.4:
                event = random.choice(WORLD_EVENTS)
                self._apply_event(event)
                events_fired.append(event["msg"])
                self._events_log.append(event["msg"])
                if len(self._events_log) > 10:
                    self._events_log = self._events_log[-10:]

        self._last_tick = time.time()
        return events_fired

    def _apply_event(self, event: Dict):
        for ticker, pct in event.get("affects", {}).items():
            if ticker in self._prices:
                self._prices[ticker] = max(1.0, round(self._prices[ticker] * (1 + pct), 2))

    def apply_hack_effect(self, hack_type: str) -> List[str]:
        """Called when player performs a notable hack action."""
        effects = HACK_EFFECTS.get(hack_type, {})
        msgs = []
        for ticker, pct in effects.items():
            if ticker in self._prices:
                old = self._prices[ticker]
                self._prices[ticker] = max(1.0, round(old * (1 + pct), 2))
                direction = "▲" if pct > 0 else "▼"
                msgs.append(f"  [MARKET] {ticker} {direction} {abs(pct*100):.0f}%  {old:.2f} → {self._prices[ticker]:.2f}")
        return msgs

    def reset(self, bonus_cash: float = 0.0):
        """Fully reset market to starting state (called on prestige ascension)."""
        self._prices = {c["ticker"]: c["base_price"] for c in COMPANIES}
        self._history = {c["ticker"]: [c["base_price"]] for c in COMPANIES}
        self._holdings = {}
        self._cash = 10000.0 + bonus_cash
        self._last_tick = time.time()
        self._tick_count = 0
        self._events_log = []

    def buy(self, ticker: str, shares: int) -> Dict[str, Any]:
        ticker = ticker.upper()
        if ticker not in self._prices:
            return {"error": f"Unknown ticker: {ticker}"}
        price = self._prices[ticker]
        cost = round(price * shares, 2)
        if cost > self._cash:
            return {"error": f"Insufficient funds. Need ${cost:.2f}, have ${self._cash:.2f}"}
        self._cash = round(self._cash - cost, 2)
        self._holdings[ticker] = self._holdings.get(ticker, 0) + shares
        return {
            "ok": True,
            "ticker": ticker,
            "shares": shares,
            "price": price,
            "cost": cost,
            "cash_remaining": self._cash,
        }

    def sell(self, ticker: str, shares: int) -> Dict[str, Any]:
        ticker = ticker.upper()
        if ticker not in self._prices:
            return {"error": f"Unknown ticker: {ticker}"}
        held = self._holdings.get(ticker, 0)
        if shares > held:
            return {"error": f"You only hold {held} shares of {ticker}"}
        price = self._prices[ticker]
        proceeds = round(price * shares, 2)
        self._cash = round(self._cash + proceeds, 2)
        self._holdings[ticker] -= shares
        if self._holdings[ticker] == 0:
            del self._holdings[ticker]
        return {
            "ok": True,
            "ticker": ticker,
            "shares": shares,
            "price": price,
            "proceeds": proceeds,
            "cash_remaining": self._cash,
        }

    def portfolio_value(self) -> float:
        total = self._cash
        for ticker, shares in self._holdings.items():
            total += self._prices.get(ticker, 0) * shares
        return round(total, 2)

    def get_quote(self, ticker: str) -> Optional[Dict]:
        ticker = ticker.upper()
        if ticker not in COMPANY_MAP:
            return None
        company = COMPANY_MAP[ticker]
        price = self._prices[ticker]
        history = self._history[ticker]
        prev = history[-2] if len(history) >= 2 else price
        change = round(price - prev, 2)
        change_pct = round((change / prev) * 100, 2) if prev else 0
        return {
            "ticker": ticker,
            "name": company["name"],
            "description": company["description"],
            "price": price,
            "change": change,
            "change_pct": change_pct,
            "held": self._holdings.get(ticker, 0),
            "sector": company["sector"],
            "history": history[-10:],
        }

    def price_graph(self, ticker: str, width: int = 20) -> str:
        """ASCII sparkline for a ticker's recent price history."""
        ticker = ticker.upper()
        history = self._history.get(ticker, [])
        if len(history) < 2:
            return "──────"
        window = history[-width:]
        lo = min(window)
        hi = max(window)
        if hi == lo:
            return "─" * len(window)
        blocks = "▁▂▃▄▅▆▇█"
        graph = ""
        for p in window:
            idx = int((p - lo) / (hi - lo) * (len(blocks) - 1))
            graph += blocks[idx]
        return graph

    def to_dict(self) -> dict:
        return {
            "prices": dict(self._prices),
            "history": {k: list(v) for k, v in self._history.items()},
            "holdings": dict(self._holdings),
            "cash": self._cash,
            "last_tick": self._last_tick,
            "tick_count": self._tick_count,
            "events_log": list(self._events_log),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "StockMarket":
        market = cls()
        market._prices = d.get("prices", {c["ticker"]: c["base_price"] for c in COMPANIES})
        market._history = {k: list(v) for k, v in d.get("history", {}).items()}
        for ticker, company in COMPANY_MAP.items():
            if ticker not in market._history:
                market._history[ticker] = [market._prices.get(ticker, company["base_price"])]
        market._holdings = d.get("holdings", {})
        market._cash = d.get("cash", 10000.0)
        market._last_tick = d.get("last_tick", time.time())
        market._tick_count = d.get("tick_count", 0)
        market._events_log = d.get("events_log", [])
        return market
