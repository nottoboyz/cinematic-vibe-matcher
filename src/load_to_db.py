import pandas as pd
import sys
import os

# เพิ่ม src/ เข้า path เพื่อ import ไฟล์อื่นได้
sys.path.append(os.path.dirname(__file__))

from db_connect import get_engine
from sqlalchemy import text

def load_movies(df_movies):
    """
    Insert movies เข้า DB
    
    ทำไมใช้ if_exists='append'?
    → 'replace' = ลบ table แล้วสร้างใหม่ (อันตราย!)
    → 'append' = เพิ่มข้อมูลต่อท้าย (ปลอดภัย)
    → 'fail' = error ถ้า table มีอยู่แล้ว
    """
    engine = get_engine()

    # เลือกเฉพาะ columns ที่ตรงกับ schema
    df = df_movies[["tmdb_id", "title", "overview", "genre", "release_date", "popularity"]]

    # แปลง release_date เป็น datetime
    df = df.copy()
    df["release_date"] = pd.to_datetime(df["release_date"], errors="coerce")

    df.to_sql(
        name="movies",        # ชื่อ table ใน DB
        con=engine,           # engine ที่สร้างไว้
        if_exists="append",   # append ต่อท้าย
        index=False,          # ไม่เอา pandas index
        method="multi"        # insert หลาย rows ทีเดียว (เร็วกว่า)
    )

    print(f"✅ Insert movies สำเร็จ: {len(df)} rows")


def load_songs(df_songs):
    """Insert songs เข้า DB"""
    engine = get_engine()

    df = df_songs[["spotify_id", "title", "artist", "valence", "energy", "tempo", "danceability"]].copy()

    df.to_sql(
        name="songs",
        con=engine,
        if_exists="append",
        index=False,
        method="multi"
    )

    print(f"✅ Insert songs สำเร็จ: {len(df)} rows")


def verify_data():
    """เช็คว่าข้อมูลเข้า DB จริง"""
    engine = get_engine()

    with engine.connect() as conn:
        movies_count = conn.execute(text("SELECT COUNT(*) FROM movies")).fetchone()[0]
        songs_count = conn.execute(text("SELECT COUNT(*) FROM songs")).fetchone()[0]

        print(f"\n📊 ข้อมูลใน DB ตอนนี้:")
        print(f"   movies: {movies_count} rows")
        print(f"   songs:  {songs_count} rows")

        # ดู sample
        print("\n🎬 Movies ตัวอย่าง:")
        result = conn.execute(text("SELECT title, genre FROM movies LIMIT 3"))
        for row in result:
            print(f"   {row[0]} | {row[1]}")

        print("\n🎵 Songs ตัวอย่าง:")
        result = conn.execute(text("SELECT title, artist, valence, energy FROM songs LIMIT 3"))
        for row in result:
            print(f"   {row[0]} - {row[1]} | valence={row[2]} energy={row[3]}")


if __name__ == "__main__":
    # โหลด CSV ที่ save ไว้ใน Block 5
    print("กำลังโหลด CSV...")
    df_movies = pd.read_csv("data/raw/movies.csv")
    df_songs = pd.read_csv("data/raw/songs.csv")
    print(f"Movies: {len(df_movies)} rows | Songs: {len(df_songs)} rows")

    print("\nกำลัง insert เข้า DB...")
    load_movies(df_movies)
    load_songs(df_songs)

    verify_data()