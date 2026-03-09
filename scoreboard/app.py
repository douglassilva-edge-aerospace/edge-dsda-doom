from flask import Flask, request, jsonify, render_template
from pathlib import Path
import json
import time

app = Flask(__name__)

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

SCOREBOARD_PATH = DATA_DIR / "scoreboard.json"   # aggregated latest-per-player
HISTORY_PATH = DATA_DIR / "history.jsonl"        # append-only log

from queue import Queue, Empty
subscribers = set()

def compute_score(p: dict) -> float:
    monsters = (p.get("monsters") or {})
    secrets = (p.get("secrets") or {})
    items = (p.get("items") or {})
    face = p.get("face_index", 0) or 0

    monsters_total = monsters.get("total", 0) or 0
    secrets_total = secrets.get("total", 0) or 0
    items_total = items.get("total", 0) or 0

    monsters_ratio = (monsters.get("killed", 0) / monsters_total) if monsters_total else 0
    secrets_ratio = (secrets.get("found", 0) / secrets_total) if secrets_total else 0
    items_ratio = (items.get("picked_up", 0) / items_total) if items_total else 0

    return (
        100 * monsters_ratio +
         50 * secrets_ratio +
         25 * items_ratio +
          0.1 * face
    )

@app.get("/api/stream")
def api_stream():
    def gen():
        q = Queue()
        subscribers.add(q)
        try:
            # initial ping so client knows connection is alive
            yield "event: ping\ndata: {}\n\n"
            while True:
                try:
                    msg = q.get(timeout=30)
                    yield f"event: update\ndata: {json.dumps(msg)}\n\n"
                except Empty:
                    # keep-alive
                    yield "event: ping\ndata: {}\n\n"
        finally:
            subscribers.discard(q)

    return app.response_class(gen(), mimetype="text/event-stream")

def publish_event(event: dict) -> None:
    dead = []
    for q in list(subscribers):
        try:
            q.put_nowait(event)
        except Exception:
            dead.append(q)
    for q in dead:
        subscribers.discard(q)

def atomic_write_json(path: Path, obj) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2), encoding="utf-8")
    tmp.replace(path)


def append_jsonl(path: Path, obj: dict) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, separators=(",", ":")) + "\n")


def load_scoreboard() -> dict:
    if not SCOREBOARD_PATH.exists():
        return {}
    try:
        return json.loads(SCOREBOARD_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


@app.get("/")
def scoreboard():
    return render_template("scoreboard.html")


@app.get("/api/scoreboard")
def api_scoreboard():
    board = load_scoreboard()
    # Convert dict -> list for frontend
    players = list(board.values())

    # Default sort: monsters killed desc, then secrets found desc, then name
    def sort_key(p):
        m = (p.get("monsters") or {}).get("killed", 0)
        s = (p.get("secrets") or {}).get("found", 0)
        return (-m, -s, (p.get("player_name") or "").lower())

    players.sort(key=sort_key)
    return jsonify({"ok": True, "players": players})


@app.post("/api/ingest")
def api_ingest():
    payload = request.get_json(silent=True)
    if payload is None:
        return jsonify({"ok": False, "error": "Invalid or missing JSON body"}), 400

    name = payload.get("player_name")
    if not name:
        return jsonify({"ok": False, "error": "player_name is required"}), 400

    stamped = {
        "received_at_unix": int(time.time()),
        **payload,
    }

    append_jsonl(HISTORY_PATH, stamped)

    board = load_scoreboard()
    board[name] = stamped
    atomic_write_json(SCOREBOARD_PATH, board)

    players = list(board.values())
    players.sort(key=compute_score, reverse=True)

    player_identifier = stamped.get("player_identifier")

    position = None
    for idx, player in enumerate(players, start=1):
        same_identifier = (
            player_identifier and
            player.get("player_identifier") == player_identifier
        )
        same_name = player.get("player_name") == name

        if same_identifier or same_name:
            position = idx
            break

    publish_event({
        "type": "scoreboard_updated",
        "player_name": name,
        "ts": stamped["received_at_unix"]
    })

    return jsonify({
        "ok": True,
        "updated": 1,
        "position": position
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5005, debug=True)