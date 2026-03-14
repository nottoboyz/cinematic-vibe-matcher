from matching_engine import match_songs

# user ใหม่
print("=== n_interactions=0 ===")
r0 = match_songs(movie_id=1, top_k=3, n_interactions=0)
print(r0[['title', 'hybrid_score', 'alpha_used']])

# user เล่นมาแล้ว 20 ครั้ง
print("\n=== n_interactions=20 ===")
r20 = match_songs(movie_id=1, top_k=3, n_interactions=20)
print(r20[['title', 'hybrid_score', 'alpha_used']])