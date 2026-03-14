from dotenv import load_dotenv
import os
import requests
import base64
import random
import sys
sys.path.append(os.path.dirname(__file__))
from utils import safe_request, safe_json  # ← เพิ่ม

load_dotenv()

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

GENRE_PROFILES = {
    "Action":       {"valence": (0.3, 0.6), "energy": (0.7, 1.0), "tempo": (120, 160), "danceability": (0.4, 0.7)},
    "Romance":      {"valence": (0.6, 1.0), "energy": (0.3, 0.6), "tempo": (70, 110),  "danceability": (0.5, 0.8)},
    "Horror":       {"valence": (0.0, 0.3), "energy": (0.6, 0.9), "tempo": (100, 140), "danceability": (0.2, 0.5)},
    "Comedy":       {"valence": (0.6, 1.0), "energy": (0.5, 0.8), "tempo": (100, 130), "danceability": (0.5, 0.9)},
    "Drama":        {"valence": (0.2, 0.5), "energy": (0.3, 0.6), "tempo": (60, 100),  "danceability": (0.3, 0.6)},
    "Science Fiction": {"valence": (0.3, 0.7), "energy": (0.6, 0.9), "tempo": (110, 150), "danceability": (0.4, 0.7)},
    "Thriller":     {"valence": (0.1, 0.4), "energy": (0.6, 0.9), "tempo": (110, 150), "danceability": (0.3, 0.6)},
    "Animation":    {"valence": (0.5, 0.9), "energy": (0.4, 0.7), "tempo": (90, 130),  "danceability": (0.5, 0.8)},
    "Default":      {"valence": (0.3, 0.7), "energy": (0.3, 0.7), "tempo": (80, 130),  "danceability": (0.3, 0.7)},
}


def get_spotify_token():
    credentials = f"{CLIENT_ID}:{CLIENT_SECRET}"
    encoded = base64.b64encode(credentials.encode()).decode()

    # ← Spotify token ใช้ POST ไม่ใช่ GET
    # safe_request ใช้ GET เท่านั้น — ใช้ requests.post ตรงๆ ได้เลย
    response = requests.post(
        "https://accounts.spotify.com/api/token",
        headers={
            "Authorization": f"Basic {encoded}",
            "Content-Type": "application/x-www-form-urlencoded"
        },
        data={"grant_type": "client_credentials"}
    )
    response.raise_for_status()
    return response.json()["access_token"]


def search_track(token, query):
    response = safe_request(                    # ← เปลี่ยน
        "https://api.spotify.com/v1/search",
        headers={"Authorization": f"Bearer {token}"},
        params={"q": query, "type": "track", "limit": 1}
    )
    items = safe_json(response, key="tracks")["items"]  # ← เปลี่ยน
    if not items:
        return None
    track = items[0]
    return {
        "spotify_id": track["id"],
        "title": track["name"],
        "artist": track["artists"][0]["name"],
    }


def mock_audio_features(genre_str):
    matched = "Default"
    for genre in GENRE_PROFILES:
        if genre.lower() in genre_str.lower():
            matched = genre
            break
    profile = GENRE_PROFILES[matched]

    def rand_range(key):
        lo, hi = profile[key]
        return round(random.uniform(lo, hi), 4)

    return {
        "valence":      rand_range("valence"),
        "energy":       rand_range("energy"),
        "tempo":        round(random.uniform(*profile["tempo"]), 1),
        "danceability": rand_range("danceability"),
        "source":       "mock"
    }


def fetch_song_for_movie(token, movie_title, genre):
    track = search_track(token, f"{movie_title} soundtrack")
    if not track:
        first_genre = genre.split(",")[0].strip()
        track = search_track(token, f"{first_genre} music")
    if not track:
        return None
    features = mock_audio_features(genre)
    return {**track, **features}


if __name__ == "__main__":
    import pandas as pd
    from sqlalchemy import create_engine

    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://vibeuser:vibepass@localhost:5432/vibedb"
    )

    token = get_spotify_token()
    print("✅ Token OK")

    # ดึงรายชื่อหนังจาก DB
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        from sqlalchemy import text
        rows = conn.execute(text("SELECT id, title, genre FROM movies")).fetchall()

    print(f"🎬 พบ {len(rows)} movies ใน DB")

    songs = []
    for row in rows:
        movie_id, title, genre = row
        print(f"  🎵 หาเพลงสำหรับ: {title}")
        result = fetch_song_for_movie(token, title, genre)
        if result:
            result["movie_ref"] = movie_id  # เก็บไว้อ้างอิง (ไม่ insert)
            songs.append(result)

    # drop_duplicates ป้องกัน spotify_id ซ้ำ
    df = pd.DataFrame(songs)
    df = df.drop_duplicates(subset=["spotify_id"])
    df = df.drop(columns=["movie_ref", "source"])  # ไม่มี column นี้ใน schema
    print(f"📦 หลัง dedup เหลือ {len(df)} songs")

    df.to_sql("songs", engine, if_exists="append", index=False, method="multi")
    print(f"✅ Insert สำเร็จ {len(df)} songs")