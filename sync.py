import os, json, requests

ANILIST_USER = os.environ["ANILIST_USER"]
CLIENT_ID = os.environ["SHIKI_CLIENT_ID"]
CLIENT_SECRET = os.environ["SHIKI_CLIENT_SECRET"]
AUTH_CODE = os.environ["SHIKI_AUTH_CODE"]
HEADERS = {"User-Agent": "AnilistSync/1.0"}

token_file = "token.json"
if os.path.exists(token_file):
    tokens = json.load(open(token_file))
    r = requests.post("https://shikimori.io", headers=HEADERS, data={
        "grant_type": "refresh_token", "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET, "refresh_token": tokens["refresh_token"]
    })
else:
    r = requests.post("https://shikimori.io", headers=HEADERS, data={
        "grant_type": "authorization_code", "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET, "code": AUTH_CODE,
        "redirect_uri": "urn:ietf:wg:oauth:2.0:oob"
    })

tokens = r.json()
if "access_token" not in tokens:
    raise Exception(f"Ошибка авторизации Shikimori: {tokens}")
json.dump(tokens, open(token_file, "w"))
HEADERS["Authorization"] = f"Bearer {tokens['access_token']}"

query = '''
query ($name: String) {
  MediaListCollection(userName: $name, type: ANIME) {
    lists { entries { status progress score(format: POINT_10) media { idMal } } }
  }
}'''
al_data = requests.post("https://anilist.co", json={"query": query, "variables": {"name": ANILIST_USER}}).json()

STATUS_MAP = {"CURRENT": "watching", "COMPLETED": "completed", "PAUSED": "on_hold", "DROPPED": "dropped", "PLANNING": "planned"}

me = requests.get("https://shikimori.io", headers=HEADERS).json()
user_id = me["id"]

for lst in al_data["data"]["MediaListCollection"]["lists"]:
    for entry in lst["entries"]:
        mal_id = entry["media"]["idMal"]
        if not mal_id: continue
        payload = {
            "user_rate": {
                "user_id": user_id,
                "target_id": mal_id,
                "target_type": "Anime",
                "status": STATUS_MAP.get(entry["status"], "watching"),
                "episodes": entry["progress"],
                "score": int(entry["score"] or 0)
            }
        }
        requests.post("https://shikimori.io", headers=HEADERS, json=payload)
print("Синхронизация завершена!")
