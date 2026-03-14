import pandas as pd
from fetch_movies import fetch_popular_movies
from fetch_songs import get_spotify_token, fetch_song_for_movie

def build_dataframes():
    """
    ดึงข้อมูลทั้งหมด แล้วแปลงเป็น DataFrame
    
    ทำไมต้องใช้ pandas DataFrame?
    → จัดการ missing data ได้ง่าย
    → filter/transform ข้อมูลเป็น column ได้เลย
    → insert เข้า DB ได้ทีเดียวทั้ง table
    """
    print("=" * 40)
    print("STEP 1: ดึง movies จาก TMDB")
    print("=" * 40)
    movies = fetch_popular_movies(pages=2)  # 40 movies
    df_movies = pd.DataFrame(movies)

    print(f"\nshape: {df_movies.shape}")  # (rows, columns)
    print(df_movies.head(3))             # ดู 3 แถวแรก

    print("\n" + "=" * 40)
    print("STEP 2: ดึง songs จาก Spotify")
    print("=" * 40)
    token = get_spotify_token()

    songs = []
    for i, row in df_movies.iterrows():
        print(f"[{i+1}/{len(df_movies)}] {row['title']}")
        song = fetch_song_for_movie(token, row["title"], row["genre"])
        if song:
            song["movie_tmdb_id"] = row["tmdb_id"]  # เชื่อมกับหนัง
            songs.append(song)

    df_songs = pd.DataFrame(songs)

    print(f"\nshape: {df_songs.shape}")
    print(df_songs.head(3))

    return df_movies, df_songs


if __name__ == "__main__":
    df_movies, df_songs = build_dataframes()

    # เช็ค missing values
    print("\n=== Missing values (movies) ===")
    print(df_movies.isnull().sum())

    print("\n=== Missing values (songs) ===")
    print(df_songs.isnull().sum())

    # บันทึกเป็น CSV ไว้ตรวจสอบ
    df_movies.to_csv("data/raw/movies.csv", index=False)
    df_songs.to_csv("data/raw/songs.csv", index=False)
    print("\n✅ บันทึก CSV ลง data/raw/ แล้ว")