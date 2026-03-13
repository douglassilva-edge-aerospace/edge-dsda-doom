import json
import os

def compute_score(p):
    """Ported scoring logic with safety for missing/zero values."""
    try:
        # Extract monster stats
        m_killed = p.get("monsters", {}).get("killed", 0)
        m_total = p.get("monsters", {}).get("total", 1) or 1
        
        # Extract secret stats
        s_found = p.get("secrets", {}).get("found", 0)
        s_total = p.get("secrets", {}).get("total", 1) or 1
        
        # Extract item stats
        i_picked = p.get("items", {}).get("picked_up", 0)
        i_total = p.get("items", {}).get("total", 1) or 1

        face = p.get("face_index", 0)

        # Formula: 100*monsters + 50*secrets + 25*items + 0.1*face
        score = (100 * (m_killed / m_total)) + \
                (50 * (s_found / s_total)) + \
                (25 * (i_picked / i_total)) + \
                (0.1 * face)
        
        return round(score, 2), m_killed, i_picked, s_found
    except Exception:
        return 0, 0, 0, 0

def generate_leaderboard(filename):
    if not os.path.exists(filename):
        print(f"Error: {filename} not found.")
        return

    with open(filename, 'r') as f:
        data = json.load(f)

    all_players = []

    # Iterate through the dictionary keys (Player_000000, TEST, etc.)
    for key in data:
        player_stats = data[key]
        score, killed, picked, found = compute_score(player_stats)
        
        all_players.append({
            "name": player_stats.get("player_name", key),
            "score": score,
            "monsters": killed,
            "items": picked,
            "secrets": found
        })

    # Sort all players by score descending
    sorted_players = sorted(all_players, key=lambda x: x['score'], reverse=True)

    print(f"{'Rank':<5} | {'Player':<15} | {'Score':<10} | {'Stats'}")
    print("-" * 75)

    for i, p in enumerate(sorted_players, 1):
        print(f"{i:<5} | {p['name']:<15} | {p['score']:<10} | "
              f"Monsters: {p['monsters']}, Items: {p['items']}, Secrets: {p['secrets']}")

if __name__ == "__main__":
    generate_leaderboard("data/scoreboard.json")