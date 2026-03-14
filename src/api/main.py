# import ที่ต้องใช้
from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

# import จากไฟล์ที่เราเพิ่งเขียน
from .database import get_db
from .schemas import (
    RecommendResponse,
    SongMatch,
    FeedbackRequest,
    FeedbackResponse
)

# สร้าง FastAPI instance
app = FastAPI(
    title="🎬 Cinematic Vibe Matcher API",
    description="Match movies to songs using AI embeddings",
    version="1.0.0"
)

@app.get("/")
async def root():
    return {"status": "alive", "service": "Cinematic Vibe Matcher"}

@app.get("/recommend/{movie_id}", response_model=RecommendResponse)
async def get_recommendations(
    movie_id: int,
    top_k: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    # เช็คว่า movie มีอยู่จริง
    movie_query = text("SELECT id, title FROM movies WHERE id = :movie_id")
    movie_result = await db.execute(movie_query, {"movie_id": movie_id})
    movie = movie_result.fetchone()

    if not movie:
        raise HTTPException(status_code=404, detail=f"Movie id={movie_id} not found")
    

    matches_query = text("""
        SELECT 
            vm.song_id,
            s.title,
            s.artist,
            vm.hybrid_score AS similarity_score,
            ROW_NUMBER() OVER (ORDER BY vm.hybrid_score DESC) AS rank
        FROM vibe_matches vm
        JOIN songs s ON s.id = vm.song_id
        WHERE vm.movie_id = :movie_id
        AND vm.hybrid_score IS NOT NULL
        ORDER BY vm.hybrid_score DESC
        LIMIT :top_k
    """)

    matches_result = await db.execute(
        matches_query,
        {"movie_id": movie_id, "top_k": top_k}
    )
    rows = matches_result.fetchall()

    # แปลง rows → Pydantic models
    matches = [
        SongMatch(
            song_id=row.song_id,
            title=row.title,
            artist=row.artist,
            similarity_score=round(float(row.similarity_score or 0), 4),
            rank=row.rank
        )
        for row in rows   # ← loop ทุก row
    ]

    return RecommendResponse(
        movie_id=movie_id,
        movie_title=movie.title,
        matches=matches
    )

@app.get("/movies")
async def get_movies(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        text("SELECT id, title FROM movies ORDER BY title")
    )
    rows = result.fetchall()
    return [{"id": row.id, "title": row.title} for row in rows]

@app.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    body: FeedbackRequest,                         # รับ request body
    db: AsyncSession = Depends(get_db)
):
    # เช็คว่า movie และ song มีอยู่จริงในครั้งเดียว
    check_query = text("""
        SELECT 
            EXISTS(SELECT 1 FROM movies WHERE id = :movie_id) as movie_exists,
            EXISTS(SELECT 1 FROM songs  WHERE id = :song_id)  as song_exists
    """)
    check = await db.execute(
        check_query,
        {"movie_id": body.movie_id, "song_id": body.song_id}
    )
    result = check.fetchone()

    if not result.movie_exists:
        raise HTTPException(status_code=404, detail=f"Movie id={body.movie_id} not found")
    if not result.song_exists:
        raise HTTPException(status_code=404, detail=f"Song id={body.song_id} not found")
    
    insert_query = text("""
        INSERT INTO user_feedback (movie_id, song_id, rating)
        VALUES (:movie_id, :song_id, :rating)
        ON CONFLICT (movie_id, song_id)
        DO UPDATE SET
            rating = EXCLUDED.rating,
            created_at = NOW()
        RETURNING id
    """)

    insert_result = await db.execute(
        insert_query,
        {"movie_id": body.movie_id, "song_id": body.song_id, "rating": body.rating}
    )
    feedback_id = insert_result.scalar() # ดึง id ที่ RETURNING ส่งมา

    # update n_interactions ใน vibe_matches
    update_query = text("""
        UPDATE vibe_matches
        SET n_interactions = n_interactions + 1
        WHERE movie_id = :movie_id AND song_id = :song_id
    """)

    await db.execute(
        update_query,
        {"movie_id": body.movie_id, "song_id": body.song_id}
    )

    # return response
    return FeedbackResponse(
        success=True,
        message=f"Feedback saved (id={feedback_id})"
    )