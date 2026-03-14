# src/query_similar.py
from nlp_processor import NLPProcessor
from db_connect import get_engine
from sqlalchemy import text

processor = NLPProcessor()
engine = get_engine()

def find_similar_movies(query_text: str, top_k: int = 5):

    # แปลง query → vector
    query_embedding = processor.get_embedding(query_text)

    # Query หา movie ที่ใกล้เคียงที่สุด
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT title, overview, similarity FROM (
                SELECT title, overview,
                        1 - (embedding <=> CAST(:embedding AS vector)) as similarity
                FROM movies
                WHERE embedding IS NOT NULL
            ) ranked
            ORDER BY similarity DESC
            LIMIT :top_k
        """), {
            "embedding": str(query_embedding),
            "top_k": top_k
        })

        movies = result.fetchall()

    print(f"\n🔍 Query: '{query_text}'")
    print(f"{'='*50}")
    for i, movie in enumerate(movies):
        print(f"{i+1}. {movie[0]}")
        print(f"    Similarity: {movie[2]:.4f}")
        print(f"    Overview: {movie[1][:80]}...")
        print()

if __name__ == "__main__":
    find_similar_movies("A heartwarming family adventure with friendship and love")