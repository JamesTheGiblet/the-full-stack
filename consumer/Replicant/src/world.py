import random
import hashlib
import json
import copy
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

from agent import Agent, Traits, Intent
from leighton import LeightonEngine, LambdaState
from capsule import Capsule


@dataclass
class Pheromone:
    x: float; y: float
    agent_id: str
    kind: str
    lens: str
    strength: float
    tick: int


@dataclass
class Claim:
    id: str
    x: float; y: float
    agent_id: str
    kind: str
    lens: str
    strength: float
    tick: int
    attestations: List[Dict] = field(default_factory=list)


class World:
    def __init__(self, seed: int, config: Dict[str, Any]):
        self.seed = seed
        self.config = config
        random.seed(seed)

        self.tick = 0
        self.agents: Dict[str, Agent] = {}
        self.pheromones: List[Pheromone] = []
        self.claims: Dict[str, Claim] = {}
        self.ledger: List[Dict] = []

        self.leighton = LeightonEngine(
            k_forage=config.get("leighton", {}).get("k_per_day_forage", 0.05),
            k_signal=config.get("leighton", {}).get("k_per_day_signal", 0.02)
        )
        self._next_claim_id = 0

    def add_agent(self, agent: Agent) -> None:
        self.agents[agent.scp_id] = agent
        self.leighton._cache[agent.scp_id] = agent.lambda_state
        self._log_event({
            "type": "agent.born",
            "agent_id": agent.scp_id,
            "role": agent.role,
            "tick": self.tick,
            "energy": agent.energy,
            "x": agent.x, "y": agent.y
        })

    def get_nearby_pheromones(self, x: float, y: float, radius: float) -> List[Dict]:
        result = []
        for p in self.pheromones:
            if ((p.x - x)**2 + (p.y - y)**2)**0.5 < radius and p.strength > 0.01:
                result.append({"x": p.x, "y": p.y, "strength": p.strength, "kind": p.kind, "lens": p.lens})
        return result

    def get_nearby_agents(self, self_id: str, x: float, y: float, radius: float) -> List[Dict]:
        result = []
        for aid, agent in self.agents.items():
            if aid != self_id and agent.alive and ((agent.x - x)**2 + (agent.y - y)**2)**0.5 < radius:
                result.append({"id": aid, "x": agent.x, "y": agent.y, "energy": agent.energy, "role": agent.role})
        return result

    def get_nearby_claims(self, x: float, y: float, radius: float) -> List[Dict]:
        result = []
        for cid, claim in self.claims.items():
            if ((claim.x - x)**2 + (claim.y - y)**2)**0.5 < radius:
                result.append({
                    "id": cid, "x": claim.x, "y": claim.y,
                    "lens": claim.lens, "kind": claim.kind,
                    "attestations": len(claim.attestations)
                })
        return result

    def deposit_claim(self, agent_id: str, x: float, y: float, kind: str, lens: str, strength: float, tick: int) -> None:
        claim = Claim(id=f"claim-{self._next_claim_id}", x=x, y=y, agent_id=agent_id, kind=kind, lens=lens, strength=strength, tick=tick)
        self._next_claim_id += 1
        self.claims[claim.id] = claim
        self.pheromones.append(Pheromone(x=x, y=y, agent_id=agent_id, kind=kind, lens=lens, strength=strength, tick=tick))

        self.leighton.apply_attestation(agent_id, 0.05, tick, kind)
        self._log_event({"type": "claim.deposited", "claim_id": claim.id, "agent_id": agent_id, "x": x, "y": y, "kind": kind, "lens": lens, "strength": strength, "tick": tick, "domain": kind})

    def attest_claim(self, claim_id: str, agent_id: str, outcome: str, tick: int) -> None:
        if claim_id not in self.claims:
            return
        claim = self.claims[claim_id]
        claim.attestations.append({"agent_id": agent_id, "outcome": outcome, "tick": tick})

        weight = 0.1 if outcome == "confirmed" else -0.15
        self.leighton.apply_attestation(agent_id, weight, tick, claim.kind)

        required = self.config.get("claims", {}).get(claim.kind, {}).get("commit_attestations", 2)
        if len(claim.attestations) >= required:
            confirmations = [a for a in claim.attestations if a["outcome"] == "confirmed"]
            if len(confirmations) >= required and claim.lens == "OPINION":
                claim.lens = "FACT"
            counters = [a for a in claim.attestations if a["outcome"] == "countered"]
            if len(counters) >= required:
                claim.lens = "COUNTER"

        self._log_event({"type": "claim.attested", "claim_id": claim_id, "agent_id": agent_id, "outcome": outcome, "tick": tick, "domain": claim.kind})

    def spawn_child(self, parent_scp_id: str, x: float, y: float, energy: float, traits: Optional[Traits], tick: int) -> None:
        capsule = Capsule.mint(
            inherits=[parent_scp_id, "replicant/protocol/run-v1"],
            declaration={"parent": parent_scp_id, "traits": traits.__dict__ if traits else None, "birth_tick": tick, "birth_pos": [x, y]},
            licence="MSL-1.0"
        )
        lambda_state = LambdaState(value=1.00, last_update_tick=tick)
        initial_lambda_state = copy.deepcopy(lambda_state)
        agent = Agent(capsule.scp_id, capsule, x, y, traits, lambda_state, initial_lambda_state, tick, "child")
        agent.energy = energy
        self.leighton._cache[agent.scp_id] = lambda_state
        self.add_agent(agent)

    def tick_driver(self) -> None:
        intents = {}
        for aid, agent in self.agents.items():
            if agent.alive and not agent.is_rogue:
                intents[aid] = agent.decide(agent.sense(self))

        for aid in sorted(intents.keys()):
            agent = self.agents.get(aid)
            if agent:
                agent.apply_intent(intents[aid], self, self.tick)

        for aid, agent in self.agents.items():
            if agent.alive:
                lam = agent.lambda_state.compute(self.tick, 0.05)
                if lam < 0.60:
                    agent.is_rogue = True
                    self._log_event({"type": "agent.quarantined", "agent_id": aid, "lambda": lam, "tick": self.tick})

        # Witness
        ledger_hash = self._merkle_root()
        self._log_event({
            "type": "tick.sealed",
            "tick": self.tick,
            "merkle_root": ledger_hash,
            "agent_count": len([a for a in self.agents.values() if a.alive])
        })

        self._decay_pheromones()
        self.tick += 1

    def _merkle_root(self) -> str:
        events = [e for e in self.ledger if e.get("tick") == self.tick]
        if not events:
            return hashlib.sha256(b"empty").hexdigest()
        combined = "".join(json.dumps(e, sort_keys=True) for e in events)
        return hashlib.sha256(combined.encode('utf-8')).hexdigest()

    def _decay_pheromones(self) -> None:
        retention = self.config.get("claims", {}).get("food", {}).get("retention_per_tick", 0.90)
        for p in self.pheromones:
            p.strength *= retention
        self.pheromones = [p for p in self.pheromones if p.strength > 0.01]

    def _log_event(self, event: Dict) -> None:
        if self.ledger:
            event["prev_hash"] = self.ledger[-1].get("hash")
        else:
            event["prev_hash"] = "genesis"
        canonical = json.dumps(event, sort_keys=True, separators=(',',':'))
        event["hash"] = hashlib.sha256(canonical.encode('utf-8')).hexdigest()
        self.ledger.append(event)

    def verify_lambda_cache(self) -> Dict[str, Any]:
        results = {}
        for aid, agent in self.agents.items():
            match, cached, recomputed = self.leighton.verify_cache(aid, self.ledger, self.tick, agent.initial_lambda_state)
            results[aid] = {"match": match, "cached": cached, "recomputed": recomputed, "role": agent.role, "alive": agent.alive}
        return results