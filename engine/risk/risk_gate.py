from typing import Tuple, Dict

from engine.signals.models import Signal

class RiskGate:
    def validate(self, signal: Signal, portfolio_state: Dict) -> Tuple[bool, str]:
        # For now: always return (True, "ok")
        # Full implementation comes in Phase 3
        return (True, "ok")
