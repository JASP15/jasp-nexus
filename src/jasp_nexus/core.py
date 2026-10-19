"""Deterministic role routing. No provider is launched here."""
from dataclasses import dataclass
import json
from pathlib import Path

KINDS = frozenset({"visual", "backend", "integration", "general"})


@dataclass(frozen=True)
class Agent:
    id: str
    provider: str
    roles: frozenset[str]
    specialties: frozenset[str]
    max_complexity: int
    review_quality: int
    cost_rank: int
    enabled: bool


@dataclass(frozen=True)
class Plan:
    coordinator: str
    worker: str
    reviewer: str


def load_agents(path: str | Path) -> list[Agent]:
    """Load routing preferences, NOT real provider health or quota."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    agents = []
    ids = set()
    for item in data["agents"]:
        aid = str(item["id"])
        if not aid or aid in ids:
            raise ValueError("Agent IDs must be unique and nonempty")
        ids.add(aid)
        agent = Agent(
            id=aid, provider=str(item["provider"]),
            roles=frozenset(item["roles"]),
            specialties=frozenset(item["specialties"]),
            max_complexity=int(item["max_complexity"]),
            review_quality=int(item["review_quality"]),
            cost_rank=int(item["cost_rank"]),
            enabled=bool(item["enabled"]),
        )
        if not 1 <= agent.max_complexity <= 3 or not 1 <= agent.review_quality <= 3:
            raise ValueError(f"Invalid level for agent {aid}")
        if agent.cost_rank < 0:
            raise ValueError(f"Invalid cost rank for agent {aid}")
        agents.append(agent)
    return agents


def route(kind: str, complexity: int, quality: int, agents: list[Agent]) -> Plan:
    """Suggest roles with independent reviewer. Simulation, not execution."""
    if kind not in KINDS or complexity not in (1, 2, 3) or quality not in (1, 2, 3):
        raise ValueError("Invalid task kind, complexity or quality")
    active = [a for a in agents if a.enabled]
    supervisors = [a for a in active if "coordinator" in a.roles and a.id in {"claude", "codex"}]
    if not supervisors:
        raise ValueError("No eligible Claude/Codex coordinator")
    coordinator = min(
        supervisors,
        key=lambda a: (-(kind in a.specialties), -a.max_complexity, a.cost_rank, a.id),
    )
    workers = [
        a for a in active if "worker" in a.roles and a.max_complexity >= complexity
        and (kind in a.specialties or "general" in a.specialties)
    ]
    if not workers:
        raise ValueError("No worker satisfies the task complexity")
    worker = min(
        workers,
        key=lambda a: (a.cost_rank, -(kind in a.specialties), -a.max_complexity, a.id),
    )
    reviewers = [
        a for a in active
        if "reviewer" in a.roles and a.review_quality >= quality and a.id != worker.id
    ]
    if not reviewers:
        raise ValueError("No independent reviewer meets the quality target")
    reviewer = min(
        reviewers,
        key=lambda a: (-(kind in a.specialties), -a.review_quality, a.cost_rank, a.id),
    )
    return Plan(coordinator=coordinator.id, worker=worker.id, reviewer=reviewer.id)
