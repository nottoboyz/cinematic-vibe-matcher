# src/embed_movies.py
from nlp_processor import NLPProcessor
from db_connect import get_engine
from sqlalchemy import text

def embed_all_movies():
    engine = get_engine()
    processor = NLPProcessor()

    # ดึง movies ทั้งหมดที่ยังไม่มี embedding
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT id, title, overview
            FROM movies
            WHERE embedding IS NULL
        """))
        movies = result.fetchall()

    print(f"พบ {len(movies)} movies ที่ยังไม่มี embedding")

    # วน loop แปลงทีละ movie
    with engine.connect() as conn:
        for i, movie in enumerate(movies):
            movie_id = movie[0]
            title    = movie[1]
            overview = movie[2]

            try:
                embedding = processor.get_embedding(overview)
                entities = processor.extract_entities(overview)
                sentiment = processor.get_sentiment(overview)

                conn.execute(text("""
                    UPDATE movies
                    SET embedding = :embedding
                    WHERE id = :id
                """), {
                    "embedding": str(embedding),
                    "id": movie_id
                })

                print(f"[{i+1}/{len(movies)}] ✅ {title} | sentiment: {sentiment:.3f}")

            except Exception as e:
                print(f"❌ {title}: {e}")
                continue

        conn.commit()
        print("\n✅ บันทึก embeddings ครบทุก movie แล้ว!")

if __name__ == "__main__":
    embed_all_movies()