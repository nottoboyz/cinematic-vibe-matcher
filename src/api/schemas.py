from pydantic import BaseModel, Field
from typing import List

class SongMatch(BaseModel):
    song_id: int
    title: str
    artist: str
    similarity_score: float
    rank: int

class RecommendResponse(BaseModel):
    movie_id: int
    movie_title: str
    matches: List[SongMatch]

class FeedbackRequest(BaseModel):
    movie_id: int
    song_id: int
    rating: float = Field(..., ge=1, le=5)

class FeedbackResponse(BaseModel):
    success: bool
    message: str