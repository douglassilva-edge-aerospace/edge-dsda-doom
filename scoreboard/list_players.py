import json
import os

def compute_score(p):
    """
    Ported from your JavaScript function. 
    Handles both object and list formats for items/time.
    """
    try:
        # Extract monster stats
        m_killed = p.get("monsters", {}).get("killed", 0)
        m_total = p.get("monsters", {}).get("total", 1) or 1 # Avoid division by zero
        
        # Extract secret stats
        s_found = p.get("secrets", {}).get("found", 0)
        s_total = p.get("secrets", {}).get("total", 1) or 1
        
        # Extract item stats (Handles both {"picked_up": x, "total": y} and [x, y])
        items_data = p.get("items", {})
        if isinstance(items_data, dict):
            i_picked = items_data.get("picked_up", 0)
            i_total = items_data.get("total", 1) or 1
        elif isinstance(items_data, list) and len(items_data) >= 2:
            i_picked = items_data[0]
            i_total = items_data[1] or 1
        else:
            i_picked, i_total = 0, 1

        face = p.get("face_index", 0)

        # Formula logic
        score = (100 * (m_killed / m_total)) + \
                (50 * (s_found / s_total)) + \
                (25 * (i_picked / i_total)) + \
                (0.1 * face)
        
        return round(score, 2), m_killed, i_picked, s_found
    except Exception:
        return 0, 0, 0, 0

def get_top_10(filename):
    if not os.path.exists(filename):
        print(f"Error: {filename} not found.")
        return

    players = []

    with open(filename, 'r') as f:
        for line in f:
            if not line.strip():
                continue
            
            data = json.loads(line)
            score, killed, picked, found = compute_score(data)
            
            players.append({
                "name": data.get("player_name", "Unknown"),
                "score": score,
                "monsters": killed,
                "items": picked,
                "secrets": found
            })

    # Sort by score descending
    scoreboard_list = sorted(players, key=lambda x: x['score'], reverse=True)

    # Print formatted output
    for i, p in enumerate(scoreboard_list, 1):
        print(f"{i}. {p['name']} - Monsters Killed: {p['monsters']}, "
              f"Items Pickedup: {p['items']}, Secrets Found: {p['secrets']}, "
              f"Score : {p['score']}")

if __name__ == "__main__":
    get_top_10("data/history.jsonl")
