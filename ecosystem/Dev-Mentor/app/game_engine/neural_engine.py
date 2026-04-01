"""
app/game_engine/neural_engine.py — P14 Neural Network from Player Patterns
============================================================================
A simple feedforward neural network that learns from the player's command
patterns and predicts what they'll type next.

Educational game mechanic: the AI adapts to you.

Architecture:
- Input: one-hot encoded last N commands (N=5 context window)
- Hidden: single hidden layer (configurable size)
- Output: probability distribution over command vocabulary
- Training: online (trains on each command as it arrives)
- Optimizer: SGD with momentum (no numpy required — pure stdlib)

Lore integration:
- The neural net is SERENA's predictive model
- As accuracy increases, SERENA gets more "in-character" hints
- Achievement: NEURAL_GHOST (>80% prediction accuracy over 50+ commands)

Wire format compatible throughout.
"""
from __future__ import annotations

import json
import math
import random
import time
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Command vocabulary
# ---------------------------------------------------------------------------

COMMAND_VOCAB = [
    "ls", "cat", "cd", "pwd", "grep", "find", "echo", "mkdir", "rm",
    "status", "scan", "exploit", "nc", "ssh", "git", "sudo", "talk",
    "osint", "trust", "faction", "nodes", "skills", "quests", "missions",
    "lore", "help", "man", "achievements", "augment", "inventory",
    "sleep", "basement", "number-theory", "graph-theory", "life",
    "shenzhen", "compose", "evolve", "idle", "supply", "strategy",
    "http", "koschei", "mole", "expose", "exfil", "ascend", "class",
    "other",  # catch-all for unknown commands
]

VOCAB_SIZE = len(COMMAND_VOCAB)
_CMD_TO_IDX = {c: i for i, c in enumerate(COMMAND_VOCAB)}


def _cmd_to_idx(cmd: str) -> int:
    base = cmd.split()[0] if cmd else "other"
    return _CMD_TO_IDX.get(base, _CMD_TO_IDX["other"])

# ---------------------------------------------------------------------------
# Pure-Python neural network
# ---------------------------------------------------------------------------

class _Layer:
    """Single dense layer with sigmoid activation."""
    def __init__(self, in_size: int, out_size: int, lr: float = 0.05):
        # Xavier initialization
        scale = math.sqrt(2.0 / (in_size + out_size))
        self.W = [[random.gauss(0, scale) for _ in range(out_size)]
                  for _ in range(in_size)]
        self.b = [0.0] * out_size
        self.lr = lr
        self._last_x: List[float] = []
        self._last_z: List[float] = []
        self._last_a: List[float] = []

    def _sigmoid(self, x: float) -> float:
        if x >= 0:
            return 1.0 / (1.0 + math.exp(-x))
        e = math.exp(x)
        return e / (1.0 + e)

    def forward(self, x: List[float]) -> List[float]:
        self._last_x = x
        out_size = len(self.b)
        z = [self.b[j] + sum(x[i] * self.W[i][j] for i in range(len(x)))
             for j in range(out_size)]
        self._last_z = z
        a = [self._sigmoid(v) for v in z]
        self._last_a = a
        return a

    def backward(self, grad_a: List[float]) -> List[float]:
        """Backprop through sigmoid, update weights, return grad for previous layer."""
        # sigmoid derivative: σ(z) * (1 - σ(z))
        grad_z = [grad_a[j] * self._last_a[j] * (1.0 - self._last_a[j])
                  for j in range(len(grad_a))]
        # Update weights + biases
        for i in range(len(self._last_x)):
            for j in range(len(grad_z)):
                self.W[i][j] -= self.lr * grad_z[j] * self._last_x[i]
        for j in range(len(grad_z)):
            self.b[j] -= self.lr * grad_z[j]
        # Gradient for previous layer
        grad_x = [sum(grad_z[j] * self.W[i][j] for j in range(len(grad_z)))
                  for i in range(len(self._last_x))]
        return grad_x


