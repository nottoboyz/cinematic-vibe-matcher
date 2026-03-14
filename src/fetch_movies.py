from dotenv import load_dotenv
import os
import requests
import sys
sys.path.append(os.path.dirname(__file__))
from utils import safe_request, safe_json

load_dotenv()

BASE_URL = "https://api.themoviedb.org/3"
TOKEN = os.getenv("TMDB_API_KEY")

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

def fetch_genres():
    response = safe_request(
        f"{BASE_URL}/genre/movie/list",
        headers=headers,
        params={"language": "en-US"}
    )
    genres = safe_json(response, key="genres")
    return {g["id"]: g["name"] for g in genres}


def fetch_popular_movies(pages=3):
    genre_map = fetch_genres()
    all_movies = []

    for page in range(1, pages + 1):
        print(f"กำลังดึง page {page}/{pages}...")

        response = safe_request(
            f"{BASE_URL}/movie/popular",
            headers=headers,
            params={"language": "en-US", "page": page}
        )
        movies = safe_json(response, key="results")

        for m in movies:
            genre_names = [
                genre_map.get(gid, "Unknown")
                for gid in m.get("genre_ids", [])
            ]
            all_movies.append({
                "tmdb_id": m["id"],
                "title": m["title"],
                "overview": m.get("overview", ""),
                "genre": ", ".join(genre_names),
                "release_date": m.get("release_date", None),
                "popularity": m.get("popularity", 0),
            })

    print(f"\n✅ ดึงมาได้ทั้งหมด {len(all_movies)} movies")
    return all_movies


if __name__ == "__main__":
    import pandas as pd
    from sqlalchemy import create_engine

    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://vibeuser:vibepass@localhost:5432/vibedb"
    )

    movies = fetch_popular_movies(pages=2)
    for m in movies[:2]:
        print(m)

    df = pd.DataFrame(movies)

    # ✅ กัน duplicate tmdb_id ที่ TMDB ส่งมาซ้ำระหว่าง page
    df = df.drop_duplicates(subset=["tmdb_id"])
    print(f"📦 หลัง dedup เหลือ {len(df)} movies")

    engine = create_engine(DATABASE_URL)
    df.to_sql("movies", engine, if_exists="append", index=False, method="multi")
    print(f"✅ Insert สำเร็จ {len(df)} movies")
