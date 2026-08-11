import math
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class LambdaState:
    """Two-field cache: exactly equivalent to full history."""

    value: float          # Unclamped deviation from 1.00
    last_update_tick: int

    def compute(self, current_tick: int, k: float) -> float:
        dt = current_tick - self.last_update_tick
        d = self.value - 1.00
        d_decayed = d * math.exp(-k * dt)
        raw = 1.00 + d_decayed
        return max(0.00, min(2.00, raw))

    def apply_observation(self, weight: float, current_tick: int, k: float) -> None:
        dt = current_tick - self.last_update_tick
        d = self.value - 1.00
        d_decayed = d * math.exp(-k * dt)
        self.value = 1.00 + d_decayed + weight
        self.last_update_tick = current_tick


class LeightonEngine:
    """λ reputation engine with lossless two-field cache."""

    def __init__(self, k_forage: float = 0.05, k_signal: float = 0.02):
        self.k_forage = k_forage
        self.k_signal = k_signal
        self._cache: Dict[str, LambdaState] = {}

    def _k_for_domain(self, domain: str) -> float:
        # `food` claims are forage-domain observations in this simulation.
        if domain in ("forage", "food"):
            return self.k_forage
        return self.k_signal

    def get_lambda(self, agent_id: str, current_tick: int, domain: str = "forage") -> float:
        if agent_id not in self._cache:
            return 1.00
        k = self._k_for_domain(domain)
        return self._cache[agent_id].compute(current_tick, k)

    def apply_attestation(self, agent_id: str, weight: float, current_tick: int, domain: str = "forage") -> None:
        if agent_id not in self._cache:
            self._cache[agent_id] = LambdaState(value=1.00, last_update_tick=current_tick)
        k = self._k_for_domain(domain)
        self._cache[agent_id].apply_observation(weight, current_tick, k)

    def verify_cache(self, agent_id: str, ledger: List[Dict], current_tick: int, initial_state: LambdaState) -> tuple:
        cached = self.get_lambda(agent_id, current_tick)
        # Recompute from ledger
        # Start replay from the agent's actual birth state.
        state = LambdaState(value=initial_state.value, last_update_tick=initial_state.last_update_tick)
        last_domain = "forage"
        for event in ledger:
            if event.get("agent_id") != agent_id:
                continue
            if event.get("type") not in ("claim.deposited", "claim.attested"):
                continue
            # This relies on the `domain` being present in the ledger event.
            last_domain = event.get("domain", "forage")
            k = self._k_for_domain(last_domain)
            weight = 0.05 if event.get("type") == "claim.deposited" else (0.1 if event.get("outcome") == "confirmed" else -0.15)
            state.apply_observation(weight, event.get("tick", 0), k)

        final_k = self._k_for_domain(last_domain)
        recomputed = state.compute(current_tick, final_k)
        match = abs(cached - recomputed) < 1e-9
        return match, cached, recomputed