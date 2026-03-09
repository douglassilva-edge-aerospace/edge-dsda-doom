import json
import random
from pathlib import Path
from time import time

OUT = Path("data/scoreboard.json")
OUT.parent.mkdir(exist_ok=True)

random.seed(42)
now = int(time())

board = {}

for i in range(10_000):
    monsters_total = 28
    secrets_total = 3
    items_total = 32

    monsters_killed = random.randint(0, monsters_total)
    secrets_found = random.randint(0, secrets_total)
    items_picked = random.randint(0, items_total)

    player_name = f"Player_{i:06d}"

    board[player_name] = {
        "received_at_unix": now,
        "player_name": player_name,
        "player_identifier": f"FA{i}",
        "health": random.randint(0, 100),
        "armor": random.randint(0, 200),
        "face_index": random.choice([
            0, 1, 2, 10, 11, 12, 20, 21, 22, 30, 31, 32, 40, 41, 42
        ]),
        "monsters": {
            "killed": monsters_killed,
            "total": monsters_total
        },
        "secrets": {
            "found": secrets_found,
            "total": secrets_total
        },
        "items": {
            "picked_up": items_picked,
            "total": items_total
        },
        "ammo": {
            "current": random.randint(0, 50),
            "max": 50
        },
        "time_taken": {
            "hours": 0,
            "minutes": random.randint(0, 59),
            "seconds": random.randint(0, 59)
        }
    }

with OUT.open("w", encoding="utf-8") as f:
    json.dump(board, f)

print(f"Wrote {len(board)} fake players to {OUT}")