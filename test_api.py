import requests
import random
import time
from security import create_access_token

BASE_URL = "http://127.0.0.1:8000"
AUTH_HEADERS = {"Authorization": f"Bearer {create_access_token('game-server')}"}


def populate_database():
    print("⏳ Populăm baza de date cu scoruri fictive...\n")

    players = ["Alex", "Maria", "John", "Elena", "David", "Sofia"]

    # Generăm 15 scoruri aleatoare
    for _ in range(15):
        player = random.choice(players)
        score = random.randint(50, 500)

        data = {"player_name": player, "score": score}

        response = requests.post(f"{BASE_URL}/scores", json=data, headers=AUTH_HEADERS)
        if response.status_code == 200:
            print(f"✅ Adăugat: {player} cu scorul {score}")
        else:
            print(f"❌ Eroare la adăugare: {response.text}")

        # O mică pauză ca să avem timestamp-uri ușor diferite
        time.sleep(0.1)


def check_leaderboard():
    print("\n🏆 Top 10 Leaderboard:")
    response = requests.get(f"{BASE_URL}/scores")

    if response.status_code == 200:
        scores = response.json()
        for i, s in enumerate(scores, 1):
            print(f"{i}. {s['player_name']} - {s['score']} puncte")
    else:
        print("Eroare la preluarea leaderboard-ului.")


def check_player_history(player_name):
    print(f"\n📜 Istoric pentru {player_name}:")
    response = requests.get(f"{BASE_URL}/player/{player_name}")

    if response.status_code == 200:
        history = response.json()
        for entry in history["items"]:
            # Formatăm data pentru a fi mai ușor de citit
            date_str = entry["timestamp"].split("T")[0]
            time_str = entry["timestamp"].split("T")[1].split(".")[0]
            print(f"Scor: {entry['score']} | Data: {date_str} Ora: {time_str}")
    else:
        print(f"Eroare: {response.json().get('detail')}")


if __name__ == "__main__":
    # 1. Adăugăm date
    populate_database()

    # 2. Afișăm clasamentul general
    check_leaderboard()

    # 3. Verificăm istoricul unui jucător specific (Alegem "Maria" de exemplu)
    check_player_history("Maria")
