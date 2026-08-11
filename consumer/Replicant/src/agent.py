import math
import random
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

from capsule import Capsule
from leighton import LambdaState


@dataclass
class Traits:
    forage_bias: float = 0.50
    deposit_rate: float = 0.50
    scepticism: float = 0.50
    broadcast_cost: float = 0.50


@dataclass
class Intent:
    kind: str
    payload: Dict[str, Any] = field(default_factory=dict)


class Agent:
    def __init__(
        self,
        scp_id: str,
        capsule: Capsule,
        x: float, y: float,
        traits: Optional[Traits],
        lambda_state: LambdaState,
        initial_lambda_state: LambdaState,
        birth_tick: int,
        role: str = "generic"
    ):
        self.scp_id = scp_id
        self.capsule = capsule
        self.x = x
        self.y = y
        self.traits = traits
        self.lambda_state = lambda_state
        self.initial_lambda_state = initial_lambda_state
        self.birth_tick = birth_tick
        self.role = role

        self.energy = 100.0
        self.alive = True
        self.tasks_done = 0
        self.is_rogue = False
        self.can_replicate = True
        self.replication_cooldown = 0
        self.last_find_quality = 0.0
        self.last_find_dir = 0.0

    def sense(self, world) -> Dict[str, Any]:
        return {
            "nearby_pheromones": world.get_nearby_pheromones(self.x, self.y, 10.0),
            "nearby_agents": world.get_nearby_agents(self.scp_id, self.x, self.y, 10.0),
            "nearby_claims": world.get_nearby_claims(self.x, self.y, 10.0),
            "energy": self.energy,
            "lambda": self.lambda_state.compute(world.tick, 0.05),
            "can_replicate": self.can_replicate,
            "tick": world.tick
        }

    def decide(self, percepts: Dict[str, Any]) -> Intent:
        if self.is_rogue or not self.alive:
            return Intent(kind="idle")

        if self.replication_cooldown > 0:
            self.replication_cooldown -= 1
            if self.replication_cooldown == 0:
                self.can_replicate = True

        pheromones = percepts.get("nearby_pheromones", [])
        if pheromones:
            strongest = max(pheromones, key=lambda p: p["strength"])
            angle = math.atan2(strongest["y"] - self.y, strongest["x"] - self.x)
            return Intent(kind="move", payload={"dx": math.cos(angle) * 0.5, "dy": math.sin(angle) * 0.5})

        if self.traits and random.random() < self.traits.forage_bias:
            return Intent(kind="move", payload={"dx": random.uniform(-1.0, 1.0), "dy": random.uniform(-1.0, 1.0)})

        if random.random() < 0.2:
            quality = random.random()
            return Intent(kind="deposit", payload={
                "kind": "food",
                "lens": "OPINION",
                "strength": quality * 0.5
            })

        nearby_claims = percepts.get("nearby_claims", [])
        if self.traits and nearby_claims and random.random() < self.traits.scepticism * 0.2:
            claim = random.choice(nearby_claims)
            resource_present = random.random() < 0.7
            return Intent(kind="attest", payload={
                "claim_id": claim["id"],
                "outcome": "confirmed" if resource_present else "countered"
            })

        if self.can_replicate and self.energy >= 70.0 and percepts["lambda"] >= 1.10:
            return Intent(kind="replicate")

        if self.energy < 25.0:
            return Intent(kind="recharge")

        return Intent(kind="idle")

    def apply_intent(self, intent: Intent, world, tick: int) -> None:
        if not self.alive or self.is_rogue:
            return

        if intent.kind == "move":
            self.x += intent.payload.get("dx", 0)
            self.y += intent.payload.get("dy", 0)
            self.energy -= 0.10
            self.energy = max(0, self.energy)

        elif intent.kind == "deposit":
            world.deposit_claim(
                agent_id=self.scp_id,
                x=self.x, y=self.y,
                kind=intent.payload.get("kind", "food"),
                lens=intent.payload.get("lens", "OPINION"),
                strength=intent.payload.get("strength", 0.5),
                tick=tick
            )
            self.energy -= 0.05
            self.tasks_done += 1

        elif intent.kind == "attest":
            claim_id = intent.payload.get("claim_id")
            outcome = intent.payload.get("outcome")
            if claim_id and outcome:
                world.attest_claim(claim_id, self.scp_id, outcome, tick)
                self.energy -= 0.50
                self.tasks_done += 1

        elif intent.kind == "replicate":
            if self.can_replicate and self.energy >= 70.0:
                cost = 40.0
                self.energy -= cost
                self.can_replicate = False
                self.replication_cooldown = 25
                child_energy = cost - 10.0
                world.spawn_child(
                    parent_scp_id=self.scp_id,
                    x=self.x + random.uniform(-1.0, 1.0),
                    y=self.y + random.uniform(-1.0, 1.0),
                    energy=child_energy,
                    traits=self.mutate_traits(),
                    tick=tick
                )

        elif intent.kind == "recharge":
            self.energy += 0.5
            self.energy = min(100.0, self.energy)

    def mutate_traits(self) -> Optional[Traits]:
        if not self.traits:
            return None
        sigma = 0.05
        return Traits(
            forage_bias=max(0.0, min(1.0, self.traits.forage_bias + random.gauss(0, sigma))),
            deposit_rate=max(0.0, min(1.0, self.traits.deposit_rate + random.gauss(0, sigma))),
            scepticism=max(0.0, min(1.0, self.traits.scepticism + random.gauss(0, sigma))),
            broadcast_cost=max(0.0, min(1.0, self.traits.broadcast_cost + random.gauss(0, sigma)))
        )