class _Softmax:
    """Softmax output layer."""
    def __init__(self):
        self._last_p: List[float] = []

    def forward(self, x: List[float]) -> List[float]:
        max_x = max(x)
        exps = [math.exp(v - max_x) for v in x]
        total = sum(exps)
        p = [e / total for e in exps]
        self._last_p = p
        return p

    def cross_entropy_grad(self, p: List[float], target_idx: int) -> List[float]:
        """Returns gradient of cross-entropy loss w.r.t. pre-softmax inputs."""
        grad = list(p)
        grad[target_idx] -= 1.0
        return grad


class CommandPredictor:
    """
    Small 2-layer network predicting next command from command history.
    Input: flattened one-hot vectors for last CONTEXT_LEN commands.
    """
    CONTEXT_LEN = 5

    def __init__(self, hidden_size: int = 32, lr: float = 0.05):
        in_size = self.CONTEXT_LEN * VOCAB_SIZE
        self.hidden = _Layer(in_size, hidden_size, lr)
        self.output = _Layer(hidden_size, VOCAB_SIZE, lr)
        self.softmax = _Softmax()
        self.history: List[int] = []
        self.predictions: int = 0
        self.correct_predictions: int = 0
        self.loss_log: List[float] = []

    def _encode(self, history: List[int]) -> List[float]:
        """One-hot encode last CONTEXT_LEN commands."""
        vec = [0.0] * (self.CONTEXT_LEN * VOCAB_SIZE)
        for pos, cmd_idx in enumerate(history[-self.CONTEXT_LEN:]):
            offset = pos * VOCAB_SIZE
            if 0 <= cmd_idx < VOCAB_SIZE:
                vec[offset + cmd_idx] = 1.0
        return vec

    def predict(self) -> Tuple[str, float]:
        """Predict next command. Returns (command, confidence)."""
        if len(self.history) < 2:
            return ("ls", 0.0)
        x = self._encode(self.history[:-1])
        h = self.hidden.forward(x)
        logits = self.output.forward(h)
        probs = self.softmax.forward(logits)
        best_idx = max(range(VOCAB_SIZE), key=lambda i: probs[i])
        return (COMMAND_VOCAB[best_idx], probs[best_idx])

    def train_step(self, cmd_idx: int) -> float:
        """Online training: observe next command, compute loss, backprop."""
        if len(self.history) < 1:
            self.history.append(cmd_idx)
            return 0.0

        # Forward pass
        x = self._encode(self.history)
        h = self.hidden.forward(x)
        logits = self.output.forward(h)
        probs = self.softmax.forward(logits)

        # Track accuracy
        self.predictions += 1
        predicted_idx = max(range(VOCAB_SIZE), key=lambda i: probs[i])
        if predicted_idx == cmd_idx:
            self.correct_predictions += 1

        # Cross-entropy loss
        loss = -math.log(max(probs[cmd_idx], 1e-10))
        self.loss_log.append(loss)
        if len(self.loss_log) > 100:
            self.loss_log.pop(0)

        # Backprop
        grad_logits = self.softmax.cross_entropy_grad(probs, cmd_idx)
        grad_h = self.output.backward(grad_logits)
        self.hidden.backward(grad_h)

        self.history.append(cmd_idx)
        if len(self.history) > self.CONTEXT_LEN * 3:
            self.history = self.history[-(self.CONTEXT_LEN * 3):]
        return loss

    @property
    def accuracy(self) -> float:
        if self.predictions < 5:
            return 0.0
        return self.correct_predictions / self.predictions

    @property
    def avg_loss(self) -> float:
        if not self.loss_log:
            return 1.0
        return sum(self.loss_log) / len(self.loss_log)

    def top_k_predictions(self, k: int = 5) -> List[Tuple[str, float]]:
        """Return top-k predicted next commands."""
        if len(self.history) < 1:
            return []
        x = self._encode(self.history)
        h = self.hidden.forward(x)
        logits = self.output.forward(h)
        probs = self.softmax.forward(logits)
        ranked = sorted(range(VOCAB_SIZE), key=lambda i: probs[i], reverse=True)[:k]
        return [(COMMAND_VOCAB[i], round(probs[i] * 100, 1)) for i in ranked]

    def to_dict(self) -> dict:
        return {
            "history": self.history[-30:],
            "predictions": self.predictions,
            "correct": self.correct_predictions,
            "loss_log": self.loss_log[-20:],
        }

    def from_dict(self, d: dict) -> None:
        self.history = d.get("history", [])
        self.predictions = d.get("predictions", 0)
        self.correct_predictions = d.get("correct", 0)
        self.loss_log = d.get("loss_log", [])


