# src/matching_engine.py
import numpy as np
import pandas as pd
import ast
from sqlalchemy import text
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler
from db_connect import get_engine

def get_alpha(n_interactions, midpoint=20, k=0.4):
    x = -k * (n_interactions - midpoint)
    alpha = 1 / (1 + np.exp(-x))
    return float(alpha)

def get_movie_audio_profile(genre: str) -> list:
    if not genre:
        return [0.5, 0.5, 0.5, 0.5]
    # Step 1: แยก primary genre
    primary = genre.split(",")[0].strip()

    # Step 2: map กับ audio profile
    profiles = {
    #              valence  energy  tempo   dance
    #              (mood)  (power) (pace)  (groove)
        "Action":     [0.45,   0.85,   0.75,   0.55],
        "Horror":     [0.15,   0.70,   0.55,   0.25],
        "Comedy":     [0.75,   0.65,   0.60,   0.65],
        "Romance":    [0.65,   0.45,   0.35,   0.45],
        "Drama":      [0.35,   0.50,   0.40,   0.35],
        "Thriller":   [0.25,   0.75,   0.65,   0.35],
        "Animation":  [0.75,   0.70,   0.60,   0.70],
        "Science Fiction": [0.40, 0.75, 0.65,  0.45],
        "Adventure":  [0.60,   0.80,   0.70,   0.55],
        "Mystery":    [0.25,   0.55,   0.45,   0.30],
    }

    # Step 3: return profile (ถ้าไม่มีใน dict → neutral)
    return profiles.get(primary, [0.5, 0.5, 0.5, 0.5])

def match_songs(movie_id, top_k=10, n_interactions=0):
    engine = get_engine()

    # Step 1: ดึง movie embedding จาก DB
    with engine.connect() as conn:
        movie = conn.execute(text("""
            SELECT title, embedding, genre
            FROM movies
            WHERE id = :mid
        """), {"mid": movie_id}).fetchone()

        if movie is None:
            print(f"⚠️ movie_id={movie_id} not found, skipping")
            return pd.DataFrame()

    print(f"Movie: {movie.title}")

    # Step 2: ดึง songs ทั้งหมดที่มี embedding
    with engine.connect() as conn:
        songs_df = pd.read_sql(text("""
            SELECT id, title, artist,
                    valence, energy, tempo, danceability,
                    embedding
            FROM songs
            WHERE embedding IS NOT NULL
        """), conn)
        if songs_df.empty:
            print("⚠️ No songs found, skipping")
            return pd.DataFrame()

    print(f"Found {len(songs_df)} songs")

    # Step 3 : content:score
    movie_vec = np.array(ast.literal_eval(movie.embedding))
    song_vecs = np.array([
        ast.literal_eval(emb) for emb in songs_df['embedding']
    ])
    content_scores = cosine_similarity(
        movie_vec.reshape(1, -1), song_vecs
    )[0]
    songs_df['content_score'] = content_scores

    # Step 4: audio score
    features = ['valence', 'energy', 'tempo', 'danceability']
    scaler = MinMaxScaler()
    songs_norm = songs_df.copy()
    songs_norm[features] = scaler.fit_transform(songs_df[features])
    movie_audio = get_movie_audio_profile(movie.genre)
    songs_df['audio_score'] = songs_norm[features].apply(
        lambda row: 1 - np.mean(np.abs(row.values - movie_audio)),
        axis=1
    )

    # Step 5: hybrid_score
    alpha = get_alpha(n_interactions)
    songs_df['hybrid_score'] = (
        alpha * songs_df['content_score'] +
        (1 - alpha) * songs_df['audio_score']
    )
    songs_df['alpha_used'] = alpha

    # Step 6: return
    result = (
        songs_df[['id', 'title', 'artist',
                  'content_score', 'audio_score',
                  'hybrid_score', 'alpha_used']]
        .sort_values('hybrid_score', ascending=False)
        .head(top_k)
        .reset_index(drop=True)
    )
    return result
def save_matches(movie_id, matches_df):
    engine = get_engine()
    
    with engine.connect() as conn:
        for _, row in matches_df.iterrows():
            conn.execute(text("""
                INSERT INTO vibe_matches
                    (movie_id, song_id, content_score,
                     audio_score, hybrid_score, alpha_used)
                VALUES
                    (:movie_id, :song_id, :content,
                     :audio, :hybrid, :alpha)
                ON CONFLICT (movie_id, song_id)
                DO UPDATE SET
                    content_score = EXCLUDED.content_score,
                    audio_score   = EXCLUDED.audio_score,
                    hybrid_score  = EXCLUDED.hybrid_score,
                    alpha_used    = EXCLUDED.alpha_used
            """), {
                "movie_id": movie_id,
                "song_id":  row['id'],
                "content":  row['content_score'],
                "audio":    row['audio_score'],
                "hybrid":   row['hybrid_score'],
                "alpha":    row['alpha_used']
            })
        conn.commit()
    print(f"Saved {len(matches_df)} matches for movie_id={movie_id}")


if __name__ == "__main__":
    # ดึง movie ids ทั้งหมด
    engine = get_engine()
    with engine.connect() as conn:
        movie_ids = [
            row[0] for row in
            conn.execute(text("SELECT id FROM movies ORDER BY id")).fetchall()
        ]
    
    print(f"Matching {len(movie_ids)} movies...")
    
    for movie_id in movie_ids:
        matches = match_songs(movie_id=movie_id, top_k=10, n_interactions=0)
        save_matches(movie_id, matches)
    
    print("✅ All done!")