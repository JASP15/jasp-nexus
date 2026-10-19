"""Safe local operator commands: no process spawn or Git mutation."""
import argparse
import json
import shutil
import sys
from urllib.error import URLError
from urllib.request import urlopen

from .core import KINDS, load_agents, route
from .store import TaskStore, TRANSITIONS
from .platform_support import current_host


def doctor():
    host, compatible = current_host()
    print(f"host         {host}")
    if not compatible:
        print("CAO local    unsupported on native Windows; use Ubuntu in WSL2")
    for name, binary in {"claude": "claude", "codex": "codex", "kiro": "kiro-cli", "commandcode": "cmdc"}.items():
        print(f"{name:12} {'found' if shutil.which(binary) else 'missing'} ({binary})")
    try:
        with urlopen("http://127.0.0.1:9889/health", timeout=2) as response:
            print(f"cao-server   HTTP {response.status} /health")
    except (URLError, TimeoutError, OSError) as exc:
        print(f"cao-server   offline / unreachable ({type(exc).__name__})")
    print("No agent was launched. Binary discovery does not verify login or quota.")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="nexus")
    parser.add_argument("--db", default=".nexus/state.sqlite3")
    parser.add_argument("--agents", default="config/agents.example.json")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor", help="Read-only checks")
    create = commands.add_parser("create", help="Create a task")
    create.add_argument("--title", required=True)
    create.add_argument("--kind", choices=sorted(KINDS), default="general")
    create.add_argument("--complexity", type=int, choices=[1, 2, 3], default=2)
    create.add_argument("--quality", type=int, choices=[1, 2, 3], default=2)
    commands.add_parser("list")
    for name in ("show", "route", "history"):
        sub = commands.add_parser(name)
        sub.add_argument("id")
    advance = commands.add_parser("advance", help="Record a transition; actor is NOT authenticated")
    advance.add_argument("id")
    advance.add_argument("--to", required=True, choices=sorted(TRANSITIONS))
    advance.add_argument("--actor", required=True)
    advance.add_argument("--note", default="")
    args = parser.parse_args(argv)
    if args.command == "doctor":
        doctor()
        return 0
    try:
        store = TaskStore(args.db)
        if args.command == "create":
            print(store.create(args.title, args.kind, args.complexity, args.quality))
        elif args.command == "list":
            print(json.dumps(store.list(), indent=2, ensure_ascii=False))
        elif args.command == "show":
            print(json.dumps(store.get(args.id), indent=2, ensure_ascii=False))
        elif args.command == "history":
            print(json.dumps(store.history(args.id), indent=2, ensure_ascii=False))
        elif args.command == "route":
            task = store.get(args.id)
            plan = route(task["kind"], task["complexity"], task["quality"], load_agents(args.agents))
            store.assign(args.id, plan.coordinator, plan.worker, plan.reviewer)
            print(json.dumps(vars(plan), indent=2))
            print("SIMULATION ONLY: provider health, quota and login were NOT verified.")
        elif args.command == "advance":
            store.advance(args.id, args.to, args.actor, args.note)
            print(store.get(args.id)["state"])
        return 0
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