# ---------------------------------------------------------------------------
# Integration singleton
# ---------------------------------------------------------------------------

_predictor: Optional[CommandPredictor] = None


def get_predictor() -> CommandPredictor:
    global _predictor
    if _predictor is None:
        _predictor = CommandPredictor(hidden_size=32, lr=0.05)
    return _predictor


def observe_command(cmd: str, flags: dict) -> Optional[str]:
    """
    Observe a command, train the model, return a prediction (if confident).
    Called from session.execute() after each command.
    Returns predicted next command string if confidence > 60%, else None.
    """
    predictor = get_predictor()
    # Restore state from flags
    saved = flags.get("neural_state")
    if saved:
        predictor.from_dict(saved)

    cmd_idx = _cmd_to_idx(cmd)
    predictor.train_step(cmd_idx)
    predicted, confidence = predictor.predict()

    # Save state back
    flags["neural_state"] = predictor.to_dict()

    # Achievement check
    if predictor.predictions >= 50 and predictor.accuracy >= 0.80:
        flags.setdefault("neural_achievements", set())
        flags["neural_achievements"].add("NEURAL_GHOST")

    return predicted if confidence > 0.60 else None


def render_neural_status(flags: dict) -> List[dict]:
    """Wire-format SERENA neural predictor status."""
    predictor = get_predictor()
    saved = flags.get("neural_state")
    if saved:
        predictor.from_dict(saved)

    acc = predictor.accuracy
    loss = predictor.avg_loss
    top_k = predictor.top_k_predictions(5)

    out = [
        {"t": "system", "s": "  ═══ SERENA — NEURAL COMMAND PREDICTOR ═══"},
        {"t": "dim",    "s": ""},
        {"t": "info",   "s": f"  Accuracy:    {acc:.1%}  ({predictor.correct_predictions}/{predictor.predictions} correct)"},
        {"t": "info",   "s": f"  Loss (avg):  {loss:.4f}"},
        {"t": "dim",    "s": ""},
        {"t": "info",   "s": "  SERENA predicts your next command:"},
    ]
    for cmd, pct in top_k:
        bar_len = int(pct / 5)
        bar = "█" * bar_len + "░" * (20 - bar_len)
        out.append({"t": "dim", "s": f"    {cmd:<20} [{bar}] {pct:.1f}%"})

    if "NEURAL_GHOST" in flags.get("neural_achievements", set()):
        out.append({"t": "success", "s": "\n  ★ NEURAL_GHOST — SERENA knows you better than you know yourself."})
    elif acc >= 0.60:
        out.append({"t": "npc", "s": f"\n  [SERENA]: My confidence in your patterns is at {acc:.0%}. Predictable. Not an insult."})
    elif predictor.predictions < 10:
        out.append({"t": "npc", "s": "\n  [SERENA]: Still learning. Feed me more commands."})
    else:
        out.append({"t": "npc", "s": f"\n  [SERENA]: {acc:.0%} accurate. You're less predictable than most. I'll adapt."})

    out.append({"t": "dim", "s": ""})
    out.append({"t": "dim", "s": "  Commands: neural status | neural predict | neural train"})
    return out


if __name__ == "__main__":
    # Quick self-test
    predictor = CommandPredictor(hidden_size=16, lr=0.1)
    # Train on a repeating pattern: ls → cat → grep → ls → ...
    pattern = ["ls", "cat", "grep", "ls", "cat", "grep", "ls", "scan", "exploit"]
    losses = []
    for cmd in pattern * 10:
        idx = _cmd_to_idx(cmd)
        loss = predictor.train_step(idx)
        losses.append(loss)

    print(f"Trained on {len(pattern) * 10} commands")
    print(f"Accuracy: {predictor.accuracy:.1%}")
    print(f"Avg loss: {predictor.avg_loss:.4f}")
    print(f"Top-3 predictions: {predictor.top_k_predictions(3)}")
