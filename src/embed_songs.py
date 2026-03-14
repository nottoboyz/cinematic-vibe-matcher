# src/embed_songs.py
from sqlalchemy import text
from db_connect import get_engine
from nlp_processor import NLPProcessor

def describe_audio_features(valence, energy, tempo, danceability) -> str:
    parts = []

    if valence < 0.25:
        parts.append("melancholic, dark")
    elif valence < 0.55:
        parts.append("neutral, bittersweet")
    else:
        parts.append("happy, joyful")

    if energy < 0.55:
        parts.append("calm, mellow")
    elif energy < 0.80:
        parts.append("energetic")
    else:
        parts.append("intense, powerful")

    if tempo < 90:
        parts.append("slow, ballad")
    elif tempo < 125:
        parts.append("moderate pace")
    else:
        parts.append("fast-paced, driving")

    if danceability < 0.40:
        parts.append("non-danceable")
    elif danceability < 0.62:
        parts.append("groovy")
    else:
        parts.append("highly danceable")

    return ". ".join(parts)

def build_song_text(title: str, artist: str,
                    valence: float, energy: float,
                    tempo: float, danceability: float) -> str:
    mood = describe_audio_features(valence, energy, tempo, danceability)
    text = f"{title} by {artist}. Mood: {mood}."
    return text

def embed_all_songs():
    engine = get_engine()
    nlp = NLPProcessor()

    # Step 1: ดึง songs ที่ยังไม่มี embedding
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT id, title, artist, valence, energy, tempo, danceability
            FROM songs
            WHERE embedding IS NULL
        """)).fetchall()

    print(f"Found {len(rows)} songs to embed")

    if not rows:
        print("✅ All songs already embedded!")
        return

    # Step 2: วน loop สร้าง embedding
    with engine.connect() as conn:
        for i, row in enumerate(rows):
            # สร้าง text จาก title + artist
            text_input = build_song_text(
                row.title, row.artist,
                float(row.valence), float(row.energy),
                float(row.tempo),   float(row.danceability)
)

            # สร้าง vector
            vec = nlp.get_embedding(text_input)

            # UPDATE กลับลง DB
            conn.execute(text("""
                UPDATE songs
                SET embedding = :vec
                WHERE id = :sid
            """), {"vec": str(vec), "sid": row.id})

            if (i + 1) % 10 == 0:
                print(f"  {i+1}/{len(rows)} songs embedded...")

        conn.commit()
        print("Done!")

if __name__ == "__main__":
    embed_all_songs()