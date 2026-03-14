"""
generate_embeddings.py
----------------------
สร้าง vector embeddings สำหรับ movies และ songs แล้วบันทึกลง DB
ใช้ sentence-transformers model: all-mpnet-base-v2 (384 dimensions)
"""

from dotenv import load_dotenv
import os
import sys
sys.path.append(os.path.dirname(__file__))

load_dotenv()

from sqlalchemy import create_engine, text
from sentence_transformers import SentenceTransformer
import numpy as np

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://vibeuser:vibepass@localhost:5432/vibedb"
)

# โหลด model ครั้งเดียว
print("🤖 กำลังโหลด embedding model...")
model = SentenceTransformer("all-mpnet-base-v2")
print("✅ โหลด model สำเร็จ")

def get_genre_vibe(genre: str) -> str:
    """แปลง genre → vibe language ให้ match กับ song mood"""
    if not genre:
        return ""
    
    primary = genre.split(",")[0].strip()
    
    vibes = {
        "Action":     "intense, powerful. fast-paced, driving.",
        "Horror":     "melancholic, dark. non-danceable.",
        "Comedy":     "happy, joyful. groovy.",
        "Romance":    "happy, joyful. calm, mellow.",
        "Drama":      "neutral, bittersweet. calm, mellow.",
        "Thriller":   "melancholic, dark. energetic.",
        "Animation":  "happy, joyful. highly danceable.",
        "Science Fiction": "neutral, bittersweet. energetic.",
        "Adventure":  "happy, joyful. intense, powerful.",
        "Mystery":    "melancholic, dark. calm, mellow.",
    }
    
    return vibes.get(primary, "neutral, bittersweet.")

def make_movie_text(row):
    vibe = get_genre_vibe(row['genre'])
    return f"{row['title']}. {row['genre']}. {row['overview']} Vibe: {vibe}"


def make_song_text(row):
    """สร้าง text จาก song สำหรับ embed"""
    return (
        f"{row['title']} by {row['artist']}. "
        f"Mood: valence={row['valence']}, energy={row['energy']}, "
        f"tempo={row['tempo']}, danceability={row['danceability']}"
    )


def embed_movies(engine):
    print("\n🎬 กำลัง embed movies...")
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT id, title, genre, overview FROM movies")
        ).mappings().fetchall()

    print(f"   พบ {len(rows)} movies")

    texts = [make_movie_text(r) for r in rows]
    embeddings = model.encode(texts, show_progress_bar=True)

    with engine.connect() as conn:
        for row, emb in zip(rows, embeddings):
            emb_list = emb.tolist()
            conn.execute(
                text("UPDATE movies SET embedding = :emb WHERE id = :id"),
                {"emb": str(emb_list), "id": row["id"]}
            )
        conn.commit()

    print(f"✅ embed movies สำเร็จ {len(rows)} rows")


def embed_songs(engine):
    print("\n🎵 กำลัง embed songs...")
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT id, title, artist, valence, energy, tempo, danceability FROM songs")
        ).mappings().fetchall()

    print(f"   พบ {len(rows)} songs")

    texts = [make_song_text(r) for r in rows]
    embeddings = model.encode(texts, show_progress_bar=True)

    with engine.connect() as conn:
        for row, emb in zip(rows, embeddings):
            emb_list = emb.tolist()
            conn.execute(
                text("UPDATE songs SET embedding = :emb WHERE id = :id"),
                {"emb": str(emb_list), "id": row["id"]}
            )
        conn.commit()

    print(f"✅ embed songs สำเร็จ {len(rows)} rows")


if __name__ == "__main__":
    engine = create_engine(DATABASE_URL)
    embed_movies(engine)
    embed_songs(engine)
    print("\n🎉 generate embeddings เสร็จสมบูรณ์!")
