"""Per-session USD budget guard.

Tracks token usage from each model call and aborts the session when the
configured cap is reached. Toggle via BUDGET_ENFORCED in .env.

Wired into Hermes via the trajectory hook — every model response carries
usage; this module sums it, prices it, and trips a stop flag.
"""

from __future__ import annotations

import json
import os
import threading
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

# Conservative defaults. Override per-model in PRICES below if needed.
# Prices are USD per 1M tokens.
PRICES: dict[str, dict[str, Decimal]] = {
    "openrouter/z-ai/glm-4.5-air":   {"input": Decimal("0.10"), "output": Decimal("0.30")},
    "openrouter/moonshotai/kimi-k2": {"input": Decimal("0.15"), "output": Decimal("2.00")},
    "openrouter/minimax/minimax-m2": {"input": Decimal("0.20"), "output": Decimal("1.00")},
}
DEFAULT_PRICE = {"input": Decimal("1.00"), "output": Decimal("3.00")}

MIN_CAP = Decimal("0.10")
MAX_CAP = Decimal("5.00")


@dataclass
class BudgetState:
    cap_usd: Decimal
    enforced: bool
    spent_usd: Decimal = Decimal("0")
    input_tokens: int = 0
    output_tokens: int = 0
    tripped: bool = False
    lock: threading.Lock = field(default_factory=threading.Lock)

    def add(self, model: str, input_tokens: int, output_tokens: int) -> bool:
        """Record usage. Returns True if the session should continue."""
        price = PRICES.get(model, DEFAULT_PRICE)
        delta = (
            (Decimal(input_tokens) / Decimal(1_000_000)) * price["input"]
            + (Decimal(output_tokens) / Decimal(1_000_000)) * price["output"]
        )
        with self.lock:
            self.input_tokens += input_tokens
            self.output_tokens += output_tokens
            self.spent_usd += delta
            if self.enforced and self.spent_usd >= self.cap_usd:
                self.tripped = True
            return not self.tripped

    def summary(self) -> dict:
        with self.lock:
            return {
                "cap_usd": str(self.cap_usd),
                "spent_usd": f"{self.spent_usd:.4f}",
                "input_tokens": self.input_tokens,
                "output_tokens": self.output_tokens,
                "enforced": self.enforced,
                "tripped": self.tripped,
            }


def load_from_env() -> BudgetState:
    cap = Decimal(os.environ.get("BUDGET_USD_PER_SESSION", "1.00"))
    if cap < MIN_CAP or cap > MAX_CAP:
        raise ValueError(
            f"BUDGET_USD_PER_SESSION must be between {MIN_CAP} and {MAX_CAP}, got {cap}"
        )
    enforced = os.environ.get("BUDGET_ENFORCED", "true").lower() in ("1", "true", "yes")
    return BudgetState(cap_usd=cap, enforced=enforced)


def write_summary(state: BudgetState, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state.summary(), indent=2) + "\n")
