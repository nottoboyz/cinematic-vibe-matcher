# tests/integration/test_api.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from src.api.main import app
from src.api.database import get_db


def make_mock_db(fetchone_value=None, fetchall_value=None, scalar_value=None):
    """
    Helper สร้าง mock AsyncSession
    
    ทำไมต้องเป็น AsyncMock?
    เพราะ endpoint ใช้ await db.execute() 
    ถ้าใช้ MagicMock ธรรมดา await จะ error
    """
    db = AsyncMock()
    result = MagicMock()
    result.fetchone.return_value = fetchone_value
    result.fetchall.return_value = fetchall_value or []
    result.scalar.return_value = scalar_value
    db.execute.return_value = result
    return db


@pytest.fixture
def client():
    """
    TestClient สำหรับ FastAPI
    override get_db dependency ด้วย mock ทุกครั้ง
    """
    return TestClient(app)


# ─── Test GET / ───────────────────────────────────────────────────────────────

class TestRoot:

    def test_root_returns_alive(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["status"] == "alive"


# ─── Test GET /movies ─────────────────────────────────────────────────────────

class TestGetMovies:

    def test_returns_200(self, client):
        mock_db = make_mock_db(fetchall_value=[])
        app.dependency_overrides[get_db] = lambda: mock_db
        
        response = client.get("/movies")
        assert response.status_code == 200
        
        app.dependency_overrides.clear()

    def test_returns_list(self, client):
        mock_row = MagicMock()
        mock_row.id = 1
        mock_row.title = "Blade Runner 2049"

        mock_db = make_mock_db(fetchall_value=[mock_row])
        app.dependency_overrides[get_db] = lambda: mock_db

        response = client.get("/movies")
        data = response.json()
        
        assert isinstance(data, list)
        assert data[0]["id"] == 1
        assert data[0]["title"] == "Blade Runner 2049"

        app.dependency_overrides.clear()


# ─── Test GET /recommend/{movie_id} ──────────────────────────────────────────

class TestGetRecommendations:

    def test_valid_movie_returns_200(self, client):
        # fetchone ครั้งแรก = movie, fetchall = matches
        mock_movie = MagicMock()
        mock_movie.id = 1
        mock_movie.title = "Blade Runner 2049"

        mock_db = AsyncMock()
        movie_result = MagicMock()
        movie_result.fetchone.return_value = mock_movie

        matches_result = MagicMock()
        matches_result.fetchall.return_value = []

        # execute ถูกเรียก 2 ครั้ง: ครั้งแรก=movie, ครั้งที่สอง=matches
        mock_db.execute.side_effect = [movie_result, matches_result]
        app.dependency_overrides[get_db] = lambda: mock_db

        response = client.get("/recommend/1")
        assert response.status_code == 200

        app.dependency_overrides.clear()

    def test_valid_movie_returns_correct_schema(self, client):
        mock_movie = MagicMock()
        mock_movie.id = 1
        mock_movie.title = "Blade Runner 2049"

        mock_db = AsyncMock()
        movie_result = MagicMock()
        movie_result.fetchone.return_value = mock_movie

        matches_result = MagicMock()
        matches_result.fetchall.return_value = []

        mock_db.execute.side_effect = [movie_result, matches_result]
        app.dependency_overrides[get_db] = lambda: mock_db

        response = client.get("/recommend/1")
        data = response.json()

        # ตรวจ schema ตาม RecommendResponse
        assert "movie_id" in data
        assert "movie_title" in data
        assert "matches" in data
        assert data["movie_title"] == "Blade Runner 2049"

        app.dependency_overrides.clear()

    def test_nonexistent_movie_returns_404(self, client):
        mock_db = make_mock_db(fetchone_value=None)  # movie ไม่มี
        app.dependency_overrides[get_db] = lambda: mock_db

        response = client.get("/recommend/99999")
        assert response.status_code == 404

        app.dependency_overrides.clear()


# ─── Test POST /feedback ──────────────────────────────────────────────────────

class TestSubmitFeedback:

    def _make_feedback_db(self, movie_exists=True, song_exists=True, feedback_id=1):
        """Helper สร้าง mock db สำหรับ feedback endpoint"""
        mock_db = AsyncMock()

        # execute ครั้งที่ 1: check movie+song exists
        check_result = MagicMock()
        check_row = MagicMock()
        check_row.movie_exists = movie_exists
        check_row.song_exists = song_exists
        check_result.fetchone.return_value = check_row

        # execute ครั้งที่ 2: INSERT feedback
        insert_result = MagicMock()
        insert_result.scalar.return_value = feedback_id

        # execute ครั้งที่ 3: UPDATE n_interactions
        update_result = MagicMock()

        mock_db.execute.side_effect = [check_result, insert_result, update_result]
        return mock_db

    def test_valid_feedback_returns_200(self, client):
        mock_db = self._make_feedback_db()
        app.dependency_overrides[get_db] = lambda: mock_db

        response = client.post("/feedback", json={
            "movie_id": 1, "song_id": 1, "rating": 5.0
        })
        assert response.status_code == 200
        assert response.json()["success"] is True

        app.dependency_overrides.clear()

    def test_invalid_rating_too_high_returns_422(self, client):
        """Pydantic validate rating ≤ 5 อัตโนมัติ — ไม่ต้อง mock db"""
        response = client.post("/feedback", json={
            "movie_id": 1, "song_id": 1, "rating": 10.0  # เกิน range
        })
        assert response.status_code == 422

    def test_invalid_rating_too_low_returns_422(self, client):
        response = client.post("/feedback", json={
            "movie_id": 1, "song_id": 1, "rating": 0.0  # ต่ำกว่า 1
        })
        assert response.status_code == 422

    def test_missing_fields_returns_422(self, client):
        response = client.post("/feedback", json={"rating": 3.0})
        assert response.status_code == 422

    def test_movie_not_found_returns_404(self, client):
        mock_db = self._make_feedback_db(movie_exists=False)
        app.dependency_overrides[get_db] = lambda: mock_db

        response = client.post("/feedback", json={
            "movie_id": 99999, "song_id": 1, "rating": 3.0
        })
        assert response.status_code == 404

        app.dependency_overrides.clear()

    def test_song_not_found_returns_404(self, client):
        mock_db = self._make_feedback_db(song_exists=False)
        app.dependency_overrides[get_db] = lambda: mock_db

        response = client.post("/feedback", json={
            "movie_id": 1, "song_id": 99999, "rating": 3.0
        })
        assert response.status_code == 404

        app.dependency_overrides.clear()